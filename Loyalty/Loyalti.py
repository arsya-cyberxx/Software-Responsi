from quart import Quart, jsonify, request
import aiofiles
import asyncio
import csv

app = Quart(__name__)

# CSV filename (assuming it's in the same directory as this Quart file)
csv_filename = 'okedeh (1).csv'

# Function to read user_voucherEligible, user_voucherChange, and user_voucher from CSV asynchronously
async def read_values_from_csv():
    user_voucherEligible = 0  # Default value if no row with login_status=1 is found
    user_voucherChange = 0    # Default value for user_voucherChange
    user_voucher = 0          # Default value for user_voucher

    # Open the CSV file asynchronously and iterate over rows to find login_status=1
    async with aiofiles.open(csv_filename, mode='r') as file:
        csv_reader = csv.reader(await file.readlines())
        rows = list(csv_reader)

        for row in rows[1:]:  # Skip header row
            login_status = row[6].strip()  # 7th column, index 6
            if login_status == '1':
                user_voucherEligible = row[7].strip()  # 8th column, index 7
                user_voucherChange = row[8].strip()    # 9th column, index 8
                user_voucher = row[5].strip()          # 6th column, index 5

                # Convert user_voucherEligible to integer
                if user_voucherEligible.lower() == 'yes':
                    user_voucherEligible = 1
                elif user_voucherEligible.lower() == 'no':
                    user_voucherEligible = 0
                else:
                    user_voucherEligible = int(user_voucherEligible) if user_voucherEligible.isdigit() else 0
                
                # Convert user_voucherChange and user_voucher to integers if possible
                user_voucherChange = int(user_voucherChange) if user_voucherChange.isdigit() else 0
                user_voucher = int(user_voucher) if user_voucher.isdigit() else 0
                
                break  # Stop once we find the first row with login_status=1

    # Print the values for verification in cmd
    print("=== CSV Values ===")
    print(f"user_voucherEligible: {user_voucherEligible}")
    print(f"user_voucherChange: {user_voucherChange}")
    print(f"user_voucher: {user_voucher}")
    print("===================")

    return user_voucherEligible, user_voucherChange, user_voucher

# Route to send voucher_code to ESP32 (or for testing without ESP)
@app.route('/get_data', methods=['GET'])
async def get_data():
    # Retrieve user_voucherEligible, user_voucherChange, and user_voucher from the CSV
    user_voucherEligible, user_voucherChange, user_voucher = await read_values_from_csv()
    
    # Define voucher_code based on conditions
    voucher_code = user_voucher if user_voucherChange == 1 and user_voucherEligible == 1 else 0
    
    # Print voucher_code for verification
    print("=== Voucher Code ===")
    print(f"voucher_code: {voucher_code}")
    print("=====================")
    
    return jsonify({'voucher_code': voucher_code})

# Route to receive updated values from ESP32
@app.route('/update_data', methods=['POST'])
async def update_data():
    try:
        # Get the JSON data from the POST request
        data = await request.get_json()

        # Update the values based on what the ESP32 sent
        user_voucherChange = data.get('user_voucherChange', 0)
        user_voucherEligible = data.get('user_voucherEligible', 0)

        # If the data was received successfully, update user_voucherChange to 2
        user_voucherChange = 2
        print("=== Update Success ===")
        print(f"Updated user_voucherChange to 2")
        print(f"Updated user_voucherEligible: {user_voucherEligible}")
        print("======================")
        
        return jsonify({'status': 'Data received successfully'}), 200

    except Exception as e:
        # If there was an error, update user_voucherChange to 3
        user_voucherChange = 3
        print("=== Update Failed ===")
        print("Failed to update data. Error:", str(e))
        print("======================")
        
        return jsonify({'status': 'Failed to receive data'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
