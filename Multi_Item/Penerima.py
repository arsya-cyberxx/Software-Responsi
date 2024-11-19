import pandas as pd
import paho.mqtt.client as mqtt
import os

def menerima(file_path):
    # MQTT connection callback
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected successfully")
            client.subscribe("esp32/terima")
        else:
            print(f"Connection failed with code {rc}")

    # MQTT message callback
    def on_message(client, userdata, msg):
        # Read the CSV file into a DataFrame, creating if it doesn't exist
        data_json = msg.payload.decode("utf-8")
        client.disconnect()
        return data_json

    # MQTT log callback for debugging
    def on_log(client, userdata, level, buf):
        print(f"Log: {buf}")

    # Set up MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_log = on_log

    try:
        client.connect("192.168.4.170", 1890, 60)
        client.loop_forever()  # Blocks the main thread, handling reconnections if necessary
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

# Usage
menerima('output.csv')