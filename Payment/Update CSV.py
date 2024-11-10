import serial
import csv

com = serial.Serial(port='COM4',
                    baudrate=19200,
                    parity=serial.PARITY_EVEN,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=3)

com_bytes = com.readline()
data = com_bytes.decode("unicode").strip()

file_path = 'okedeh.csv'

with open(file_path, mode='r+', newline='') as file:
    reader = csv.DictReader(file)
    rows = []

    cart_items = data.split(',')

    for row in reader:
        stock_name = row['stock']

        if stock_name in cart_items:
            index = cart_items.index(stock_name)
            quantity_to_deduct = int(cart_items[index + 1])
            
            current_quantity = int(row['quantity'])
            updated_quantity = max(current_quantity - quantity_to_deduct, 0)
            row['quantity'] = str(updated_quantity)
        
        rows.append(row)

    file.seek(0)
    writer = csv.DictWriter(file, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    file.truncate() 

print("Stok diperbarui.")
