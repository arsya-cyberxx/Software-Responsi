import json
import pandas as pd 
import csv 
import asyncio
import pandas as pd 


def update_rating(coor, data, new_rating ,df ):
    itemsprop = []
    for i in coor:
        for x in range(2):  
            data.iloc[i, x + 13] = new_rating[i][x+1]
    df.to_csv('okedeh.csv', index=False)
    print (" database has been updated ")
    return itemsprop

def pullproduct ( cart , df ) :
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

async def run(json_data) : 
    df = pd.read_csv('okedeh.csv')
    data = json.loads(json_data)
    user_info = [data["user_ID"], data["user_voucher"]]
    cart_items = []
    for product, details in data["cart"].items():
    # Convert each product's details into a list
        item = [product, details["rating_total"], details["rating_frequency"]]
        cart_items.append(item)

    coor = pullproduct (cart_items, df )
    print (cart_items)
    update_rating ( coor, df , cart_items, df)
    file_path = 'okedeh.csv'
    data = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
        # Update the voucher for user_id 111
            if row['user_ID'] == user_info[0]:
                row['user_voucher'] = user_info[1]  # Replace 'NEW_VOUCHER_VALUE' with the actual value you want to set
            data.append(row)

# Write the updated data back to the CSV
    with open(file_path, 'r+', newline='') as csvfile:
        fieldnames = data[0].keys()  # Get the field names from the data
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    
    print ( user_info ) 
