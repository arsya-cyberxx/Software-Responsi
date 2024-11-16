import serial
import csv
import pandas as pd

def comserial(port, baudrate):
    com = serial.Serial(port='COM3',
                    baudrate=19200)
    return com

async def update_csv(com, file_path):
    com_bytes = await com.readline()
    data = com_bytes.decode("unicode").strip()

    if data=='Pembayaran berhasil':
        df=pd.read_csv(file_path)
        last_value_cart = df['cart'][df['cart'].notna()].iloc[-1] 
        cart_items = last_value_cart.split(',')
        for i in range(cart_items):
            cart_items[i]=cart_items[i].strip()
            
        with open(file_path, mode='r+', newline='') as file:
            reader = csv.DictReader(file)
            rows = []

            for row in reader:
                stock_name = row['product_ID']

                if stock_name in cart_items:
                    index = cart_items.index(stock_name)
                    quantity_to_deduct = int(cart_items[index + 1])
                    
                    current_quantity = int(row['product_stock']) if row['product_stock'] else 0
                    updated_quantity = current_quantity - quantity_to_deduct
                    row['product_stock'] = int(updated_quantity)
                
                rows.append(row)

            file.seek(0)
            writer = csv.DictWriter(file, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            file.truncate() 

        return "Stok diperbarui."
    return "Gagal"
