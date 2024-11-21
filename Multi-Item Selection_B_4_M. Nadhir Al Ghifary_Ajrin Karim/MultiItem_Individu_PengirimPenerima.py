import threading
import time
import pandas as pd
import json
import paho.mqtt.client as mqtt
from datetime import datetime

# Konfigurasi MQTT
broker_address = "192.168.124.170"
topic_kirim = "esp32/kirim"
topic_terima = "esp32/terima"
port = 1890
file_path = "D:\\Data Rapi\\Waktu Nadhir di UGM\\Semester 5\\9. PJK\\Responsi\\okedeh.csv"

def mengirim(file_path):
    # Baca file CSV menggunakan Pandas
    df = pd.read_csv(file_path)
    
    # Bersihkan nama kolom (hilangkan spasi tambahan)
    df.columns = df.columns.str.strip()
    
    # Filter data berdasarkan login_status
    filtered_row = df[df['login_status'] == 1.0]

    # Ambil user_age dari baris dengan login_status = 1
    if not filtered_row.empty:
        user_age = filtered_row['user_age'].iloc[0].item()  # Convert int64 to int
    else:
        user_age = None

    # Filter baris yang memiliki nilai valid untuk product_ID dan product_stock
    valid_products = df[df['product_ID'].notna() & df['product_stock'].notna()]

    # Ambil product_ID dan product_stock
    product_IDs = valid_products['product_ID'].astype(str).tolist()
    product_stocks = valid_products['product_stock'].tolist()

    # Gabungkan data menjadi JSON
    data = {
        "product_ID": product_IDs,
        "product_stock": product_stocks,
        "user_age": user_age
    }
    message = json.dumps(data)  # Convert to JSON serializable format
    
    # Inisialisasi MQTT
    client = mqtt.Client()
    client.connect(broker_address, port, 60)
    client.publish(topic_kirim, message)
    print(f"Data terkirim: {message}")
    client.disconnect()

def menerima(file_path):
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
        
        # Cari baris pertama yang kosong di kolom 'cart'
        empty_row_index = df[df["cart"] == ""].index.min()
        
        # Jika tidak ada baris kosong, tambahkan baris baru
        if pd.isna(empty_row_index):
            empty_row_index = len(df)
            df.loc[empty_row_index] = {"cart": "", "timestamp": ""}
        
        # Isi data ke kolom 'cart' dan tambahkan timestamp
        df.at[empty_row_index, "cart"] = data_string
        df.at[empty_row_index, "timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Simpan kembali ke file CSV
        df.to_csv(file_path, index=False)
        print(f"Data berhasil disimpan ke file CSV: {file_path}")

    # Callback saat subscribe berhasil
    def on_subscribe(mqttc, obj, mid, reason_code):
        print(f"Berhasil subscribe dengan kode: {reason_code}")

    # Inisialisasi MQTT
    mqttc = mqtt.Client()
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe

    # Koneksi ke broker MQTT
    mqttc.connect(broker_address, port, 60)
    mqttc.subscribe(topic_terima)

    # Mulai loop MQTT
    mqttc.loop_forever()

# Fungsi utama
def main():
    data_received = threading.Event()  # Event untuk sinkronisasi penerimaan data

    # Step 1: Jalankan pengiriman data
    print("Memulai pengiriman data...")
    mengirim(file_path)  # Memanggil fungsi pengiriman
    print("Pengiriman data selesai. Menunggu data masuk...")

    # Step 2: Jalankan penerimaan data
    def start_receiver():
        # Modifikasi fungsi `menerima` agar dapat menghentikan loop setelah data diterima
        def modified_menerima(file_path):
            def on_message(mqttc, obj, msg):
                try:
                    # Baca file CSV
                    try:
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
                    
                    # Cari baris pertama yang kosong di kolom 'cart'
                    empty_row_index = df[df["cart"] == ""].index.min()
                    
                    # Jika tidak ada baris kosong, tambahkan baris baru
                    if pd.isna(empty_row_index):
                        empty_row_index = len(df)
                        df.loc[empty_row_index] = {"cart": "", "timestamp": ""}
                    
                    # Isi data ke kolom 'cart' dan tambahkan timestamp
                    df.at[empty_row_index, "cart"] = data_string
                    df.at[empty_row_index, "timestamp"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Simpan kembali ke file CSV
                    df.to_csv(file_path, index=False)
                    print(f"Data berhasil disimpan ke file CSV: {file_path}")

                    # Beri sinyal bahwa data telah diterima
                    data_received.set()
                except Exception as e:
                    print(f"Error dalam on_message: {e}")

            # Gunakan fungsi `menerima` asli dan tambahkan callback ini
            def on_connect(mqttc, obj, flags, reason_code):
                print(f"Terhubung ke broker MQTT, kode: {reason_code}")

            mqttc = mqtt.Client()
            mqttc.on_message = on_message
            mqttc.on_connect = on_connect
            mqttc.connect("192.168.124.170", 1890, 60)
            mqttc.subscribe("esp32/terima")
            mqttc.loop_forever()  # Loop hingga dihentikan oleh event
            
        modified_menerima(file_path)

    receiver_thread = threading.Thread(target=start_receiver)
    receiver_thread.daemon = True  # Daemon thread agar otomatis berhenti jika program utama berhenti
    receiver_thread.start()

    # Step 3: Tunggu sampai data diterima
    print("Menunggu data diterima...")
    data_received.wait()  # Tunggu hingga event data_received diset
    print("Data diterima. Program selesai.")

# Jalankan program utama
if __name__ == "__main__":
    main()
