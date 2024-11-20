# main.py is a program that runs all of the pulling and pushing the data in the database, 
# it uses event driven architecture to run every program
# Created by = Emanuel Adi Krisna (502840)
# Puji tuhan yesus kristus bisa jalan cause I dont know what to do if it fails lmao


'''
"Heavenly Father,
Thank You for the gift of creativity and knowledge You’ve given me.
I dedicate this code to You, asking for wisdom and clarity as I work. 
Bless the lines of code to function as intended,
free from errors and issues, and let it serve a purpose that aligns with Your will. 
May this project bring value, inspire others, and glorify Your name. 
Let my efforts reflect diligence, integrity, and excellence as I trust in You.
Amen."
'''

#import some libraries that is relevant
import asyncio , time , csv
import paymentpull , restocks , securities
import pengirim
import penerima
import mainiqbal
import Loyalti
import pandas as pd
from datetime import datetime
import os
import restockcheck
from restockcheck import restockchecks
# Read and define the database as a variable
df = pd.read_csv("okedeh.csv")
data = pd.read_csv("okedeh.csv")
# make a class that act as a broker that runs the event name
class EventEmitter:
    def __init__(self):
        self._listeners = {}
    def on(self, event_name, listener):
        """Registers a listener for a specific event."""
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)

    async def emit(self, event_name, *args):
        """Emits an event, calling all registered listeners for the event."""
        if event_name in self._listeners:
            for listener in self._listeners[event_name]:
                return await listener(*args)



async def restockcheck () : 
    while True :
        task1 = asyncio.create_task(restockcheck.run(df))
        await asyncio.sleep (2)
        await task1
        updatedata = restockchecks(df)
    
    
async def security() :
    task1 = asyncio.create_task(securities)
    status , login , date , user_ID, passwords  = await task1 
    data.loc[data['user_ID'].astype(str).str.strip() == user_ID, 'login_status'] = login
    data.loc[data['user_ID'].astype(str).str.strip() == user_ID, 'user_lastLogin'] = date 
    data.loc[data['user_ID'].astype(str).str.strip() == user_ID, 'user_password'] = passwords
    df['user ID'][df['user ID'].notna()].iloc[0] = user_ID
    data.to_csv('okedeh.csv', index=False)
    print("Data saved to CSV.")
    return status 

# function to run the multi-item selector sub-system
async def multiitemmengirim(file_path):
        pengirim.mengirim(file_path)
        return "multiitem menerima"

async def multiitemmenerima(file_path):
        data_json=penerima.menerima(file_path)
        if not os.path.exists(file_path):
            df = pd.DataFrame(columns=['cart'])
        else:
            df = pd.read_csv(file_path)
        if 'cart' not in df.columns:
            df['cart'] = ''
        new_row = pd.DataFrame({'cart': [data_json]})
        df = pd.concat([df, new_row], ignore_index=True)
    # Save updated DataFrame back to CSV
        df.to_csv(file_path, index=False)
        print("Data saved to CSV.")
    # Disconnect the client after the first message is received and processed
        print("Message received and CSV updated. Disconnecting...")
        return "loyalti"

# function to run the payment sub-system
async def payment():
    print ( "login attempted has started")
    task2 = asyncio.create_task(paymentpull.run())
    status, cart_items = await task2
    with open(df, mode='r+', newline='') as file:
        reader = csv.DictReader(file)
        rows = []
        for row in reader:
            stock_name = row['product_ID']
            if stock_name in cart_items:
                index = cart_items.index(stock_name)
                quantity_to_deduct = int(cart_items[index + 1])
                current_quantity = int(row['product_stock']) if row['product_stock'] else 0
                updated_quantity = current_quantity - quantity_to_deduct
                row['product_stock'] = int(updated_quantity)
            rows.append(row)
            file.seek(0)
            writer = csv.DictWriter(file, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            file.truncate() 
    return status

# function to run the loyalti sub-system

async def loyalti():
    await Loyalti.loyalti()
    return "payment"

#ini w percaya ma iqbal codingannya bisa ke save sumpah karena w nggak tau beneran bisa ke save apa nggak 
async def feedback () :
    task5 =asyncio.create_task(mainiqbal.main())
    status = await task5
    return status

# function to run the restock sub-system
async def restock () : 
    task3 = asyncio.creat_task(restocks.run ())
    status , frequencies = await task3 
    if frequencies:
        # Process each product
        for product, new_frequency in frequencies.items():
            product_row = df[df['product_ID'] == product]
            if not product_row.empty:
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
                df.to_csv(df, index=False)
                print("CSV file updated successfully.")
        else:
            print("Failed to parse Arduino data.")
            delay = 1 
            time.sleep(delay)  # Small delay to avoid excessive reads
        return status

async def selesai () :
    await print ("Terima kasih sudah menggunakan jasa kami")
    
    
# Instantiate EventEmitter and register the listener
event_emitter = EventEmitter()
event_emitter.on("restockcheck", )
event_emitter.on("secuity", security)
event_emitter.on("payment", payment)
event_emitter.on("multiitem mengirim", multiitemmengirim)
event_emitter.on("multiitem menerima", multiitemmenerima)
event_emitter.on("loyalti", loyalti)
event_emitter.on("feedback", feedback)
event_emitter.on("restock", restock)
event_emitter.on("selesai", selesai)


# Main function that runs the event driven
async def main():
    await event_emitter.emit("restockcheck")
    user_input = "start"
    while True:
        if user_input == "start":
            user_input = await event_emitter.emit("security")
        elif user_input == "multiitemmengirim":
            user_input = await event_emitter.emit("multiitem mengirim")
        elif user_input == "multiitem menerima": 
            user_input = await event_emitter.emit("multiitem menerima")
        elif user_input == "payment":
            user_input = await event_emitter.emit("payment")
        elif user_input == "loyalti":
            user_input = await event_emitter.emit ("loyalti")
        elif user_input == "feeback":
            user_input = await event_emitter.emit ("feedback")
        elif user_input == "restock":
            user_input = await event_emitter.emit ("restock")
        elif user_input == "selesai":
            user_input = await event_emitter.emit ("selesai")
            break
        else:
            print("Waiting for the correct input ('completed')...")
            
# Run the event-driven flow
asyncio.run(main())
