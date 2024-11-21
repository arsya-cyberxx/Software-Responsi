import csv
import serial  # Modul untuk komunikasi serial 
import pandas as pd  # Modul untuk manipulasi data dalam format seperti CSV
import time
import update_csv  # Modul eksternal (tidak jelas penggunaannya dari kode ini)

# Fungsi untuk mengatur komunikasi serial
def comserial(com_port, baud_rate=9600): 
    # Inisialisasi objek komunikasi serial dengan parameter yang ditentukan
    ser = serial.Serial(
        port=com_port,          # Port komunikasi serial (misalnya COM3)
        baudrate=baud_rate,     # Baud rate untuk komunikasi serial
        parity=None,  # Jenis parity (diatur ke OD)
        stopbits=serial.STOPBITS_ONE,  # Stop bits (1 bit)
        bytesize=serial.EIGHTBITS,  # Ukuran byte (8 bit)
        timeout=3               # Waktu tunggu (timeout) dalam detik
    )
    return ser  # Mengembalikan objek serial

# Fungsi untuk menghitung total harga dari file CSV dan mengubahnya menjadi format biner
def send_stock(file_path, ser):
    # Membaca file CSV ke dalam DataFrame pandas
    df = pd.read_csv(file_path)
    
    # Mendapatkan nilai terakhir yang tidak kosong dari kolom 'cart'
    last_value_cart = df['cart'][df['cart'].notna()].iloc[-1] 
    last_value_cart = last_value_cart.split(",")  # Memisahkan string berdasarkan koma
    
    totalharga = 0  # Variabel untuk menyimpan total harga
    
    # Menghitung total harga berdasarkan item di dalam 'cart'
    for i in range(0, len(last_value_cart), 2):  # Iterasi setiap dua elemen
        if last_value_cart[i] == 'A':
            totalharga += 1 * int(last_value_cart[i+1])  # Harga item A adalah 1
        elif last_value_cart[i] == 'B':
            totalharga += 2 * int(last_value_cart[i+1])  # Harga item B adalah 2
        elif last_value_cart[i] == 'C':
            totalharga += 3 * int(last_value_cart[i+1])  # Harga item C adalah 3
        elif last_value_cart[i] == 'D':
            totalharga += 4 * int(last_value_cart[i+1])  # Harga item D adalah 4
    
    # Konversi total harga menjadi string dan tambahkan nol di depan jika kurang dari 3 digit
    totalharga = str(totalharga)
    if len(totalharga) != 3:
        totalharga = '0' * (3 - len(totalharga)) + totalharga  # Pastikan total harga 3 digit

    ser.write(totalharga.encode())
    return totalharga  # Mengembalikan harga dalam format biner

# Blok utama (dieksekusi jika file ini dijalankan langsung)
if __name__ == "__main__":
    file_path = 'okedeh.csv'  # Nama file CSV untuk input data
    com_port = 'COM3'  # Port komunikasi serial (dapat diubah sesuai kebutuhan)
    baud_rate = 9600  # Baud rate untuk komunikasi serial
    
    try:
        # Panggil fungsi send_stock dan cetak hasilnya
        ser=comserial(com_port,baud_rate)
        print(send_stock(file_path, ser)) 
    except KeyboardInterrupt:
        # Menangani interupsi dari pengguna (Ctrl+C)
        print("Process interrupted. Closing COM port.")
