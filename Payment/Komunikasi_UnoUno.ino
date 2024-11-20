#include <RH_ASK.h>
#include <SoftwareSerial.h> 
RH_ASK driver;  // RF driver (pin 12 TX, pin 11 RX)

void setup() {
    Serial.begin(9600);  // Inisiasi Serial untuk komunikasi UART
}

void loop() {
    // Menerima data dari phyton berupa total harga
    if (Serial.available() > 0) {
        String data = Serial.readString();  // Membaca data total harga via komunikasi serial

        // Mengirim data melalui RF
        const char *msg = data.c_str();  // Konversi String to char*
        driver.send((uint8_t *)msg, strlen(msg));  // Mengirim data
        driver.waitPacketSent();  
    }

    // Menerima hasil komparasi input user dan total harga dari user via uart
    if (Serial.available()>0){
      String uno = Serial.readString(); 
      Serial.println(uno); // Mengirim data untuk update data server
    }
    delay(1000);  // Delay for 1 second before checking again
}