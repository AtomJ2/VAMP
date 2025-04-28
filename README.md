# VAMP — Application for Analyzing Movements of Patients with Amputation

---

## 📖 Project Description

**VAMP** is a desktop Python application designed for use in biomechanics and medical engineering.  
The goal of the project is to facilitate the collection and analysis of motor activity data in patients with limb amputations. The program combines a simple form for filling out patient history with body movement capture using a camera and computer vision technology.

---

## 🚀 Main Features

- Filling out and saving the patient's history in JSON format.
- Real-time video stream with pose recognition via the camera.
- Automatic calculation of joint angles: knees, hips, and ankles.
- Real-time display of the angles on screen.
- Saving a history of angles to a text log file with timestamps.
- User-friendly graphical interface built with `tkinter`.

---

## 🛠️ Technologies Used

- **Python 3.10+**
- **OpenCV** — video stream processing.
- **MediaPipe** — human pose recognition.
- **NumPy** — calculating angles based on keypoint coordinates.
- **Tkinter** — graphical user interface (GUI).
- **Pillow** — image processing in the interface, if necessary.

---

## 🏗️ Project Structure

```
VAMP/
│
├── main.py                 # Main application file
├── pose_model.py           # Handling Mediapipe pose capture
├── angle_calculation.py    # Joint angle calculations
├── requirements.txt        # Project dependencies
├── README.md               # Project instructions
└── data/                   # Automatically generated folder with patient data
    └── <PatientName>/
        ├── parameters.json  # Saved patient history
        └── angles_log.txt   # Real-time angle log
```

---

## 📋 Environment Requirements

- **Python**: 3.10 or higher  
- **Operating System**: Windows 10/11 (tested), may also work on Linux/Mac (not tested).
- **Camera**: Built-in or external USB camera.
- **Processor**: SSE4.1/SSE4.2 instruction support is recommended.

---

## 📦 Project Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/AtomJ2/VAMP.git
   cd VAMP
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Make sure your Python version is >= 3.10:

   ```bash
   python --version
   ```

---

## ⚙️ How to Run

Run the `main.py` file:

```bash
python main.py
```

After launch:
- The program will display a welcome screen.
- You will then proceed to fill in patient data.
- After completing the form, a video stream with pose overlay and angle calculation will start.

---

## 🧠 Angle Calculation Logic

1. The coordinates of three points for each joint (e.g., thigh — knee — shin) are captured;
2. Vectors between the points are calculated;
3. The angle between the two vectors is found using the dot product;
4. The angles are converted into degrees and displayed in real-time.

---

## 📂 Example of Saved Data Structure

File `parameters.json`:
```json
{
  "name": "Petr Zakharov",
  "age": 34,
  "height": 178,
  "weight": 82,
  "amputation_type": "below the knee",
  "additional_info": "first prosthesis",
  "sex": "male"
}
```

File `angles_log.txt`:
```
1714315612.52: knee_l:170,knee_r:172,ankle_l:90,ankle_r:92,hip_l:185,hip_r:183
1714315612.62: knee_l:169,knee_r:171,ankle_l:91,ankle_r:91,hip_l:186,hip_r:182
...
```

---