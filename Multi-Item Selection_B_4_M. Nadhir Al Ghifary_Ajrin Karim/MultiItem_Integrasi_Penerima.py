import pandas as pd
import paho.mqtt.client as mqtt
from datetime import datetime

async def menerima(file_path):
    # Callback saat terhubung ke broker
    def on_connect(mqttc, obj, flags, reason_code):
        print(f"Terhubung ke broker MQTT, kode: {reason_code}")

    # Callback saat pesan diterima
    def on_message(mqttc, obj, msg):
        try:
            # Baca file CSV (jika file tidak ada, buat DataFrame baru)
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            df = pd.DataFrame(columns=["cart", "timestamp"])
        
        # Tambahkan kolom jika tidak ada
        if "cart" not in df.columns:
            df["cart"] = ""
        if "timestamp" not in df.columns:
            df["timestamp"] = ""
        
        # Decode payload dari MQTT
        data_string = msg.payload.decode("utf-8").strip()
        print(f"Data diterima: {data_string}")
        return data_string
