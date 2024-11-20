from quart import Quart, jsonify, request
import aiofiles
import asyncio
import csv
from datetime import datetime

csv_filename = 'okedeh.csv'

# Quart app initialization
loyalti_app = Quart(__name__)

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

    return user_voucherEligible, user_voucherChange, user_voucher

# Route to get voucher data
@loyalti_app.route('/get_data', methods=['GET'])
async def get_data():
    user_voucherEligible, user_voucherChange, user_voucher = await read_values_from_csv()
    voucher_code = user_voucher if user_voucherChange == 1 and user_voucherEligible == 1 else 0
    return jsonify({'user_voucher': voucher_code})

# Route to update voucher data
@loyalti_app.route('/update_data', methods=['POST'])
async def update_data():
    try:
        data = await request.get_json()
        user_voucherEligible = data.get('user_voucherEligible', 0)
        new_voucherChange = data.get('user_voucherChange', 0)

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

# Timer-based function to check CSV
async def timer_check():
    try:
        current_time = datetime.now()
        async with aiofiles.open(csv_filename, mode='r') as file:
            rows = await file.readlines()

        csv_reader = csv.reader(rows)
        updated_rows = []

        for i, row in enumerate(csv_reader):
            if i == 0:
                updated_rows.append(row)  # Keep header row
                continue

            login_status = row[6].strip()
            timestamp = row[25].strip()

            if login_status == '1' and timestamp:
                try:
                    time_part = datetime.strptime(timestamp, '%H:%M:%S').time()
                    row_time = datetime.combine(current_time.date(), time_part)
                    time_diff = (current_time - row_time).total_seconds() / 60  # Difference in minutes

                    if time_diff > 5:  # 5-minute timer
                        row[8] = '2'  # Update user_voucherChange
                except ValueError:
                    pass  # Skip invalid timestamps

            updated_rows.append(row)

        # Write updated rows back to the CSV
        async with aiofiles.open(csv_filename, mode='w') as file:
            for row in updated_rows:
                await file.write(','.join(row) + '\n')

    except Exception as e:
        print(f"Error in timer check: {e}")

# Timer background task
async def start_timer():
    while True:
        await timer_check()
        await asyncio.sleep(5)  # Check every 5 seconds

@loyalti_app.before_serving
async def setup_timer():
    asyncio.create_task(start_timer())

# Loyalti function to run the Quart app
async def loyalti():
    await loyalti_app.run_task(host='0.0.0.0', port=5000, debug=True)
