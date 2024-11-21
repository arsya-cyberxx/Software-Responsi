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
const int PSoC_I2C_ADDRESS = 0x08;  // Alamat I2C PSoC
unsigned long lastPingTime = 0;     // Waktu terakhir ping

// Variabel untuk timer
unsigned long timerStartTime = 0; // Waktu mulai timer
bool reminderTriggered = false;  // Status apakah reminder sudah menyala
bool passwordChangeRequired = false; // Status apakah perlu ganti password

// State untuk State Machine
enum State {
    STATE_INPUT_ID,
    STATE_SEND_ID,
    STATE_INPUT_PASSWORD,
    STATE_SEND_PASSWORD,
    STATE_PASSWORD_TIMER,
    STATE_RESET
};
State currentState = STATE_INPUT_ID;

// Deklarasi fungsi
void requestUserID(String &user_ID);
void requestUserPassword(String &user_password);
bool validateID(const String &user_ID);
bool validatePassword(const String &user_password);
void sendIDRequest(const String& user_ID);
void sendPasswordRequest(const String& user_password);
void handleMessage(WebsocketsMessage message);
void sendStatusToPSoC(uint8_t status);

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

    // Kirim ping untuk menjaga koneksi WebSocket tetap aktif
    if (millis() - lastPingTime > 30000) {
        client.ping();
        lastPingTime = millis();
        Serial.println("Ping dikirim untuk menjaga koneksi WebSocket aktif.");
    }

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
        case STATE_PASSWORD_TIMER:
            handlePasswordTimer();
            break;
        case STATE_RESET:
            handleReset();
            break;
    }

    delay(100);  // Stabilitas loop
}

void handleInputID() {
    Serial.println("Menunggu input ID...");
    String userID;
    requestUserID(userID);
    if (validateID(userID)) {
        sendIDRequest(userID);
        currentState = STATE_SEND_ID;
    } else {
        Serial.println("ID tidak valid, coba lagi...");
    }
}

void handleSendID() {
    Serial.println("ID dikirim ke server.");
    // Transisi akan diatur oleh handleMessage saat respons diterima dari server
}

void handleInputPassword() {
    Serial.println("Menunggu input password...");
    String userPassword;
    requestUserPassword(userPassword);
    if (validatePassword(userPassword)) {
        sendPasswordRequest(userPassword);
        timerStartTime = millis(); // Mulai timer untuk 1,5 menit
        reminderTriggered = false; // Reset reminder
        passwordChangeRequired = false; // Reset password ganti
        Serial.println("Timer 1,5 menit dimulai!");
        currentState = STATE_PASSWORD_TIMER;
    } else {
        Serial.println("Password tidak valid, coba lagi...");
    }
}

void handleSendPassword() {
    Serial.println("Password dikirim ke server.");
    // Transisi akan diatur oleh handleMessage saat respons diterima dari server
}

void handlePasswordTimer() {
    unsigned long elapsedTime = millis() - timerStartTime;
    if (!reminderTriggered && elapsedTime >= 90000) {
        reminderTriggered = true;
        sendStatusToPSoC(0x04); // Nyalakan LED_Ganti_Password
        Serial.println("Reminder: LED_Ganti_Password menyala.");
        timerStartTime = millis(); // Reset untuk timer 30 detik
    } else if (reminderTriggered && elapsedTime >= 30000) {
        passwordChangeRequired = true; // Tandai bahwa ganti password diperlukan
        sendStatusToPSoC(0x00); // Matikan LED_Ganti_Password
        Serial.println("LED_Ganti_Password mati. Sistem terkunci, ganti password diperlukan.");
        currentState = STATE_RESET;
    }
}

void handleReset() {
    Serial.println("Sistem di-reset untuk menerima ID baru.");
    reminderTriggered = false;
    passwordChangeRequired = false;
    currentState = STATE_INPUT_ID;
}

void handleMessage(WebsocketsMessage message) {
    Serial.print("Pesan dari server: ");
    Serial.println(message.data());

    StaticJsonDocument<200> doc;
    if (deserializeJson(doc, message.data()) == DeserializationError::Ok) {
        const char* login_status = doc["login_status"];
        const char* messageText = doc["message"];

        if (strcmp(login_status, "id_valid") == 0) {
            sendStatusToPSoC(0x01);  // Kirim sinyal ID valid ke PSoC
            Serial.println("ID valid.");
            currentState = STATE_INPUT_PASSWORD; // Lanjut ke input password
        } else if (strcmp(login_status, "success") == 0) {
            sendStatusToPSoC(0x03);  // Kirim sinyal login berhasil ke PSoC
            Serial.println("Login berhasil.");
            currentState = STATE_INPUT_ID;  // Reset ke awal
        } else if (strcmp(login_status, "failed") == 0 && strcmp(messageText, "ID not found") == 0) {
            sendStatusToPSoC(0x02);  // Kirim sinyal ID salah ke PSoC
            Serial.println("ID tidak valid. Silakan input ulang.");
            currentState = STATE_INPUT_ID; // Ulang input ID
        } else if (strcmp(login_status, "failed") == 0 && strstr(messageText, "Password incorrect") != NULL) {
            sendStatusToPSoC(0x02);  // Kirim sinyal password salah ke PSoC
            Serial.println("Password salah. Silakan input ulang.");
            currentState = STATE_INPUT_PASSWORD; // Ulang input password
        }
    } else {
        Serial.println("Error: Parsing JSON gagal.");
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
    if (user_ID.length() != 3) return false;
    for (size_t i = 0; i < user_ID.length(); i++) {
        if (!isalnum(user_ID[i])) return false;
    }
    return true;
}

bool validatePassword(const String &user_password) {
    if (user_password.length() != 4) return false;
    for (size_t i = 0; i < user_password.length(); i++) {
        if (!isalnum(user_password[i])) return false;
    }
    return true;
}

void sendIDRequest(const String& user_ID) {
    StaticJsonDocument<200> doc;
    doc["user_IDinput"] = user_ID;
    String jsonData;
    serializeJson(doc, jsonData);
    client.send(jsonData);
    Serial.println("ID dikirim ke server.");
}

void sendPasswordRequest(const String& user_password) {
    StaticJsonDocument<200> doc;
    doc["user_password"] = user_password;
    String jsonData;
    serializeJson(doc, jsonData);
    client.send(jsonData);
    Serial.println("Password dikirim ke server.");
}

void sendStatusToPSoC(uint8_t status) {
    Wire.beginTransmission(PSoC_I2C_ADDRESS);
    Wire.write(status);
    Wire.endTransmission();
}
