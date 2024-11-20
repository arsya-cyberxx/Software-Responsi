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
    last_value_cart=last_value_cart.split(",")
    totalharga=0
    for i in range(0, len(last_value_cart), 2):
        if last_value_cart[i]=='A':
            totalharga+=1*int(last_value_cart[i+1])
        elif last_value_cart[i]=='B':
            totalharga+=2*int(last_value_cart[i+1])
        elif last_value_cart[i]=='C':
            totalharga+=3*int(last_value_cart[i+1])
        elif last_value_cart[i]=='D':
            totalharga+=4*int(last_value_cart[i+1])
    totalharga=str(totalharga)
    if len(totalharga)!=3:
        totalharga='0'*(3-len(totalharga))+totalharga
    
    # binerharga=[]
    # for i in totalharga:
    #     biner = format(int(i), '004b')
    #     binerharga.append(biner)
    # binerharga=''.join(binerharga)
    ser.write(totalharga.encode())
    return totalharga

if __name__ == "__main__":
    file_path = 'okedeh.csv'
    com_port = 'COM3'
    baud_rate = 9600
    
    try:
        ser=comserial(com_port, baud_rate)
        print(send_stock(file_path, ser)) 
    except KeyboardInterrupt:
        print("Process interrupted. Closing COM port.")
