# --- Gerekli Kütüphaneler ---
import os
import sys
import re
import json
import time
import base64
import socket
import queue
import logging
import serial
import threading
import datetime
import requests
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from playsound import playsound
from retry import retry
import RPi.GPIO as GPIO
from dotenv import load_dotenv
import google.generativeai as genai
from google.cloud import texttospeech

# --- Ortam Değişkenlerini Yükle (.env üzerinden) ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# --- Log Ayarları ---
logging.basicConfig(
    filename="vehicle_log.txt",
    level=logging.DEBUG,
    format="%(asctime)s: %(levelname)s: %(message)s"
)

# --- Sistem Değişkenleri ---
FS = 16000
WAV_FILE = "gecici_giris.wav"
command_history = []
current_stt_output = ""
current_command = {}
vehicle_state = {
    "status": "stopped",
    "speed": 0,
    "sensors": {
        "dist_on": 400.0, "dist_sag": 400.0, "dist_arka": 400.0, "dist_sol": 400.0
    }
}

# --- GPIO Motor Ayarları ---
A_IA, A_IB = 23, 22
B_IA, B_IB = 25, 24
C_IA, C_IB = 18, 17
D_IA, D_IB = 12, 20
MOTOR_PINS = [A_IA, A_IB, B_IA, B_IB, C_IA, C_IB, D_IA, D_IB]
PWM_FREQ = 1000

GPIO.setmode(GPIO.BCM)
for pin in MOTOR_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

motor_a_plus = GPIO.PWM(A_IA, PWM_FREQ)
motor_a_minus = GPIO.PWM(A_IB, PWM_FREQ)
motor_b_plus = GPIO.PWM(B_IA, PWM_FREQ)
motor_b_minus = GPIO.PWM(B_IB, PWM_FREQ)
motor_c_plus = GPIO.PWM(C_IA, PWM_FREQ)
motor_c_minus = GPIO.PWM(C_IB, PWM_FREQ)
motor_d_plus = GPIO.PWM(D_IA, PWM_FREQ)
motor_d_minus = GPIO.PWM(D_IB, PWM_FREQ)

pwms = [motor_a_plus, motor_a_minus, motor_b_plus, motor_b_minus,
        motor_c_plus, motor_c_minus, motor_d_plus, motor_d_minus]

for pwm in pwms:
    try:
        pwm.start(0)
    except Exception as e:
        logging.error(f"PWM başlatma hatası: {e}")

# --- PWM Yardımcı Fonksiyonlar ---
def stop():
    for pwm in pwms:
        try:
            pwm.ChangeDutyCycle(0)
        except Exception as e:
            logging.error(f"PWM durdurma hatası: {e}")
    vehicle_state.update({"status": "stopped", "speed": 0})
    logging.info("Tüm motorlar durduruldu.")

def motor_a_stop(): motor_a_plus.ChangeDutyCycle(0); motor_a_minus.ChangeDutyCycle(0)
def motor_b_stop(): motor_b_plus.ChangeDutyCycle(0); motor_b_minus.ChangeDutyCycle(0)
def motor_c_stop(): motor_c_plus.ChangeDutyCycle(0); motor_c_minus.ChangeDutyCycle(0)
def motor_d_stop(): motor_d_plus.ChangeDutyCycle(0); motor_d_minus.ChangeDutyCycle(0)

def motor_a_forward(s): motor_a_plus.ChangeDutyCycle(s); motor_a_minus.ChangeDutyCycle(0)
def motor_a_backward(s): motor_a_plus.ChangeDutyCycle(0); motor_a_minus.ChangeDutyCycle(s)
def motor_b_forward(s): motor_b_plus.ChangeDutyCycle(s); motor_b_minus.ChangeDutyCycle(0)
def motor_b_backward(s): motor_b_plus.ChangeDutyCycle(0); motor_b_minus.ChangeDutyCycle(s)
def motor_c_forward(s): motor_c_plus.ChangeDutyCycle(0); motor_c_minus.ChangeDutyCycle(s)
def motor_c_backward(s): motor_c_plus.ChangeDutyCycle(s); motor_c_minus.ChangeDutyCycle(0)
def motor_d_forward(s): motor_d_plus.ChangeDutyCycle(0); motor_d_minus.ChangeDutyCycle(s)
def motor_d_backward(s): motor_d_plus.ChangeDutyCycle(s); motor_d_minus.ChangeDutyCycle(0)

# --- Ses Kaydı ---
def record_audio(filename, duration, fs):
    print("🎙️ Konuşun...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    write(filename, fs, recording)
    print("✅ Kayıt tamamlandı")

# --- Google Speech-to-Text ---
def transcribe_audio_google(file_path, sample_rate):
    with open(file_path, "rb") as audio_file:
        audio_content = base64.b64encode(audio_file.read()).decode("utf-8")
    headers = {"Content-Type": "application/json"}
    url = f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}"
    data = {
        "config": {
            "encoding": "LINEAR16",
            "sampleRateHertz": sample_rate,
            "languageCode": "tr-TR"
        },
        "audio": {"content": audio_content}
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        try:
            return response.json()["results"][0]["alternatives"][0]["transcript"]
        except (KeyError, IndexError):
            return None
    else:
        logging.error(f"STT Hatası: {response.status_code}, {response.text}")
        return None

# --- Google TTS (Geri Bildirim) ---
def speak_text(text, output_file="output.mp3"):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="tr-TR", ssml_gender=texttospeech.SsmlVoiceGender.MALE)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
    playsound(output_file)

# --- Gemini LLM Komut Üretimi ---
@retry(tries=3, delay=1, backoff=2)
def generate_json_command(instruction):
    prompt = f'''
    You control a mecanum vehicle. Extract JSON with:
    "command", "speed", "duration", optional "condition" and "next_command".
    Input: "{instruction}"
    '''
    response = model.generate_content(prompt)
    raw = response.text.strip()
    return json.loads(raw)

# --- Ana Fonksiyon ---
if __name__ == "__main__":
    try:
        while True:
            record_audio(WAV_FILE, 5, FS)
            input_text = transcribe_audio_google(WAV_FILE, FS)
            if not input_text:
                speak_text("Komutu anlayamadım, tekrar dinliyorum.")
                continue
            print("Algılanan Komut:", input_text)
            speak_text(f"Komut alındı: {input_text}")
            command_data = generate_json_command(input_text)
            # Örnek: {"command": "forward", "speed": 30, "duration": 2}
            if command_data.get("command") == "forward":
                motor_a_forward(command_data["speed"])
                motor_b_forward(command_data["speed"])
                motor_c_forward(command_data["speed"])
                motor_d_forward(command_data["speed"])
                time.sleep(command_data["duration"])
                stop()
            elif command_data.get("command") == "stop":
                stop()
    except KeyboardInterrupt:
        stop()
        GPIO.cleanup()
        print("🛑 Sistem kapatıldı.")
