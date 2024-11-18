import asyncio
from bleak import BleakClient
import json
import pandas as pd
import csv
import websockets
from datetime import datetime
# BLE address and characteristic
esp32_characteristic_uuid = "84c4e7af-b494-461b-8c55-125f88183792"
address = "cc:7b:5c:26:cc:0a"
websocket_url = "ws://192.168.18.5:5000"
csv_file = "okedeh.csv"
current_time = str(datetime.now().time())

# Utility functions
def pullcart(df, cartloc): 
    cart = df.iloc[cartloc - 1, 27]  
    elements = [x.strip() for x in cart.split(",")]
    result = [[elements[i], int(elements[i + 1])] for i in range(0, len(elements), 2)]
    return result

def pullrestock(data, coor):
    restock_frequencies = []
    for i in range ( 4 ):
        restock_frequency = data.iloc[i, 12]  # Assuming restock frequency is in the 13th column
        restock_frequencies.append(restock_frequency)
    return restock_frequencies

def pullitem(cart, df): 
    letters = [item[0] for item in cart]
    coor = []
    for letter in letters:
        result = [(i, j) for i in range(len(df)) for j in range(len(df.columns)) if df.iloc[i, j] == letter]
        if result:
            row, col = result[0]
            coor.append(row)
    return coor, letters

def pullrating(coor, df):
    itemsprop = []
    for i in coor:
        item_properties = [df.iloc[i, x + 12] for x in range(3)]  
        itemsprop.append(item_properties)  
    return itemsprop

def update_rating(coor, data, new_rating, df):
    for i in range(len(coor)):
        for x in range(2):  
            data.iloc[coor[i], x + 13] = new_rating[i][x + 1]
    df.to_csv(csv_file, index=False)
    print("Database has been updated.")

def update_user_voucher(user_ID, user_voucher, df):
    file_path = csv_file
    data = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['user_ID'] == user_ID:
                row['user_voucher'] = user_voucher
            data.append(row)
    with open(file_path, 'w', newline='') as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print("User voucher updated.")

# Prepare the cart and user data
df = pd.read_csv(csv_file)
cartloc = int(input("Nomor cart kamu adalah: "))
cart = pullcart(df, cartloc)
coor, letters = pullitem(cart, df)
restock_frequencies = (pullrestock(df, coor))# Get restock frequencies for the products
item_properties = pullrating(coor, df)

user_ID = df.iloc[cartloc - 1, 26]
user_voucher_eligible = df.iloc[cartloc - 1, 7] == 'yes'

cart_data = {}
for i, product in enumerate(cart):
    rating_total = int(item_properties[i][0])
    rating_frequency = int(item_properties[i][1])
    cart_data[product[0]] = {
        "rating_total": rating_total,
        "rating_frequency": rating_frequency,
    }

restock_frequency = {}
letters = ['A', 'B', 'C', 'D']
for x in range (len(restock_frequencies)) : 
    restock_frequency[letters[x]] = int(restock_frequencies[x])

data_to_send_ble = {
    "user_ID": str(int(user_ID)),
    "user_voucherEligible": user_voucher_eligible,
    "cart": cart_data,
    "restock_frequency" : restock_frequency
}


# Send data via BLE
# BLE Communication
async def send_via_ble(address, data, df, coor, cart, item_properties, user_ID, user_voucher_eligible):
    try:
        async with BleakClient(address, timeout=20.0) as client:
            if client.is_connected:
                await client.write_gatt_char(esp32_characteristic_uuid, json.dumps(data).encode('utf-8'))
                print("Data sent via BLE:", json.dumps(data, indent=4))

                # Receive response
                received_data = await client.read_gatt_char(esp32_characteristic_uuid)
                response = json.loads(received_data.decode('utf-8'))
                print("Response from ESP32:", response)

                return response  # Return the response received from ESP32
            else:
                print("Failed to connect to BLE device.")
                return None
    except Exception as e:
        print(f"BLE error: {e}")
        return None  # Return None in case of an exception


# Send `login_status=0` via WebSocket
async def send_via_websocket():
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("Connected to WebSocket server.")
            login_status_data = {"login_status": 0}
            await websocket.send(json.dumps(login_status_data))
            print("Login status sent via WebSocket:", login_status_data)
    except Exception as e:
        print(f"WebSocket error: {e}")

# Main function
async def main():
    await send_via_ble(address, data_to_send_ble, df, coor, cart, item_properties, user_ID, user_voucher_eligible)
    await send_via_websocket()

if __name__ == "__main__":
    asyncio.run(main())
