import asyncio
from Loyalty.Loyalti import Loyalti
from Multi_Item import Pengirim, Penerima
import pandas as pd
import os

df = pd.read_csv("okedeh.csv")

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

# Listener for the "completed" event
def multiitemmengirim(file_path):
    Pengirim.mengirim(file_path)
    return "multiitem menerima"

def multiitemmenerima(file_path):
    data_json=Penerima.menerima(file_path)
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=['cart'])
    else:
        df = pd.read_csv(file_path)

    # Check if 'cart' column exists and is empty; if so, add the new message in a new row
    if 'cart' not in df.columns:
        df['cart'] = ''

    # Append the new message as a new row
    new_row = pd.DataFrame({'cart': [data_json]})
    df = pd.concat([df, new_row], ignore_index=True)

    # Save updated DataFrame back to CSV
    df.to_csv(file_path, index=False)
    print("Data saved to CSV.")

    # Disconnect the client after the first message is received and processed
    print("Message received and CSV updated. Disconnecting...")
    return "loyalti"

async def loyalti():
    loyalti_app = Loyalti()
    loyalti_app.app.run(host='0.0.0.0', port=5000, debug=True)
    return "payment"

# Instantiate EventEmitter and register the listener
event_emitter = EventEmitter()
event_emitter.on("multiitem mengirim", multiitemmengirim)
event_emitter.on("multiitem menerima", multiitemmengirim)
event_emitter.on("loyalti", loyalti)

# Continuously wait for "completed" input in main
async def main():
    user_input = "start"
    while True:
        if user_input == "start":
            user_input = multiitemmengirim('okedeh.csv')
        elif user_input == "multiitem menerima":
            user_input= multiitemmenerima('okedeh.csv')
        elif user_input == "loyalti":
            user_input= await event_emitter.emit("loyalti")
            break
        else:
            print("Waiting for the correct input ('completed')...")
            
# Run the event-driven flow
asyncio.run(main())
