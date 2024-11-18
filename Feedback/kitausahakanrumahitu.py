import asyncio
from bleak import BleakClient
import json
import pandas as pd
import websockets
#BLE address and characteristic
esp32_characteristic_uuid = "84c4e7af-b494-461b-8c55-125f88183792"
address = "cc:7b:5c:26:cc:0a"
# WebSocket server details (ESP32 IP address and port)
websocket_url = "ws://192.168.18.5:5000"

def pulldatauser(coor, data): 
    user_properties = []
    userID = data.iloc[coor - 1, 26]  
    user_properties.append(userID)
    result = [(i, j) for i in range(len(df)) for j in range(len(df.columns)) if df.iloc[i, j] == userID]
    row, col = result[0]
    user_eligable = data.iloc[row, 7]  
    user_properties.append(user_eligable)
    return user_properties

def pullcart(df, cartloc): 
    cart = df.iloc[cartloc - 1, 27]  
    elements = [x.strip() for x in cart.split(",")]
    result = [[elements[i], int(elements[i + 1])] for i in range(0, len(elements), 2)]
    return result

def pullrating(coor, data):
    itemsprop = []
    for i in coor:
        item_properties = []
        for x in range(3):  
            properties = data.iloc[i, x + 12]  
            item_properties.append(properties)
        itemsprop.append(item_properties)  
    return itemsprop

def pullitem(cart): 
    letters = []
    for item in cart:
        letters.append(item[0])          
    coor = []
    for x in range(len(letters)):
        result = [(i, j) for i in range(len(df)) for j in range(len(df.columns)) if df.iloc[i, j] == letters[x]]
        row, col = result[0]
        coor.append(row)  
    return coor, letters 

df = pd.read_csv('okedeh.csv')

#masukin koordinat buat cart
cartloc = int(input("nomor cart mu adalah: "))
#pull cart dalam csv
cart = pullcart(df, cartloc)
#filter data buat cart
coor , letter = pullitem(cart)
#pull data user 
user = pulldatauser(cartloc, df)
#pull data items 
item_properties = pullrating(coor, df)

# Data from your lists
products = cart
metrics = item_properties
user_data = user

# User info
user_ID = str(int(user_data[0]))  
voucher_eligible = True if user_data[1] == 'yes' else False 

product_identifiers = letter  

code_to_product_name = {
    'A': 'Product A',
    'B': 'Product B',
    'C': 'Product C',
    'D': 'Product D'
}

desired_products = [code_to_product_name[code] for code in product_identifiers]

cart = {}
product_names = [code_to_product_name[item[0]] for item in products]  
for i, product in enumerate(products):
    product_name = product_names[i]
    if product_name in desired_products:  
        quantity = int(product[1])  
        rating_total = int(metrics[i][0])  
        rating_frequency = int(metrics[i][1])  
        restock_frequency = int(metrics[i][2])  

        
        price = 29.99 - i * 10 

        
        cart[product_name] = {
            "price": float(price),  
            "quantity": quantity,
            "rating_total": rating_total,
            "rating_frequency": rating_frequency,
            "restock_frequency" : restock_frequency
        }

data_to_send = {
    "user_ID": user_ID,
    "user_voucherEligible": voucher_eligible,
    "cart": cart
}

json_data = json.dumps(data_to_send).encode('utf-8')

# Define websocket function
async def send_via_websocket(data):
    """Send data to ESP32 via WebSocket."""
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("Connected to WebSocket server.")
            
            # Send the data
            await websocket.send(json.dumps(data))
            print(f"Sent via WebSocket: {json.dumps(data, indent=4)}")

            # Optionally, receive and print acknowledgment from the ESP32
            response = await websocket.recv()
            print(f"Response from WebSocket server: {response}")
    except Exception as e:
        print(f"WebSocket error: {e}")

# Define main function
async def main(address):
    try:
        async with BleakClient(address, timeout=20.0) as client:
            await asyncio.sleep(2)  # Small delay before writing to stabilize the connection
            
            if client.is_connected:
                # Step 1: Send JSON data to the ESP32
                await client.write_gatt_char(esp32_characteristic_uuid, json_data)
                print("Data sent successfully.")

                # Step 2: Wait for ESP32 to process and respond
                await asyncio.sleep(2)  # Adjust delay as necessary

                # Step 3: Read JSON response data from the ESP32
                received_data = await client.read_gatt_char(esp32_characteristic_uuid)
                decoded_data = received_data.decode('utf-8')
                received_json = json.loads(decoded_data)
                # Step 4: Push Data to CSV
                
                # Step 5: Send login_status_off = 0 to ESP32 via WebSocket
                login_status_data = {"login_status_off": 0}
                await send_via_websocket(login_status_data)
            else:
                print("Failed to connect.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main(address))
