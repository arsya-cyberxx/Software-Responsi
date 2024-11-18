from quart import Quart, jsonify, request
import aiofiles
import asyncio
import csv
from io import StringIO

app = Quart(__name__)

csv_filename = 'okedeh (1).csv'

# Function to read CSV values
async def read_values_from_csv():
    user_voucherEligible = 0
    user_voucherChange = 0
    user_voucher = 0

    async with aiofiles.open(csv_filename, mode='r') as file:
        rows = await file.readlines()
        csv_reader = csv.reader(rows)

        for i, row in enumerate(csv_reader):
            if i == 0:
                continue  # Skip header
            login_status = row[6].strip()
            if login_status == '1':  # Match login status
                user_voucherEligible = 1 if row[7].strip().lower() == 'yes' else 0
                user_voucherChange = int(row[8].strip()) if row[8].strip().isdigit() else 0
                user_voucher = int(row[5].strip()) if row[5].strip().isdigit() else 0
                break  # Process only the first matching row
    # Print the values for verification in cmd
    print("=== CSV Values ===")
    print(f"user_voucherEligible: {user_voucherEligible}")
    print(f"user_voucherChange: {user_voucherChange}")
    print(f"user_voucher: {user_voucher}")
    print("===================")

    return user_voucherEligible, user_voucherChange, user_voucher

# Route to get voucher data
@app.route('/get_data', methods=['GET'])
async def get_data():
    user_voucherEligible, user_voucherChange, user_voucher = await read_values_from_csv()
    voucher_code = user_voucher if user_voucherChange == 1 and user_voucherEligible == 1 else 0
    return jsonify({'user_voucher': voucher_code})
   

# Route to update voucher data
@app.route('/update_data', methods=['POST'])
async def update_data():
    try:
        data = await request.get_json()
        status = data.get('status', 0)
        new_voucherChange = data.get('user_voucherChange', 0)
        user_voucherEligible = data.get('user_voucherEligible', 0)

        async with aiofiles.open(csv_filename, mode='r') as file:
            rows = await file.readlines()

        csv_reader = csv.reader(rows)
        updated_rows = []
        for i, row in enumerate(csv_reader):
            if i == 0:
                updated_rows.append(row)  # Add header
            else:
                login_status = row[6].strip()
                if login_status == '1':  # Only update rows with login_status == '1'
                    row[7] = str(user_voucherEligible)  # Update eligibility
                    row[8] = str(new_voucherChange)  # Update change
                updated_rows.append(row)

        # Write updated rows back to the CSV
        async with aiofiles.open(csv_filename, mode='w') as file:
            for row in updated_rows:
                await file.write(','.join(row) + '\n')

        return jsonify({'status': 'Data updated successfully'}), 200

    except Exception as e:
        return jsonify({'status': 'Failed to update data', 'error': str(e)}), 500

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
