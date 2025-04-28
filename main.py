import os
import json
import time
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from pose_model import PoseDetector
from angle_calculation import get_angles

os.environ["GLOG_minloglevel"] = "0"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
TEXT_WIDTH = 300  # ширина текстового поля в пикселях
PADDING = 40  # отступы

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Patient App")

        total_width = CAMERA_WIDTH + TEXT_WIDTH + PADDING
        total_height = max(CAMERA_HEIGHT, 600) + PADDING

        self.geometry(f"{total_width}x{total_height}")
        self.minsize(total_width, total_height)

        self.patient_data = {}
        self.frames = {}

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for F in (WelcomeScene, AnamnesisScene):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.container = container
        self.show_frame(WelcomeScene)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def show_pose_scene(self, dirname):
        frame = PoseScene(self.container, self, dirname)
        self.frames[PoseScene] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(PoseScene)

class WelcomeScene(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.columnconfigure(0, weight=1)

        ttk.Label(self, text="Добро пожаловать", font=("Arial", 24)).grid(row=0, column=0, pady=60)
        ttk.Button(self, text="Новая запись", command=lambda: controller.show_frame(AnamnesisScene)).grid(row=1, column=0, pady=20)

class AnamnesisScene(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        for i in range(2):
            self.columnconfigure(i, weight=1)

        ttk.Label(self, text="Анамнез пациента", font=("Arial", 20)).grid(row=0, column=0, columnspan=2, pady=20)

        self.entries = {}
        fields = [
            ("Имя", "name"),
            ("Возраст", "age"),
            ("Рост", "height"),
            ("Вес", "weight"),
            ("Тип ампутации", "amputation_type"),
            ("Доп. информация", "additional_info"),
        ]

        for idx, (label, key) in enumerate(fields, start=1):
            ttk.Label(self, text=label).grid(row=idx, column=0, sticky="e", padx=10, pady=5)
            entry = ttk.Entry(self)
            entry.grid(row=idx, column=1, sticky="w", padx=10, pady=5)
            self.entries[key] = entry

        ttk.Label(self, text="Пол").grid(row=len(fields) + 1, column=0, sticky="e", padx=10, pady=5)
        self.gender = tk.StringVar(value="муж")
        frame_gender = ttk.Frame(self)
        frame_gender.grid(row=len(fields) + 1, column=1, sticky="w", padx=10, pady=5)
        ttk.Radiobutton(frame_gender, text="Муж", variable=self.gender, value="муж").pack(side="left")
        ttk.Radiobutton(frame_gender, text="Жен", variable=self.gender, value="жен").pack(side="left")

        ttk.Button(self, text="Продолжить", command=self.save_data).grid(row=len(fields) + 2, column=0, columnspan=2, pady=20)

    def save_data(self):
        data = {}
        for key, entry in self.entries.items():
            value = entry.get()
            if key in ["age", "height", "weight"]:
                try:
                    value = float(value)
                except ValueError:
                    messagebox.showerror("Ошибка", f"{key} должно быть числом")
                    return
            data[key] = value

        data["gender"] = self.gender.get()

        dirname = f"data/{data['name'].replace(' ', '_')}"
        os.makedirs(dirname, exist_ok=True)

        with open(f"{dirname}/parameters.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.controller.patient_data = data
        self.controller.show_pose_scene(dirname)

class PoseScene(tk.Frame):
    def __init__(self, parent, controller, dirname):
        super().__init__(parent)
        self.controller = controller
        self.dirname = dirname
        self.pose_detector = PoseDetector()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

        self.last_save_time = 0
        self.save_interval = 0.1  # секунд

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        ttk.Label(self, text="Оценка позы", font=("Arial", 20)).grid(row=0, column=0, columnspan=2, pady=(20, 10))

        self.video_label = ttk.Label(self)
        self.video_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.angles_text = tk.Text(self, font=("Courier", 12), width=30, wrap="none")
        self.angles_text.grid(row=1, column=1, padx=10, pady=10, sticky="ns")

        self.angles_file = open(f"{dirname}/angles_log.txt", "w", encoding="utf-8")
        self.update_frame()

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.video_label.config(text="Камера недоступна.")
            return

        results = self.pose_detector.process_frame(frame)
        frame = self.pose_detector.draw_landmarks(frame, results)

        now = time.time()

        if results.pose_landmarks:
            angles = get_angles(results.pose_landmarks.landmark, self.pose_detector.pose)

            if now - self.last_save_time >= self.save_interval:
                self.angles_file.write(f"{now:.2f}: {','.join(f'{k}:{int(v)}' for k, v in angles.items())}\n")
                self.last_save_time = now

            self.angles_text.delete("1.0", tk.END)
            self.angles_text.insert("1.0", '\n'.join(f"{k}: {int(v)}°" for k, v in angles.items()))
        else:
            self.angles_text.delete("1.0", tk.END)
            self.angles_text.insert("1.0", "Поза не обнаружена.")

        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(img_pil)
        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)

        self.after(10, self.update_frame)

    def destroy(self):
        self.cap.release()
        self.angles_file.close()
        super().destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
