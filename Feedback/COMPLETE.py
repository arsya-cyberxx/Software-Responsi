import asyncio
from bleak import BleakClient
import json
import pandas as pd
import csv
import websockets

# BLE address and characteristic
esp32_characteristic_uuid = "84c4e7af-b494-461b-8c55-125f88183792"
address = "cc:7b:5c:26:cc:0a"
# WebSocket server details (ESP32 IP address and port)
websocket_url = "ws://192.168.18.5:5000"

# Utility functions
def pullcart(df, cartloc): 
    cart = df.iloc[cartloc - 1, 27]  
    elements = [x.strip() for x in cart.split(",")]
    result = [[elements[i], int(elements[i + 1])] for i in range(0, len(elements), 2)]
    return result

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
    df.to_csv('okedeh.csv', index=False)
    print("Database has been updated.")

def update_user_voucher(user_ID, user_voucher, df):
    file_path = 'okedeh.csv'
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
df = pd.read_csv('okedeh.csv')
cartloc = int(input("Nomor cart kamu adalah: "))
cart = pullcart(df, cartloc)
coor, letters = pullitem(cart, df)
item_properties = pullrating(coor, df)

user_ID = df.iloc[cartloc - 1, 26]
user_voucher_eligible = df.iloc[cartloc - 1, 7] == 'yes'

cart_data = {}
for i, product in enumerate(cart):
    rating_total = int(item_properties[i][0])
    rating_frequency = int(item_properties[i][1])
    restock_frequency = int(item_properties[i][2])
    cart_data[product[0]] = {
        "rating_total": rating_total,
        "rating_frequency": rating_frequency,
        "restock_frequency": restock_frequency
    }

data_to_send_ble = {
    "user_ID": str(int(user_ID)),
    "user_voucherEligible": user_voucher_eligible,
    "cart": cart_data
}

update_rating(coor, df, [[product[0], item_properties[i][0], item_properties[i][1]] for i, product in enumerate(cart)], df)
update_user_voucher(str(int(user_ID)), user_voucher_eligible, df)

# Send data via BLE
async def send_via_ble(address, data):
    try:
        async with BleakClient(address, timeout=20.0) as client:
            if client.is_connected:
                await asyncio.sleep(2)  # Allow connection to stabilize
                await client.write_gatt_char(esp32_characteristic_uuid, json.dumps(data).encode('utf-8'))
                print("Data sent via BLE:", json.dumps(data, indent=4))

                # Receive response
                received_data = await client.read_gatt_char(esp32_characteristic_uuid)
                response = json.loads(received_data.decode('utf-8'))
                print("Response from ESP32:", response)
            else:
                print("Failed to connect to BLE device.")
    except Exception as e:
        print(f"BLE error: {e}")

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
    await send_via_ble(address, data_to_send_ble)
    await send_via_websocket()

if __name__ == "__main__":
    asyncio.run(main())
