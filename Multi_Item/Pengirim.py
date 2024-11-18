import csv
import time
import paho.mqtt.client as mqtt
import json

# Konfigurasi MQTT
broker_address = "192.168.4.170"
topic = "esp32/csv"

def mengirim(file_path):
    # Inisialisasi client MQTT
    client = mqtt.Client()
    client.connect(broker_address, 1890, 60)

    product_IDs = []
    product_stocks = []
    user_ages = 0

    with open(file_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)  # Baca sebagai dictionary
        for row in reader:
            if row["product_ID"] and row["product_stock"]:
                product_IDs.append(int(row["product_ID"]))
                product_stocks.append(int(row["product_stock"]))
            if row.get("login_status") == "open":
                user_ages = int(row["user_age"])

    # Gabungkan data menjadi JSON
    data = {"product_ID": product_IDs, "product_stock": product_stocks, "user_age": user_ages}
    message = json.dumps(data)

    # Kirim pesan MQTT
    client.publish(topic, message)
    print(f"Data terkirim: {message}")

    client.disconnect()

# Panggil fungsi dengan path ke file CSV
mengirim("D:\Data Rapi\Waktu Nadhir di UGM\Semester 5\9. PJK\Responsi\Contoh CSV Lengkap.csv")
