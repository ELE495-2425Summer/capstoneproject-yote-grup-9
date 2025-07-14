# 🚗 Speech-Controlled Autonomous Mini Vehicle

ELE 495 Senior Design Project (2024-2025)

## 📌 Project Description
This project implements a **speech-controlled autonomous mini vehicle** that interprets Turkish voice commands and executes them using a mecanum wheel system. The vehicle uses:
- **Google STT API** for speech recognition
- **Gemini 2.5 Flash (LLM)** for natural language understanding
- **Google TTS API** for voice feedback
- **Raspberry Pi 5** as the embedded controller

> The system supports real-time sensor feedback, autonomous navigation with obstacle handling, and a TCP-based user interface for monitoring vehicle status.

---

## 🧠 System Overview
![System Diagram](System_Overview.drawio.png)

1. **Speech Input** via microphone
2. **Speech-to-Text** (Google STT)
3. **Natural Language Parsing** (Gemini LLM)
4. **Command Execution** with sensor-aware navigation
5. **Text-to-Speech Feedback** (Google TTS)
6. **Real-time UI Feedback** over TCP

---

## 🔧 Technologies Used
- Python 3
- Raspberry Pi 5 (8GB)
- Google Speech-to-Text API
- Google Gemini 2.5 Flash (via `google.generativeai`)
- Google Cloud Text-to-Speech API
- Sensor communication via UART
- Real-time web interface (socket-based)

---

## 🛠️ Setup & Installation
### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/speech-car.git
cd speech-car
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Add Your API Keys
Update the following in `son_denemeler.py`:
```python
GOOGLE_API_KEY = "<YOUR_GEMINI_API_KEY>"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "<YOUR_JSON_CREDENTIAL_PATH>"
```

### 4. Prepare Hardware
- Raspberry Pi 5
- 4-channel motor driver
- Ultrasonic sensors (front, back, left, right)
- Microphone & speaker (connected via USB or Pi’s audio jack)

### 5. Run the System
```bash
python3 son_denemeler.py
```

---

## 🎙️ Example Command
**Input:** "Engel çıkana kadar düz git, sonra sağa dön."

**LLM Output (JSON):**
```json
{
  "command": "forward",
  "condition": "until_obstacle",
  "speed": 20,
  "duration": 1,
  "next_command": {
    "command": "right",
    "speed": 20,
    "duration": 1
  }
}
```

**Voice Feedback:** "İleri gidip ardından sağa döneceğim."

---

## 🖥️ User Interface Features
Real-time TCP socket server sends JSON data to connected clients:
- `vehicle_state`: current movement and speed
- `stt_output`: last transcribed sentence
- `current_command`: parsed command
- `command_history`: last 10 executed commands

You can build a browser-based dashboard or mobile app to consume this data.

---

## 📂 Project Structure
```bash
.
├── YOTE_AUTO_CONTROL.py          # Main application
├── CommandSounds/            # Pre-recorded MP3 feedback
├── requirements.txt          # Python dependencies
└── README.md
```

---

## 👥 Team
- Özgür ARKAN – 211201036
- Tarık ELTÜRK – 211201069
- Elif COŞAR – 191201063
- Yusuf Ferhat YILMAN – 211501010

Supervisors: Dr. Zeki U. Kocabıyıkoğlu & Instructor Murat Sever



## 🎯 Future Improvements
- Speaker verification for command authorization
- Android/iOS UI via Expo or Flutter
- Offline LLM and TTS deployment using local models
