import serial
import csv
import pandas as pd

# com = serial.Serial(port='COM3',
#                     baudrate=19200,
#                     parity=serial.PARITY_EVEN,
#                     stopbits=serial.STOPBITS_ONE,
#                     bytesize=serial.EIGHTBITS,
#                     timeout=3)

# com_bytes = com.readline()
# data = com_bytes.decode("unicode").strip()

file_path = 'okedehh.csv'
df=pd.read_csv(file_path)
last_value_cart = df['cart'][df['cart'].notna()].iloc[-1] 

with open(file_path, mode='r+', newline='') as file:
    reader = csv.DictReader(file)
    rows = []

    cart_items = last_value_cart.split(',')

    for row in reader:
        stock_name = row['product_ID']

        if stock_name in cart_items:
            index = cart_items.index(stock_name)
            quantity_to_deduct = int(cart_items[index + 1])
            
            current_quantity = int(row['product_stock']) if row['product_stock'] else 0
            updated_quantity = max(current_quantity - quantity_to_deduct, 0)
            row['product_stock'] = int(updated_quantity)
        
        rows.append(row)

    file.seek(0)
    writer = csv.DictWriter(file, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    file.truncate() 

print("Stok diperbarui.")