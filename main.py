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

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Patient App")
        self.geometry("500x400")
        self.patient_data = {}
        self.frames = {}

        for F in (WelcomeScene, AnamnesisScene):
            frame = F(self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(WelcomeScene)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def show_pose_scene(self, dirname):
        frame = PoseScene(self, dirname)
        self.frames[PoseScene] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(PoseScene)

class WelcomeScene(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="Добро пожаловать", font=("Arial", 20)).pack(pady=60)
        ttk.Button(self, text="Новая запись", command=lambda: parent.show_frame(AnamnesisScene)).pack()

class AnamnesisScene(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        ttk.Label(self, text="Анамнез пациента", font=("Arial", 16)).pack(pady=10)

        self.entries = {}
        fields = [
            ("Имя", "name"),
            ("Возраст", "age"),
            ("Рост", "height"),
            ("Вес", "weight"),
            ("Тип ампутации", "amputation_type"),
            ("Доп. информация", "additional_info"),
        ]

        for label, key in fields:
            ttk.Label(self, text=label).pack()
            entry = ttk.Entry(self)
            entry.pack()
            self.entries[key] = entry

        ttk.Label(self, text="Пол").pack()
        self.gender = tk.StringVar(value="муж")
        ttk.Radiobutton(self, text="Муж", variable=self.gender, value="муж").pack()
        ttk.Radiobutton(self, text="Жен", variable=self.gender, value="жен").pack()

        ttk.Button(self, text="Продолжить", command=self.save_data).pack(pady=10)

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

        self.parent.patient_data = data
        self.parent.show_pose_scene(dirname)

class PoseScene(tk.Frame):
    def __init__(self, parent, dirname):
        super().__init__(parent)
        self.dirname = dirname
        self.pose_detector = PoseDetector()
        self.cap = cv2.VideoCapture(0)
        self.last_save_time = 0
        self.save_interval = 0.1  # сек

        ttk.Label(self, text="Оценка позы", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=(10, 0))

        self.video_label = ttk.Label(self)
        self.video_label.grid(row=2, column=0, padx=10, pady=10)

        self.angles_text = tk.Text(self, height=30, width=30, font=("Courier", 10))
        self.angles_text.grid(row=2, column=1, padx=10, pady=10, sticky="n")

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
        self.video_label.imgtk = ImageTk.PhotoImage(img_pil)
        self.video_label.config(image=self.video_label.imgtk)

        self.after(10, self.update_frame)

    def destroy(self):
        self.cap.release()
        self.angles_file.close()
        super().destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
