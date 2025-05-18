import os
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from res.pose_model import PoseDetector
from res.angle_calculation import get_angles

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
TEXT_WIDTH = 300
PADDING = 40


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Patient App")
        total_width = CAMERA_WIDTH + TEXT_WIDTH + 500
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

    def show_pose_scene(self, dirname, video_path=None):
        frame = PoseScene(self.container, self, dirname, video_path=video_path)
        self.frames[PoseScene] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(PoseScene)


class WelcomeScene(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.columnconfigure(0, weight=1)

        ttk.Label(self, text="Добро пожаловать", font=("Arial", 24)).grid(row=0, column=0, pady=60)
        ttk.Button(self, text="Новая запись", command=lambda: controller.show_frame(AnamnesisScene)).grid(row=1, column=0, pady=10)
        ttk.Button(self, text="Открыть видео", command=self.open_video).grid(row=2, column=0, pady=10)

    def open_video(self):
        filepath = filedialog.askopenfilename(
            title="Выберите видеофайл",
            filetypes=(("Video files", "*.mp4 *.avi *.mov"), ("All files", "*.*"))
        )
        if filepath:
            dummy_data = {"name": "video_input"}
            dirname = "data/video_input"
            os.makedirs(dirname, exist_ok=True)
            with open(f"{dirname}/parameters.json", "w", encoding="utf-8") as f:
                json.dump(dummy_data, f, ensure_ascii=False, indent=2)

            self.controller.patient_data = dummy_data
            self.controller.show_pose_scene(dirname, video_path=filepath)


class AnamnesisScene(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        for i in range(2):
            self.columnconfigure(i, weight=1)

        ttk.Label(self, text="Анамнез пациента", font=("Arial", 20)).grid(row=0, column=0, columnspan=2, pady=20)
        self.entries = {}
        fields = [("Имя", "name"), ("Возраст", "age"), ("Рост", "height"),
                  ("Вес", "weight"), ("Тип ампутации", "amputation_type"), ("Доп. информация", "additional_info")]

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


from fpdf import FPDF

class PDF(FPDF):
    def __init__(self, font_path: str):
        super().__init__()
        self.add_font("DejaVu", "", font_path, uni=True)
        self.set_font("DejaVu", size=12)

    def header(self):
        self.set_font("DejaVu", size=14)
        self.cell(200, 10, txt="Отчет", ln=True, align='C')

class PoseScene(tk.Frame):
    def __init__(self, parent, controller, dirname, video_path=None):
        super().__init__(parent)
        self.controller = controller
        self.dirname = dirname
        self.pose_detector = PoseDetector()
        self.cap = cv2.VideoCapture(video_path if video_path else 0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

        self.last_save_time = 0
        self.save_interval = 0.1
        self.recording = False
        self.angle_log = []
        self.start_time = None

        self.grid_rowconfigure(1, weight=1)
        for i in range(3):
            self.grid_columnconfigure(i, weight=1)

        ttk.Label(self, text="Оценка позы", font=("Arial", 20)).grid(row=0, column=0, columnspan=3, pady=(20, 10))

        self.video_label = ttk.Label(self)
        self.video_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.angles_text = tk.Text(self, font=("Courier", 12), width=30, wrap="none")
        self.angles_text.grid(row=1, column=1, padx=10, pady=10, sticky="ns")

        self.angle_history = {name: [] for name in ["RHip", "RKnee", "RAnkle", "LHip", "LKnee", "LAnkle"]}

        self.figure, self.axs = plt.subplots(3, 2, figsize=(5, 4), dpi=100)
        self.figure.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

        self.record_button = ttk.Button(self, text="Начать запись", command=self.toggle_recording)
        self.record_button.grid(row=2, column=0, columnspan=3, pady=20)

        self.update_frame()

    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.angle_log.clear()
            self.start_time = time.time()
            self.record_button.config(text="Остановить запись")
        else:
            self.recording = False
            self.record_button.config(text="Начать запись")
            self.generate_report()

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
            if angles:
                self.angles_text.delete("1.0", tk.END)
                self.angles_text.insert("1.0", '\n'.join(f"{k}: {int(v)}°" for k, v in angles.items()))

                for key in self.angle_history:
                    val = angles.get(key)
                    if val is not None:
                        self.angle_history[key].append((now, val))

                if self.recording and now - self.last_save_time >= self.save_interval:
                    self.angle_log.append((now - self.start_time, angles.copy()))
                    self.last_save_time = now

                self.update_plots()
            else:
                self.angles_text.delete("1.0", tk.END)
                self.angles_text.insert("1.0", "Поза не обнаружена.")
        else:
            self.angles_text.delete("1.0", tk.END)
            self.angles_text.insert("1.0", "Поза не обнаружена.")

        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(img_pil)
        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)

        self.after(10, self.update_frame)

    def update_plots(self):
        angle_names = ["RHip", "RKnee", "RAnkle", "LHip", "LKnee", "LAnkle"]
        current_time = time.time()
        window_seconds = 10

        for i, name in enumerate(angle_names):
            row, col = divmod(i, 2)
            ax = self.axs[row][col]
            ax.clear()

            filtered = [(t, v) for t, v in self.angle_history[name] if current_time - t <= window_seconds]
            self.angle_history[name] = filtered

            if filtered:
                times, values = zip(*filtered)
                times = [t - times[0] for t in times]
                ax.plot(times, values, label=name)

            ax.set_title(name)
            ax.set_ylim(0, 180)
            ax.set_xlim(0, window_seconds)
            ax.legend(loc="upper right")
            ax.grid(True)

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def generate_report(self):

        font_path = "fonts/DejaVuSans.ttf"

        pdf = PDF(font_path)
        pdf.add_page()

        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=12)

        patient_file = os.path.join(self.dirname, "parameters.json")
        data = {}
        if os.path.exists(patient_file):
            with open(patient_file, "r", encoding="utf-8") as f:
                data = json.load(f)

        for key, val in data.items():
            pdf.cell(0, 10, txt=f"{key}: {val}", ln=True)

        pdf.ln(10)
        pdf.cell(0, 10, txt="Графики углов", ln=True)

        # Графики
        fig, axs = plt.subplots(3, 2, figsize=(8, 6))
        for i, (key, _) in enumerate(self.angle_history.items()):
            row, col = divmod(i, 2)
            times = [t for t, _ in self.angle_log]
            values = [angles[key] for _, angles in self.angle_log if key in angles]
            axs[row][col].plot(times[:len(values)], values)
            axs[row][col].set_title(key)
            axs[row][col].set_ylim(0, 180)

        plt.tight_layout()
        plot_path = os.path.join(self.dirname, "angles_plot.png")
        plt.savefig(plot_path)
        plt.close()

        pdf.image(plot_path, x=10, w=180)

        report_path = os.path.join(self.dirname, "report.pdf")
        pdf.output(report_path)
        messagebox.showinfo("Отчет", f"Отчет сохранен в {report_path}")

    def destroy(self):
        self.cap.release()
        super().destroy()



if __name__ == "__main__":
    app = App()
    app.mainloop()
