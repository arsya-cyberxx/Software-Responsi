import serial
import time
import random
import pandas as pd

# Fungsi untuk membaca data dari CSV
def read_csv_data(csv_path):
    """
    Membaca data dari file CSV dan mengembalikannya dalam bentuk DataFrame.
    """
    try:
        return pd.read_csv(csv_path, delimiter=",")
    except (FileNotFoundError, pd.errors.EmptyDataError) as e:
        print(f"Error: {e}")
        return None

# Fungsi untuk memproses data produk dari file CSV
def process_product_data(df):
    """
    Memproses data produk untuk mendapatkan product_id dan status_stock.
    """
    if df is not None:
        product_data = {
            row.iloc[10]: 1 if int(row.iloc[12]) == 0 else 0
            for _, row in df.iterrows()
            if pd.notna(row.iloc[10]) and pd.notna(row.iloc[12])
        }
        return product_data
    return {'A': 0, 'B': 0, 'C': 0, 'D': 0}

# Fungsi untuk menampilkan data ke terminal dan mengirimkan ke Arduino
def display_data(frequencies, timers, temperature, almost_expired, expired, data_received, product_data, ser):
    current_time = time.time()
    last_display_update = getattr(display_data, 'last_display_update', 0)

    if current_time - last_display_update >= 3:
        output = []
        for product, frequency in frequencies.items():
            output.append(f"{temperature},{product_data.get(product, 0)},{almost_expired[product]},{expired[product]}")
        
        # Gabungkan semua data menyamping
        output_string = ", ".join(output)
        
        # Tampilkan ke terminal
        print(output_string)
        
        # Kirimkan data ke Arduino melalui serial
        if ser.is_open:
            ser.write((output_string + "\n").encode('utf-8'))
        
        display_data.last_display_update = current_time



# Fungsi untuk membaca data dari Arduino dan memprosesnya
def read_and_process_data(ser, csv_path):
    frequencies = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    timers = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    almost_expired = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    expired = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    last_update_time = {'A': time.time(), 'B': time.time(), 'C': time.time(), 'D': time.time()}
    speedup_factors = {'A': 1.25, 'B': 1.75, 'C': 1.5, 'D': 2.5}
    temperature = 0
    last_temp_update = time.time()

    while True:
        current_time = time.time()
        if current_time - last_temp_update >= 20:
            temperature = random.randint(0, 1)
            last_temp_update = current_time

        data_received = False

        if ser.in_waiting > 0:
            raw_data = ser.readline().decode('utf-8').strip()

            if len(raw_data) == 8:
                new_frequencies = {
                    'A': int(raw_data[0:2]),
                    'B': int(raw_data[2:4]),
                    'C': int(raw_data[4:6]),
                    'D': int(raw_data[6:8])
                }

                for product, new_frequency in new_frequencies.items():
                    if new_frequency > frequencies[product]:
                        timers[product] = 0
                        almost_expired[product] = 0
                        expired[product] = 0
                    frequencies[product] = new_frequency
                    last_update_time[product] = current_time
                data_received = True

        for product in timers.keys():
            elapsed_time = current_time - last_update_time[product]
            if temperature == 1:
                timers[product] += elapsed_time * speedup_factors[product]
            else:
                timers[product] += elapsed_time

            last_update_time[product] = current_time

            if timers[product] >= 240:
                expired[product] = 1
                almost_expired[product] = 1
            elif timers[product] >= 120:
                almost_expired[product] = 1
                expired[product] = 0

        # Membaca CSV untuk diproses
        df = read_csv_data(csv_path)
        product_data = process_product_data(df)

        # Memanggil fungsi display_data dengan argumen lengkap
        display_data(frequencies, timers, temperature, almost_expired, expired, data_received, product_data, ser)

        time.sleep(0.1)

# Main program
if __name__ == "__main__":
    csv_path = "okedeh.csv"
    try:
        ser = serial.Serial('COM26', 9600, timeout=1)
        print("Connected to Arduino\n")
        read_and_process_data(ser, csv_path)
    except serial.SerialException as e:
        print(f"Error connecting to serial port: {e}")
