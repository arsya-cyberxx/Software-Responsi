#include <RH_ASK.h>
#include <SoftwareSerial.h>

SoftwareSerial psoc(2,3);  // Define Pin serial UART antara PSoC dan Arduino Receiver
RH_ASK driver;  // RF driver (pin 12 TX, pin 11 RX)

void setup() {
  Serial.begin(9600);  // Inisiasi UART antar Arduino
  psoc.begin(9600); // Inisiasi UART antar Arduino receiver dan PSoC
}

void loop() {
  uint8_t buf[100]; // Buffer untuk menerima data
  uint8_t buflen = sizeof(buf);       // Size dari buffer

  // Memeriksa ukuran data yang diterim
  if (Serial.available() > 0) {
      String receivedData = Serial.readString(); // Membaca data sampai newline
      Serial.println(receivedData); // Menampilkan data di Serial Monitor
      psoc.write(receivedData.c_str()); // Mengirim data ke PSoC
  }

  // Menerima data komparasi dari PSoC ke arduino receiver dengan UART
  if (psoc.available()>0) {
    String data_succes = "Payment Success"; // String penanda payment berhasil
    String data_gagal = "Payment Failed"; // String penanda payment gagal
    String data_psoc = psoc.readString();
    if (data_psoc == data_succes){
      Serial.println("Sukses"); // String untuk mengupdate stock
    }
    if (data_psoc == data_gagal) {
      Serial.println("Gagal"); //String untuk mengupdate login status dan mengeksekusi fungsi security
    }
  }
}
