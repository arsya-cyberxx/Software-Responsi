#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include <Wire.h>
#include <ArduinoJson.h>

using namespace websockets;

// Konfigurasi WiFi dan WebSocket
const char* ssid = "BillyGanteng";
const char* wifi_password = "akuganteng";
const char* websockets_server_host = "ws://192.168.112.200:5000";

WebsocketsClient client;
const int PSoC_I2C_ADDRESS = 0x08;

// State untuk State Machine
enum State {
    STATE_INPUT_ID,
    STATE_SEND_ID,
    STATE_INPUT_PASSWORD,
    STATE_SEND_PASSWORD
};
State currentState = STATE_INPUT_ID;  // Mulai dari input ID

// Variabel global
String currentID = "";
String currentPassword = "";
bool idValidated = false;  // Menandakan apakah ID sudah valid

void setup() {
    Serial.begin(115200);
    Wire.begin();  // Inisialisasi I2C sebagai master

    // Koneksi ke WiFi
    WiFi.begin(ssid, wifi_password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nTerhubung ke WiFi");

    // Koneksi ke WebSocket Server
    client.onMessage(handleMessage);
    if (client.connect(websockets_server_host)) {
        Serial.println("Terhubung ke server WebSocket");
    } else {
        Serial.println("Gagal terhubung ke server WebSocket");
    }
}

void loop() {
    client.poll();  // Periksa pesan yang masuk dari server

    switch (currentState) {
        case STATE_INPUT_ID:
            handleInputID();
            break;
        case STATE_SEND_ID:
            handleSendID();
            break;
        case STATE_INPUT_PASSWORD:
            handleInputPassword();
            break;
        case STATE_SEND_PASSWORD:
            handleSendPassword();
            break;
    }

    delay(100);  // Stabilisasi loop
}

void handleInputID() {
    Serial.println("Menunggu input ID...");
    String userID;
    requestUserID(userID);
    if (validateID(userID)) {
        currentID = userID;  // Simpan ID
        currentState = STATE_SEND_ID;
    } else {
        Serial.println("ID tidak valid, coba lagi...");
    }
}

void handleSendID() {
    sendIDRequest(currentID);
    Serial.println("ID dikirim ke server.");
}

void handleInputPassword() {
    Serial.println("Menunggu input password...");
    String userPassword;
    requestUserPassword(userPassword);
    if (validatePassword(userPassword)) {
        currentPassword = userPassword;  // Simpan password
        currentState = STATE_SEND_PASSWORD;
    } else {
        Serial.println("Password tidak valid, coba lagi...");
    }
}

void handleSendPassword() {
    sendPasswordRequest(currentPassword);
    Serial.println("Password dikirim ke server.");
}

void handleMessage(WebsocketsMessage message) {
    Serial.print("Pesan dari server: ");
    Serial.println(message.data());

    StaticJsonDocument<200> doc;
    if (deserializeJson(doc, message.data()) == DeserializationError::Ok) {
        const char* login_status = doc["login_status"];
        const char* messageText = doc["message"];

        if (strcmp(login_status, "id_valid") == 0) {
            idValidated = true;
            Serial.println("ID valid, lanjut ke input password.");
            currentState = STATE_INPUT_PASSWORD;
        } else if (strcmp(login_status, "success") == 0) {
            Serial.println("Login berhasil!");
            idValidated = false;
            currentState = STATE_INPUT_ID;  // Reset ke awal
        } else if (strcmp(login_status, "failed") == 0 && strcmp(messageText, "ID not found") == 0) {
            Serial.println("ID tidak valid, ulangi input ID.");
            currentState = STATE_INPUT_ID;
        } else if (strcmp(login_status, "failed") == 0 && strstr(messageText, "Password incorrect") != NULL) {
            Serial.println("Password salah, ulangi input password.");
            currentState = STATE_INPUT_PASSWORD;
        }
    }
}

void requestUserID(String &user_ID) {
    Wire.requestFrom(PSoC_I2C_ADDRESS, 3);
    char idBuffer[4] = {0};
    for (int i = 0; i < 3; i++) {
        if (Wire.available()) {
            idBuffer[i] = Wire.read();
        }
    }
    user_ID = String(idBuffer);
    user_ID.trim();
    Serial.print("ID diterima: ");
    Serial.println(user_ID);
}

void requestUserPassword(String &user_password) {
    Wire.requestFrom(PSoC_I2C_ADDRESS, 4);
    char passwordBuffer[5] = {0};
    for (int i = 0; i < 4; i++) {
        if (Wire.available()) {
            passwordBuffer[i] = Wire.read();
        }
    }
    user_password = String(passwordBuffer);
    user_password.trim();
    Serial.print("Password diterima: ");
    Serial.println(user_password);
}

bool validateID(const String &user_ID) {
    if (user_ID.length() != 3) return false;  // Panjang harus 3
    for (size_t i = 0; i < user_ID.length(); i++) {
        if (!isalnum(user_ID[i])) return false;  // Periksa apakah alfanumerik
    }
    return true;  // Semua karakter valid
}

bool validatePassword(const String &user_password) {
    if (user_password.length() != 4) return false;  // Panjang harus 4
    for (size_t i = 0; i < user_password.length(); i++) {
        if (!isalnum(user_password[i])) return false;  // Periksa apakah alfanumerik
    }
    return true;  // Semua karakter valid
}


void sendIDRequest(const String& user_ID) {
    StaticJsonDocument<200> doc;
    doc["user_IDinput"] = user_ID;
    String jsonData;
    serializeJson(doc, jsonData);
    client.send(jsonData);
}

void sendPasswordRequest(const String& user_password) {
    StaticJsonDocument<200> doc;
    doc["user_password"] = user_password;
    String jsonData;
    serializeJson(doc, jsonData);
    client.send(jsonData);
}
