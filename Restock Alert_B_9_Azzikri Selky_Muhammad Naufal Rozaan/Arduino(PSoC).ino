#include <RH_ASK.h>
#include <SoftwareSerial.h>

// Inisialisasi modul RF dan SoftwareSerial
RH_ASK driver;
SoftwareSerial Seriall(2, 3); // RX, TX untuk komunikasi dengan PSoC
SoftwareSerial Server(5, 6); // RX, TX untuk komunikasi dengan server
String receivedData = "";    // Buffer untuk data dari PSoC
String receivedData2 = "";   // Buffer untuk data dari server
void setup() {
    Serial.begin(9600);       // Debugging serial
    Seriall.begin(9600);      // Serial untuk komunikasi dengan PSoC
    Server.begin(9600);       // Serial untuk komunikasi dengan server

    if (!driver.init()) {     // Inisialisasi modul RF
        Serial.println("RF Init Gagal");
    } else {
        Serial.println("RF Init Berhasil");
    }
}

void loop() {
    // *1. Komunikasi dengan server*
    
    Server.listen(); // Aktifkan SoftwareSerial untuk server
    delay (599);
    while (Server.available() > 0) {
        char serialData2 = Server.read();
        if (serialData2 != '\n') {
            if (receivedData2.length() < 50) {
                receivedData2 += serialData2;
            }
        } else {
            if (receivedData2.length() > 0) { // Ganti isEmpty dengan length > 0
                Serial.println("Data diterima dari server: " + receivedData2);
                Seriall.listen(); // Beralih ke komunikasi PSoC
                Seriall.print("<" + receivedData2 + ">");
                Serial.println("Data dikirim ke PSoC: " + receivedData2);

                receivedData2 = ""; // Reset buffer
            }
        }
    }
      

    // *2. Komunikasi dengan PSoC*

    Seriall.listen(); // Aktifkan SoftwareSerial untuk PSoC
    delay (299);

    while (Seriall.available() > 0) {
        char serialData = Seriall.read();
        if (serialData != '\n') {
            if (receivedData.length() < 50) {
                receivedData += serialData;
            }
        } else {
            if (receivedData.length() > 0) { // Ganti isEmpty dengan length > 0
                Serial.println("Data diterima dari PSoC: " + receivedData);

                // Validasi dan kirim melalui RF
                if (receivedData.length() <= RH_ASK_MAX_MESSAGE_LEN) {
                    const char *msg = receivedData.c_str();
                    driver.send((uint8_t *)msg, strlen(msg));
                    driver.waitPacketSent();
                    Serial.println("Data terkirim melalui RF: " + receivedData);
                } else {
                    Serial.println("Error: Data terlalu panjang untuk RF");
                }


                receivedData = ""; // Reset buffer
            }
        }
    }
}
