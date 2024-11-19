import json
import pandas as pd 
# Sample JSON data
json_data = '''

{
    "user_ID": "333",
    "user_voucherEligible": false,
    "cart": {
        "Product A": {
            "price": 29.99,
            "quantity": 1,
            "rating_total": 40,
            "rating_frequency": 12000000,
            "restock_frequency": 40
        },
        "Product B": {
            "price": 19.99,
            "quantity": 2,
            "rating_total": 40,
            "rating_frequency": 80,
            "restock_frequency": 40
        }
    }
}

'''

def update_voucher_time_in_dataframe(user_ID: int, user_voucher: int, time: datetime, data: pd.DataFrame) -> pd.DataFrame:
    """
    Update the 'user_voucher' and 'voucher_time' columns for the given user_ID in the provided DataFrame.

    Args:
    user_ID (int): The ID of the user to update.
    user_voucher (int): The voucher value to assign to the user.
    time (datetime): The datetime when the voucher is assigned.
    data (pd.DataFrame): The DataFrame containing the data.

    Returns:
    pd.DataFrame: The updated DataFrame with the new values.
    """
    # Check if the user_ID exists in the dataset
    if user_ID in data['user_ID'].values:
        # Update the relevant row
        data.loc[data['user_ID'] == user_ID, 'user_voucher'] = user_voucher
        data.loc[data['user_ID'] == user_ID, 'voucher_time'] = time.strftime('%H:%M:%S')
        print(f"Updated user_ID {user_ID} with user_voucher {user_voucher} and voucher_time {time.strftime('%H:%M:%S')}")
    else:
        print(f"user_ID {user_ID} not found in the dataset.")
    return data

def update_rating(coor, data, new_rating):
    itemsprop = []
    for i in coor:
        for x in range(3):  
            data.iloc[i, x + 12] = new_rating[i][x+3]
    df.to_csv('okedeh.csv', index=False)
    print (" database has been updated ")
    return itemsprop

def pullproduct ( cart) :
    
    product = []
    for i in range  ( len ( cart )) : 
        letters = cart [i][0]
        product.append ( letters)
    
    product_id = [item.replace('Product ', '') for item in product]
    
    coor = [ ]
    for x in range(len(product_id)):
        result = [(i, j) for i in range(len(df)) for j in range(len(df.columns)) if df.iloc[i, j] == product_id[x]]
        row, col = result[0]
        coor.append(row)  
        
    return (coor)

df = pd.read_csv('okedeh.csv')


data = json.loads(json_data)


user_info = [data["user_ID"], data["user_voucherEligible"]]

cart_items = []
for product, details in data["cart"].items():
    # Convert each product's details into a list
    item = [product, details["price"], details["quantity"], details["rating_total"], details["rating_frequency"], details["restock_frequency"]]
    cart_items.append(item)

result = [user_info, cart_items]

coor = pullproduct (cart_items )

update_rating ( coor, df , cart_items)
