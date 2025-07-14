"""
ELE495 - Flask UI Web Server

Bu sunucu, Raspberry Pi'deki TCP sunucudan gelen JSON verileri alır
ve HTML arayüzü aracılığıyla kullanıcıya sunar.
"""

from flask import Flask, render_template
import socket
import json
import threading
import logging
import time

app = Flask(__name__)

# Log formatı
logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")

# Küresel UI verisi
ui_data = {
    "vehicle_state": {"status": "stopped", "speed": 0, "sensors": {}},
    "stt_output": "",
    "current_command": {},
    "command_history": []
}

# Raspberry Pi'den TCP veri alımı
class UIClient(threading.Thread):
    def __init__(self, host="10.5.64.94", port=54321):  # IP'yi kendi Pi adresinle değiştir
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True

    def run(self):
        global ui_data
        while self.running:
            try:
                self.socket.connect((self.host, self.port))
                logging.info("Connected to RPi TCP server")
                while self.running:
                    data = self.socket.recv(4096).decode('utf-8').strip()
                    if data:
                        try:
                            ui_data = json.loads(data)
                        except json.JSONDecodeError:
                            logging.error("Invalid JSON received")
                    time.sleep(0.1)
            except (ConnectionRefusedError, ConnectionResetError):
                logging.warning("Connection to RPi lost, retrying...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                time.sleep(1)
            except Exception as e:
                logging.error(f"UIClient error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
        self.socket.close()

# Ana sayfa
@app.route('/')
def index():
    return render_template('index.html')

# JSON verisi endpoint
@app.route('/data')
def get_data():
    return ui_data

# Uygulama başlatılıyor
if __name__ == "__main__":
    client = UIClient()
    client.start()
    app.run(host='0.0.0.0', port=8080, debug=False)
    client.stop()
