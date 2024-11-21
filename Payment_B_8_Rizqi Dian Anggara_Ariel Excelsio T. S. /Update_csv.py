import serial  # Modul untuk komunikasi serial
import csv  # Modul untuk membaca dan menulis file CSV
import pandas as pd  # Modul untuk manipulasi data

# Fungsi untuk inisialisasi komunikasi serial
def comserial(port, baudrate):
    # Membuat objek serial untuk komunikasi dengan perangkat tertentu
    com = serial.Serial(
        port='COM3',       # Port serial (ubah sesuai kebutuhan)
        baudrate=19200     # Baud rate komunikasi
    )
    return com  # Mengembalikan objek serial

# Fungsi asinkron untuk memperbarui file CSV berdasarkan data dari komunikasi serial
async def update_csv(com, file_path):
    # Membaca data dari serial (dalam bentuk byte) dan mengubahnya menjadi string
    com_bytes = await com.readline()  # Membaca satu baris data
    data = com_bytes.decode("unicode").strip()  # Decode data ke string dan hapus spasi/karakter tak terlihat

    # Jika data dari serial menunjukkan pembayaran berhasil
    if data == 'Pembayaran berhasil':
        # Membaca file CSV ke dalam DataFrame pandas
        df = pd.read_csv(file_path)
        
        # Mengambil nilai terakhir yang tidak kosong dari kolom 'cart'
        last_value_cart = df['cart'][df['cart'].notna()].iloc[-1] 
        cart_items = last_value_cart.split(',')  # Memisahkan string berdasarkan koma
        
        # Menghapus spasi di sekitar setiap item dalam `cart_items`
        for i in range(len(cart_items)):
            cart_items[i] = cart_items[i].strip()
        
        # Membuka file CSV dalam mode baca-tulis ('r+') untuk memperbarui stok
        with open(file_path, mode='r+', newline='') as file:
            reader = csv.DictReader(file)  # Membaca file sebagai dictionary
            rows = []  # Daftar untuk menyimpan baris data baru
            
            # Iterasi setiap baris dalam file CSV
            for row in reader:
                stock_name = row['product_ID']  # Mendapatkan ID produk
                
                # Jika produk ada dalam daftar `cart_items`
                if stock_name in cart_items:
                    index = cart_items.index(stock_name)  # Mendapatkan indeks produk dalam daftar
                    quantity_to_deduct = int(cart_items[index + 1])  # Jumlah yang harus dikurangi
                    
                    # Mendapatkan stok saat ini (default 0 jika kosong)
                    current_quantity = int(row['product_stock']) if row['product_stock'] else 0
                    updated_quantity = current_quantity - quantity_to_deduct  # Mengurangi stok
                    row['product_stock'] = int(updated_quantity)  # Memperbarui stok dalam baris
                
                rows.append(row)  # Menambahkan baris ke daftar baru
            
            # Kembali ke awal file untuk menulis data yang diperbarui
            file.seek(0)
            writer = csv.DictWriter(file, fieldnames=reader.fieldnames)  # Membuat writer dengan header
            writer.writeheader()  # Menulis header ke file
            writer.writerows(rows)  # Menulis semua baris baru ke file
            file.truncate()  # Memotong file jika ada data sisa dari sebelumnya

        return "Stok diperbarui."  # Mengembalikan pesan keberhasilan
    return "Gagal"  # Mengembalikan pesan gagal jika data bukan 'Pembayaran berhasil'
