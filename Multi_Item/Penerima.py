#import context  # Ensures paho is in PYTHONPATH
import pandas as pd
import csv
import json
import paho.mqtt.client as mqtt

def menerima(file_path):
    def on_connect(mqttc, obj, flags, reason_code, properties):
        print(str(reason_code))

    def on_message(mqttc, obj, msg):
        df = pd.read_csv(file_path)
        data_json = msg.payload.decode("utf-8")
        print(data_json)
        if 'cart' not in df.columns:
            df['cart'] = ''
        if df['cart'].isnull().all() or (df['cart'] == '').all():
            df.at[0, 'cart'] = data_json
        else:
            new_row = pd.DataFrame({'cart': [data_json]})
            df = pd.concat([df, new_row], ignore_index=True)
        #df['cart'] = df['cart'].astype(str) + data_json + ';'
        df.to_csv(file_path, index=False)

    def on_subscribe(mqttc, obj, mid, reason_code_list, properties):
        print(str(reason_code_list))

    def on_log(mqttc, obj, level, string):
        print(string)

    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe
    mqttc.connect("192.168.4.170", 1890, 60)
    mqttc.subscribe("esp32/terima")

    mqttc.loop_forever()
