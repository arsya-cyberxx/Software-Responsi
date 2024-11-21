#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>

// Konfigurasi WiFi dan MQTT
const char* ssid = "Samsul";
const char* password = "13051983";
const char* mqtt_server = "192.168.124.170";

WiFiClient espClient;
PubSubClient client(espClient);

// Konfigurasi I2C
#define PSOC_ADDRESS 0x08
char dataToSend[100] = "";  // Buffer untuk data yang akan dikirim ke PSoC
char receivedData[50];      // Buffer untuk data yang diterima dari PSoC
bool sendDataToPsoc = false;  // Flag untuk mengontrol pengiriman data ke PSoC
bool dataSentToMqtt = false;  // Flag untuk mengontrol pengiriman ke MQTT

// Fungsi setup WiFi
void setup_wifi() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    Serial.print("Connecting to WiFi...");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
}

// Callback ketika menerima pesan MQTT
void callback(char* topic, byte* message, unsigned int length) {
    Serial.print("Message arrived on topic: ");
    Serial.print(topic);
    Serial.print(". Message: ");
    
    String messageTemp = "";
    for (int i = 0; i < length; i++) {
        messageTemp += (char)message[i];
    }

    // Print JSON asli
    Serial.println("Original JSON message: ");
    Serial.println(messageTemp);

    // Parse JSON
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, messageTemp);

    if (error) {
        Serial.print("Failed to parse JSON: ");
        Serial.println(error.f_str());
        return;
    }

    // Ekstrak data dari JSON
    JsonArray product_ID = doc["product_ID"];
    JsonArray product_stock = doc["product_stock"];
    int user_age = doc["user_age"];

    // Konversi data ke format string
    String output = "";
    for (int i = 0; i < product_ID.size(); i++) {
        output += product_ID[i].as<String>();
        if (i < product_ID.size() - 1) output += ",";
    }
    output += ",";

    for (int i = 0; i < product_stock.size(); i++) {
        output += String(product_stock[i].as<int>());
        if (i < product_stock.size() - 1) output += ",";
    }
    output += "," + String(user_age);

    // Tampilkan hasil konversi
    Serial.println("Formatted String: ");
    Serial.println(output);

    // Simpan hasil konversi ke buffer untuk dikirim via I2C
    strncpy(dataToSend, output.c_str(), sizeof(dataToSend));
    dataToSend[sizeof(dataToSend) - 1] = '\0';  // Pastikan null-terminated

    // Set flag untuk mengirim data ke PSoC dan reset flag untuk pengiriman ke MQTT
    sendDataToPsoc = true;
    dataSentToMqtt = false;
}

// Fungsi reconnect ke MQTT
void reconnect() {
    while (!client.connected()) {
        Serial.print("Attempting MQTT connection...");
        if (client.connect("ESP32PublisherSubscriber")) {
            Serial.println("Connected to MQTT");
            client.subscribe("esp32/kirim"); // Subscribe ke topic untuk menerima data
        } else {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println(" try again in 5 seconds");
            delay(5000);
        }
    }
}

// Fungsi membaca data dari PSoC melalui I2C
String readFromPsoc() {
    String psocData = "";

    Wire.requestFrom(PSOC_ADDRESS, sizeof(receivedData)); // Meminta data dari PSoC
    for (int i = 0; i < sizeof(receivedData); i++) {
        if (Wire.available()) {
            receivedData[i] = Wire.read();
        } else {
            receivedData[i] = '\0'; // Isi dengan null jika tidak ada data
            break; // Hentikan loop jika tidak ada data lagi
        }
    }

    psocData = String(receivedData); // Konversi buffer ke string
    Serial.print("Data diterima dari PSoC: ");
    Serial.println(psocData);
    return psocData;
}

bool validateData(String data) {
    // Pastikan data tidak kosong
    if (data.length() == 0) {
        return false;
    }

    // Pastikan data hanya berisi karakter yang valid (A-Z, a-z, 0-9, ',', ';')
    for (char c : data) {
        if (!isalnum(c) && c != ',' && c != ';' && c != '\0') {
            return false;
        }
    }

    // Data valid
    return true;
}


void setup() {
    // Setup Serial
    Serial.begin(115200);

    // Setup WiFi dan MQTT
    setup_wifi();
    client.setServer(mqtt_server, 1890);
    client.setCallback(callback);

    // Setup I2C
    Wire.begin(21, 22, 100000);  // SDA = GPIO21, SCL = GPIO22
    Serial.println("ESP32 I2C and MQTT Initialized.");
}

void loop() {
    // MQTT loop
    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    // Periksa apakah ada data yang siap dikirim ke PSoC
    if (sendDataToPsoc) {
        // Kirim string data ke PSoC melalui I2C
        Wire.beginTransmission(PSOC_ADDRESS);
        Wire.write((const uint8_t*)dataToSend, strlen(dataToSend));  // Kirim dataToSend
        Wire.endTransmission();

        // Tampilkan data yang dikirim
        Serial.print("Data yang dikirim ke PSoC: ");
        Serial.println(dataToSend);

        // Reset flag setelah data dikirim
        sendDataToPsoc = false;
    }

    // Periksa apakah data telah dikirim ke MQTT dan tidak perlu dikirim lagi
    if (!dataSentToMqtt) {
        // Meminta data string dari PSoC berkali-kali hingga data diterima
        String psocData = readFromPsoc();
        // Validasi data sebelum mengirim ke MQTT
        if (validateData(psocData)) {
            // Kirim data ke topic MQTT hanya jika valid
            client.publish("esp32/terima", psocData.c_str());
            Serial.print("Data dikirim ke topic MQTT esp32/terima: ");
            Serial.println(psocData);

            // Set flag untuk mencegah pengiriman ulang ke MQTT
            dataSentToMqtt = true;
        } else {
            Serial.println("Data dari PSoC tidak valid. Tidak dikirim ke MQTT.");
        }
    }
}
