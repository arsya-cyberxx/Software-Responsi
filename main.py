import asyncio
from Loyalty.Loyalti import Loyalti
from Multi_Item import Pengirim
import pandas as pd
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
async def multiitem(file_path):
    Pengirim.mengirim(file_path)
    return "loyalti"

async def loyalti():
    loyalti_app = Loyalti()
    loyalti_app.app.run(host='0.0.0.0', port=5000, debug=True)
    return "payment"

# Instantiate EventEmitter and register the listener
event_emitter = EventEmitter()
event_emitter.on("multiitem", multiitem)
event_emitter.on("loyalti", loyalti)

# Continuously wait for "completed" input in main
async def main():
    user_input = "start"
    while True:
        if user_input == "start":
            user_input = multiitem('okedeh.csv')
        elif user_input == "loyalti":
            user_input= await event_emitter.emit("loyalti")
            break
        else:
            print("Waiting for the correct input ('completed')...")
            
# Run the event-driven flow
asyncio.run(main())
