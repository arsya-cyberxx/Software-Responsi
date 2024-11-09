import csv

def update_stock_from_cart(file_path):
    with open(file_path, mode='r+', newline='') as file:
        reader = csv.DictReader(file)
        rows = []
      
        for row in reader:
            if 'product stock' in row and 'cart' in row:
                product_stock = eval(row['product stock']) if row['product stock'] else {}

                if row['cart']:
                    cart_items = row['cart'].split(', ')
                    for i in range(0, len(cart_items), 2):
                        product = cart_items[i]
                        quantity = int(cart_items[i + 1])
                        
                        if product in product_stock:
                            product_stock[product] = max(product_stock[product] - quantity, 0)
                
                # Update kolom 'product stock' dengan hasil baru
                row['product stock'] = str(product_stock)
            rows.append(row)
        
        # Reset pointer file dan tulis ulang data yang telah diubah
        file.seek(0)
        writer = csv.DictWriter(file, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        file.truncate()  # Potong sisa file agar tidak ada data lama
    
    print("Stok produk berhasil diperbarui berdasarkan cart.")

file_path = 'okedeh.csv'
update_stock_from_cart(file_path)
