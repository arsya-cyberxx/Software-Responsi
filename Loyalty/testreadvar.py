import csv
import os

def read_user_voucherEligible_from_csv():
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'okedeh (1).csv')
    
    with open(csv_path, mode='r') as file:
        csv_reader = csv.reader(file)
        rows = list(csv_reader)
        
        user_voucherEligible = 0  # Default value if no row with login_status=1 is found
        
        # Iterate over rows starting from the 2nd row
        for row in rows[1:]:
            login_status = row[6].strip()  # 7th column, index 6
            if login_status == '1':
                user_voucherEligible = row[7].strip()  # 8th column, index 7
                if user_voucherEligible.lower() == 'yes':
                    user_voucherEligible = 1
                elif user_voucherEligible.lower() == 'no':
                    user_voucherEligible = 0
                else:
                    user_voucherEligible = int(user_voucherEligible) if user_voucherEligible.isdigit() else 0
                break  # Stop searching once we find the first row with login_status=1
        
    return user_voucherEligible

# Call the function and print the result
print("user_voucherEligible for login_status=1:", read_user_voucherEligible_from_csv())
