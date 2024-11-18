import asyncio
from bleak import BleakClient
import json
import websockets

# Constants for BLE communication
esp32_characteristic_uuid = "84c4e7af-b494-461b-8c55-125f88183792"
ble_address = "cc:7b:5c:26:cc:0a"

# WebSocket server details (ESP32 IP address and port)
websocket_url = "ws://192.168.18.5:5000"

# JSON data to send to the ESP32 via BLE
data_to_send = {
    "user_ID": "IqbalNinalove",
    "user_voucherEligible": True,
    "cart": {
        "Product A": {
            "price": 29.99,
            "quantity": 2
        }
    },
    "rating_total": 45,
    "rating_frequency": 10
}

json_data = json.dumps(data_to_send).encode('utf-8')

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

async def main(address):
    try:
        async with BleakClient(address, timeout=20.0) as client:
            await asyncio.sleep(2)  # Small delay before writing to stabilize the connection
            
            if client.is_connected:
                # Step 1: Send JSON data to the ESP32 via BLE
                await client.write_gatt_char(esp32_characteristic_uuid, json_data)
                print("Data sent successfully via BLE.")

                # Step 2: Wait for ESP32 to process and respond
                await asyncio.sleep(2)  # Adjust delay as necessary

                # Step 3: Read JSON response data from the ESP32
                received_data = await client.read_gatt_char(esp32_characteristic_uuid)
                decoded_data = received_data.decode('utf-8')
                received_json = json.loads(decoded_data)
                
                print("Data received successfully via BLE:")
                print(json.dumps(received_json, indent=4))  # Print JSON data in a readable format

                # Step 4: Send login_status_off = 0 to ESP32 via WebSocket
                login_status_data = {"login_status_off": 0}
                await send_via_websocket(login_status_data)

            else:
                print("Failed to connect via BLE.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main(ble_address))
