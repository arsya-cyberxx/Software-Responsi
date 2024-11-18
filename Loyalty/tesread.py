
import csv
import os



def read_user_voucherEligible_from_csv():
    # Adjust path to navigate up one level from the current file's directory
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'okedeh (1).csv')
    
    # Read the specific cell for user_voucherEligible
    with open(csv_path, mode='r') as file:
        csv_reader = csv.reader(file)
        rows = list(csv_reader)  # Convert CSV data to a list of rows
        
        try:
            user_voucherEligible = rows[1][7].strip()  # 8th column (index 7), 2nd row (index 1)
            if user_voucherEligible == 'yes':  # Convert 'yes'/'no' to 1/0 for consistency
                user_voucherEligible = 1
            elif user_voucherEligible == 'no':
                user_voucherEligible = 0
            else:
                user_voucherEligible = int(user_voucherEligible) if user_voucherEligible.isdigit() else 0
        except (IndexError, ValueError) as e:
            print(f"Error reading user_voucherEligible: {e}")
            user_voucherEligible = 0  # Default to 0 if there's an error
    return user_voucherEligible


print("read_user_voucherEligible_from_csv", read_user_voucherEligible_from_csv())