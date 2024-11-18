import asyncio
from bleak import BleakClient
import json

esp32_characteristic_uuid = "84c4e7af-b494-461b-8c55-125f88183792"
address = "cc:7b:5c:26:cc:0a"

# JSON data to send to the ESP32
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
                
                print("Data received successfully:")
                print(json.dumps(received_json, indent=4))  # Print JSON data in a readable format
            else:
                print("Failed to connect.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main(address))
    nnn