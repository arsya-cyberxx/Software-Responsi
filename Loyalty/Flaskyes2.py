from flask import Flask, jsonify, request

app = Flask(__name__)

# Initial values of the variables
user_voucher = 42  # This is the voucher value, range 00-99
user_voucherChange = 1  # Initial value (1, 2, or 3)
user_voucherEligible = 1  # Initial value (0 or 1)

# Route to send user_voucher, user_voucherChange, and user_voucherEligible to ESP32
@app.route('/get_data', methods=['GET'])
def get_data():
    return jsonify({
        'user_voucher': user_voucher,
        'user_voucherChange': user_voucherChange,
        'user_voucherEligible': user_voucherEligible
    })

# Route to receive updated values from ESP32
@app.route('/update_data', methods=['POST'])
def update_data():
    global user_voucherChange, user_voucherEligible

    # Get the JSON data from the POST request
    data = request.get_json()
    
    # Update the values based on what the ESP32 sent
    user_voucherChange = data.get('user_voucherChange', user_voucherChange)
    user_voucherEligible = data.get('user_voucherEligible', user_voucherEligible)
    
    print(f"Updated user_voucherChange: {user_voucherChange}")
    print(f"Updated user_voucherEligible: {user_voucherEligible}")

    return jsonify({'status': 'Data received successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
