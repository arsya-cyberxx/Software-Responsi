import serial
import pandas as pd
from datetime import datetime
import time

def monitor_and_update_csv(serial_port, baud_rate, csv_path, delay=1):
    """
    Monitor data from Arduino and update the CSV file with restock information.

    Args:
        serial_port (str): COM port of the Arduino.
        baud_rate (int): Baud rate for the serial connection.
        csv_path (str): Path to the CSV file to update.
        delay (int): Time in seconds between serial reads. Default is 1.
    """
    try:
        # Set up the serial connection
        ser = serial.Serial(serial_port, baud_rate)
        time.sleep(2)  # Wait for Arduino to initialize
        
        # Load the CSV file
        df = pd.read_csv(csv_path)
        print("CSV loaded successfully.")

        # Function to parse Arduino data
        def parse_arduino_data(data):
            # Ensure the data has the expected length
            if len(data) != 8:
                print("Error: Arduino data is not the expected length.")
                return None
            
            # Parse product frequencies
            frequencies = {
                'A': int(data[0:2]),  # Frequency A
                'B': int(data[2:4]),  # Frequency B
                'C': int(data[4:6]),  # Frequency C
                'D': int(data[6:8])   # Frequency D
            }
            return frequencies

        while True:
            if ser.in_waiting > 0:
                # Read and decode the data
                arduino_data = ser.readline().decode('utf-8').strip()  # Remove unwanted chars
                print("Arduino data received:", arduino_data)

                # Parse the data
                frequencies = parse_arduino_data(arduino_data)
                if frequencies:
                    # Process each product
                    for product, new_frequency in frequencies.items():
                        # Locate the row based on Product ID in Column 'product_ID'
                        product_row = df[df['product_ID'] == product]

                        if not product_row.empty:
                            # Get the current restock frequency
                            current_frequency = product_row.iloc[0]['product_restockFrequency']

                            # Update only if there is a change in restock frequency
                            if current_frequency != new_frequency:
                                df.loc[product_row.index, 'product_restockFrequency'] = new_frequency
                                df.loc[product_row.index, 'product_stock'] = 15  # Reset stock to 15
                                df.loc[product_row.index, 'product_lastRestock'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                                print(f"Product {product}: restock frequency updated to {new_frequency}, stock reset to 15, and restock timestamp updated.")
                        else:
                            print(f"Product {product} not found in CSV.")
                    
                    # Save the updated CSV file
                    df.to_csv(csv_path, index=False)
                    print("CSV file updated successfully.")
                else:
                    print("Failed to parse Arduino data.")
                
                time.sleep(delay)  # Small delay to avoid excessive reads
    except KeyboardInterrupt:
        print("Program stopped manually.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'ser' in locals():
            ser.close()
        print("Serial connection closed.")

# Example Usage
if __name__ == "__main__":
    monitor_and_update_csv(
        serial_port='COM14', 
        baud_rate=9600, 
        csv_path=r"D:\VSCode\okedeh.csv", 
        delay=1
    )
