import asyncio
import file1
import file2
import file3
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
async def security():
    print ( "login attempted has started")
    task1 = asyncio.create_task(file1.run())
    lenght, user_id= await task1
    df.loc [  lenght - 1  , 'user ID'] = user_id
    df.to_csv('okedeh.csv', index=False) 
    print("Login Completed")
    return "backend"

async def on_backend() :
    print ( "cart picking has started")
    task2 = asyncio.create_task(file2.run())
    newrow, cart = await task2
    await asyncio.sleep(1)
    df.loc [newrow - 1 , 'cart'] = cart
    df.to_csv('okedeh.csv', index=False) 


# Instantiate EventEmitter and register the listener
event_emitter = EventEmitter()
event_emitter.on("completed", security)
event_emitter.on("backend", on_backend)
# Continuously wait for "completed" input in main
async def main():
    user_input = "start"
    while True:
        if user_input == "start":
            user_input = await event_emitter.emit("completed")
        elif user_input == "backend":
            await event_emitter.emit("backend")
            break
        else:
            print("Waiting for the correct input ('completed')...")
            
# Run the event-driven flow
asyncio.run(main())
