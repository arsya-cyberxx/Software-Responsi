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



async def ble_transaction(address,data):
    try:
        async with BleakClient(address, timeout=20.0) as client:
            if client.is_connected:
                await client.write_gatt_char(esp32_characteristic_uuid, json.dumps(data).encode('utf-8'))
                print("Data sent via BLE:", json.dumps(data, indent=4))
                # Receive response
                received_data = await client.read_gatt_char(esp32_characteristic_uuid)
                response = json.loads(received_data.decode('utf-8'))
                return response  # Return the response received from ESP32
            else:
                print("Failed to connect to BLE device.")
                return None
    except Exception as e:
        print(f"BLE error: {e}")
        return None  # Return None in case of an exception


# Send `login_status=0` via WebSocket
async def websocket_transaction():
    try:
        async with websockets.connect(websocket_url) as websocket:
            login_status_data = {"login_status": 0}
            await websocket.send(json.dumps(login_status_data))
    except Exception as e:
        print(f"WebSocket error: {e}")








# # Main function
# async def main():
#     await send_via_ble(address, data_to_send_ble, df, coor, cart, item_properties, user_ID, user_voucher_eligible)
#     await send_via_websocket()

# if __name__ == "__main__":
#     asyncio.run(main())
