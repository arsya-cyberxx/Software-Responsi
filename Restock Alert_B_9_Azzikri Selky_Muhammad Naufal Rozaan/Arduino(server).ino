#include <SoftwareSerial.h>
#include <RH_ASK.h>

// Inisialisasi SoftwareSerial
SoftwareSerial arduino2(5, 6); // RX, TX ke Arduino 2

// Inisialisasi RF433 (RadioHead)
RH_ASK driver;

void setup() {
    // Inisialisasi Serial Monitor dan SoftwareSerial
    Serial.begin(9600);       // Untuk komunikasi dengan Python
    arduino2.begin(9600);     // Untuk komunikasi dengan Arduino lain

    // Inisialisasi RF433
    if (!driver.init()) {
        Serial.println("RF433 Gagal Inisialisasi");
    }
}

void loop() {
    // *** Menerima data dari Python dan mengirimkan ke Arduino lain ***
    if (Serial.available() > 0) {
        // Baca data dari Python
        String dataFromPython = Serial.readStringUntil('\n');
        
        // Kirim data ke Arduino lain melalui SoftwareSerial
        arduino2.println(dataFromPython);

        // Debug: Tampilkan data yang diterima dari Python
        Serial.println(dataFromPython);
    }

    // *** Menerima data dari RF433 dan mengirimkan ke Python ***
    uint8_t buf[RH_ASK_MAX_MESSAGE_LEN];
    uint8_t buflen = sizeof(buf);

    if (driver.recv(buf, &buflen)) {
        buf[buflen] = '\0'; // Mengakhiri buffer sebagai string
        String receivedData = String((char*)buf);
        
        // Validasi: Hanya teruskan jika data hanya mengandung angka
        if (isNumeric(receivedData)) {
            // Kirim data ke Python melalui Serial
            Serial.println(receivedData);

            // Debug: Tampilkan data yang diterima dari RF433
            Serial.println(receivedData);
        } else {
            // Debug: Data diabaikan
        }
    }

    delay(0); // Hindari loop terlalu cepat
}

// Fungsi untuk mengecek apakah string hanya mengandung angka
bool isNumeric(String str) {
    for (unsigned int i = 0; i < str.length(); i++) {
        if (!isdigit(str[i])) {
            return false;
        }
    }
    return true;
}
