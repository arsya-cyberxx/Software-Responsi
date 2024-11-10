import csv
import serial
import pandas as pd
import time

def comserial(com_port, baud_rate=9600):
    ser = serial.Serial(port=com_port,
                        baudrate=baud_rate,  
                        parity=serial.PARITY_ODD,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        timeout=3)
    return ser

def send_stock(file_path, ser):
    df = pd.read_csv(file_path)
    last_value_cart = df['cart'][df['cart'].notna()].iloc[-1] 
    ser.write(last_value_cart.encode())

if __name__ == "__main__":
    file_path = 'okedeh.csv'
    com_port = 'COM3'
    baud_rate = 9600

    ser = comserial(com_port, baud_rate)
    
    try:
        send_stock(file_path, ser)  
    except KeyboardInterrupt:
        print("Process interrupted. Closing COM port.")
    finally:
        ser.close()
