import pandas as pd
import json

def pulldatauser(coor, data): 
    user_properties = []
    userID = data.iloc[coor - 1, 26]  # Assuming user ID is in the 27th column
    user_properties.append(userID)
    result = [(i, j) for i in range(len(df)) for j in range(len(df.columns)) if df.iloc[i, j] == userID]
    row, col = result[0]
    user_eligible = data.iloc[row, 7]  # Assuming voucher eligibility is in the 8th column
    user_properties.append(user_eligible)
    return user_properties

def pullcart(df, cartloc): 
    cart = df.iloc[cartloc - 1, 27]  # Assuming cart details are in the 28th column
    elements = [x.strip() for x in cart.split(",")]
    result = [[elements[i], int(elements[i + 1])] for i in range(0, len(elements), 2)]
    return result

def pullrating(coor, data):
    itemsprop = []
    for i in coor:
        item_properties = []
        for x in range(2):  # Assuming rating details start from column 13
            properties = data.iloc[i, x + 12]  
            item_properties.append(properties)
        itemsprop.append(item_properties)  
    return itemsprop

def pullitem(cart): 
    letters = []
    for item in cart:
        letters.append(item[0])  # Get product code        
    coor = []
    for x in range(len(letters)):
        result = [(i, j) for i in range(len(df)) for j in range(len(df.columns)) if df.iloc[i, j] == letters[x]]
        row, col = result[0]
        coor.append(row)  # Collect row indices for each product
    return coor, letters 

def pullrestock(data, coor):
    restock_frequencies = []
    for i in range ( 4 ):
        restock_frequency = data.iloc[i, 12]  # Assuming restock frequency is in the 13th column
        restock_frequencies.append(restock_frequency)
    return restock_frequencies

# Load the CSV file into a DataFrame
df = pd.read_csv('okedeh.csv')

# User's cart location
cartloc = int(input("Nomor cart mu adalah: "))  # For example: 2
cart = pullcart(df, cartloc)
coor, letter = pullitem(cart)
user = pulldatauser(cartloc, df)
item_properties = pullrating(coor, df)
restock_frequencies = (pullrestock(df, coor))# Get restock frequencies for the products


print ( restock_frequencies)
# Data from your lists
products = cart
metrics = item_properties
user_data = user

# User info
user_ID = str(int(user_data[0]))  # Convert the float/int64 user ID to string
voucher_eligible = True if user_data[1] == 'yes' else False  # Determine voucher eligibility



product_identifiers = letter

# Mapping of product codes to their respective product names
code_to_product_name = {
    'A': 'Product A',
    'B': 'Product B',
    'C': 'Product C',
    'D': 'Product D'
}

# Creating a list of desired products based on the product codes
desired_products = [code_to_product_name[code] for code in product_identifiers]

# Creating the cart dictionary dynamically based on the desired products
cart = {}
restock_frequency = {}
product_names = [code_to_product_name[item[0]] for item in products]  # Extract names dynamically

for i, product in enumerate(products):
    product_name = product_names[i]
    if product_name in desired_products:  # Only add the products specified in the desired list
        rating_total = int(metrics[i][0])  # Convert rating_total to int
        rating_frequency = int(metrics[i][1])  # Convert rating_frequency to int
        # Assuming prices are hardcoded or available elsewhere
        cart[product_name] = {
            "rating_total": rating_total,
            "rating_frequency": rating_frequency,
        }

letters = ['A', 'B', 'C', 'D']
for x in range ( len(restock_frequencies)) : 
    restock_frequency[letters[x]] = int(restock_frequencies[x])
    
data_to_send = {
    "user_ID": user_ID,
    "user_voucherEligible": voucher_eligible,
    "cart": cart, 
    "restock_frequency" : restock_frequency
}

# Convert to JSON
json_data = json.dumps(data_to_send, indent=5)

# Print the resulting JSON for verification
print(json_data)
