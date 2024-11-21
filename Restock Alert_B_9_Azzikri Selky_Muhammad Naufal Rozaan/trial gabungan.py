import serial
import time
import random
import pandas as pd
from datetime import datetime
import re  # Untuk validasi dengan regex

# Fungsi untuk membaca data dari CSV
def read_csv_data(csv_path):
    try:
        return pd.read_csv(csv_path, delimiter=",")
    except (FileNotFoundError, pd.errors.EmptyDataError) as e:
        return None

# Fungsi untuk memproses data produk dari CSV
def process_product_data(df):
    if df is not None:
        product_data = {
            row.iloc[10]: 1 if int(row.iloc[12]) == 0 else 0
            for _, row in df.iterrows()
            if pd.notna(row.iloc[10]) and pd.notna(row.iloc[12])
        }
        return product_data
    return {'A': 0, 'B': 0, 'C': 0, 'D': 0}

# Fungsi untuk menampilkan data ke terminal dan mengirimkan ke Arduino
def display_data(frequencies, timers, temperature, almost_expired, expired, product_data, ser):
    current_time = time.time()
    last_display_update = getattr(display_data, 'last_display_update', 0)

    if current_time - last_display_update >= 0.99:
        output = []
        for product, frequency in frequencies.items():
            output.append(f"{temperature},{product_data.get(product, 0)},{almost_expired[product]},{expired[product]}")

        # Gabungkan semua data menyamping
        output_string = ",".join(output)
        
        # Tampilkan ke terminal
        print(output_string)
        
        # Kirimkan data ke Arduino melalui serial
        if ser.is_open:
            ser.write((output_string + "\n").encode('utf-8'))
        
        display_data.last_display_update = current_time

# Fungsi utama untuk membaca data dan memperbarui CSV
def main(serial_port, baud_rate, csv_path):
    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=1)
        time.sleep(2)  # Tunggu inisialisasi serial

        # Inisialisasi variabel
        frequencies = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        timers = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        almost_expired = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        expired = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        last_update_time = {'A': time.time(), 'B': time.time(), 'C': time.time(), 'D': time.time()}
        speedup_factors = {'A': 1.25, 'B': 1.75, 'C': 1.5, 'D': 2.5}
        temperature = 0
        last_temp_update = time.time()

        while True:
            # Update suhu secara berkala
            current_time = time.time()
            if current_time - last_temp_update >= 20:
                temperature = random.randint(0, 1)
                last_temp_update = current_time

            # Membaca data dari Arduino
            if ser.in_waiting > 0:
                raw_data = ser.readline()  # Membaca data mentah dari serial
               
                try:
                    # Decode data menjadi string ASCII
                    decoded_data = raw_data.decode("ascii").strip()
                    
                    # Validasi dengan regex: hanya memproses data 8 digit
                    if re.fullmatch(r'\d{8}', decoded_data):
                        # Proses data menjadi frekuensi produk
                        new_frequencies = {
                            'A': int(decoded_data[0:2]),
                            'B': int(decoded_data[2:4]),
                            'C': int(decoded_data[4:6]),
                            'D': int(decoded_data[6:8])
                        }
                        for product, new_frequency in new_frequencies.items():
                            if new_frequency > frequencies[product]:
                                timers[product] = 0
                                almost_expired[product] = 0
                                expired[product] = 0
                            frequencies[product] = new_frequency
                            last_update_time[product] = current_time
                    else:
                        print("Data tidak valid.")
                except UnicodeDecodeError as e:
                    print("Terjadi kesalahan decoding data.")

            # Update timer untuk setiap produk
            for product in timers.keys():
                elapsed_time = current_time - last_update_time[product]
                timers[product] += elapsed_time * speedup_factors[product] if temperature == 1 else elapsed_time
                last_update_time[product] = current_time

                if timers[product] >= 240:
                    expired[product] = 1
                    almost_expired[product] = 1
                elif timers[product] >= 120:
                    almost_expired[product] = 1
                    expired[product] = 0

            # Membaca CSV dan memperbarui data
            df = read_csv_data(csv_path)
            product_data = process_product_data(df)
            display_data(frequencies, timers, temperature, almost_expired, expired, product_data, ser)

            # Update CSV jika ada perubahan frekuensi
            if df is not None:
                for product, frequency in frequencies.items():
                    # Cari baris berdasarkan product_ID
                    product_row = df[df['product_ID'] == product]
                    if not product_row.empty:
                        current_frequency = product_row.iloc[0]['product_restockFrequency']
                        current_stock = product_row.iloc[0]['product_stock']
                        
                        # Jika frekuensi berubah dan bertambah 1, reset stock ke 15 hanya jika stock lebih besar dari 0
                        if frequency > current_frequency and current_stock > 0:
                            df.loc[product_row.index, 'product_restockFrequency'] = frequency
                            df.loc[product_row.index, 'product_stock'] = 15  # Reset stock ke 15
                            df.loc[product_row.index, 'product_lastRestock'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                
                # Simpan perubahan ke file CSV
                df.to_csv(csv_path, index=False)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Program dihentikan secara manual.")
    except Exception as e:
        print(f"Terjadi error: {e}")
    finally:
        if 'ser' in locals():
            ser.close()
        print("Koneksi serial ditutup.")

# Menjalankan program
if __name__ == "__main__":
    csv_path = r"D:\VSCode\okedeh.csv"
    main(serial_port='COM15', baud_rate=9600, csv_path=csv_path)
