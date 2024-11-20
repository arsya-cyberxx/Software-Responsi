
import asyncio
from complete import ble_transaction  # Import the BLE function from complete.py
from processor_utils import CartProcessor  # Assuming CartProcessor is in cart_processor.py
from processor_utils import DatabaseProcessor
from complete import websocket_transaction
import pandas as pd
from datetime import datetime
import asyncio
from bleak import BleakClient
import json
import csv
import websockets
from datetime import datetime
websocket_url = "ws://192.168.18.5:5000"
# BLE device address and characteristic UUID
esp32_address = "cc:7b:5c:26:cc:0a"  # Replace with the actual BLE address
esp32_characteristic_uuid = "84c4e7af-b494-461b-8c55-125f88183792"  # Define UUID here if needed in ble_transaction
file_path = "okedeh.csv"
df = pd.read_csv(file_path)
async def main():


    # Process the cart and prepare data
    processor = CartProcessor(df)
    data_to_send_ble = processor.prepare_data_to_send()

    # Call the BLE transaction function
    print("Sending data to BLE device...")
    response = await ble_transaction(esp32_address, data_to_send_ble)
    
    # Initialize the database processor
    processor = DatabaseProcessor(file_path)
    
    # Run the processor with the provided JSON data
    await processor.run(response)
    await websocket_transaction()
    # Handle the response
    if response:
        print("Response received from BLE device:")
        print(response)
    else:
        print("No response or an error occurred during the BLE transaction.")


# Run the main coroutine
if __name__ == "__main__":
    asyncio.run(main())
