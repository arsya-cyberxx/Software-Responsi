#include <ArduinoJson.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define SERVICE_UUID "84c4e7af-b494-461b-8c55-125f88183792"
#define CHARACTERISTIC_UUID "84c4e7af-b494-461b-8c55-125f88183792"

BLECharacteristic *pCharacteristic;
bool deviceConnected = false;

// Variabel untuk menyimpan data dari JSON
String user_ID;
bool user_voucherEligible;
String cartProduct;
float cartPrice;
int cartQuantity;
int rating_total;
int rating_frequency;

// Additional variables based on code usage
int rating_inputted = 3;      // Example rating input from PSOC
int user_voucher = 12;        // Example voucher generated by PSOC
int login_status = 0;         // Status of login
String cart_status = "None";  // Status of the cart

class MyServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
    }
};

class MyCharacteristicCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* pCharacteristic) {
        String value = pCharacteristic->getValue().c_str(); // Convert received data to String
        if (value.length() > 0) {
            Serial.print("Received JSON Data: ");
            Serial.println(value);

            // Parsing JSON
            StaticJsonDocument<512> doc; 
            DeserializationError error = deserializeJson(doc, value);
            if (error) {
                Serial.print(F("Failed to parse JSON: "));
                Serial.println(error.f_str());
                return;
            }

            // Extract values from JSON
            user_ID = doc["user_ID"].as<String>();
            user_voucherEligible = doc["user_voucherEligible"];
            cartProduct = doc["cart"]["Product A"].as<String>();
            cartPrice = doc["cart"]["Product A"]["price"];
            cartQuantity = doc["cart"]["Product A"]["quantity"];
            rating_total = doc["rating_total"];
            rating_frequency = doc["rating_frequency"];

            // Display extracted values
            Serial.println("Parsed Data:");
            Serial.println("user_ID: " + user_ID);
            Serial.println("user_voucherEligible: " + String(user_voucherEligible));
            Serial.println("cartProduct: " + cartProduct);
            Serial.println("cartPrice: " + String(cartPrice));
            Serial.println("cartQuantity: " + String(cartQuantity));
            Serial.println("rating_total: " + String(rating_total));
            Serial.println("rating_frequency: " + String(rating_frequency));

            // Prepare JSON data to send back
            StaticJsonDocument<512> responseDoc;
            responseDoc["user_voucher"] = user_voucher;
            responseDoc["login_status"] = login_status;
            responseDoc["rating_total"] = rating_total + rating_inputted;
            responseDoc["rating_frequency"] = rating_frequency + 1;
            responseDoc["cart_status"] = cart_status;

            // Serialize the JSON response to a string
            String jsonResponse;
            serializeJson(responseDoc, jsonResponse);

            // Send JSON response back to the client
            pCharacteristic->setValue(jsonResponse.c_str());  // Set characteristic value
            Serial.println("Sending JSON Data to Client:");
            Serial.println(jsonResponse);
        }
    }
};

void setup() {
    Serial.begin(115200);
    BLEDevice::init("ESP32_Server");

    BLEServer *pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    BLEService *pService = pServer->createService(SERVICE_UUID);

    pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_READ // Set properties for write and read
    );

    pCharacteristic->setCallbacks(new MyCharacteristicCallbacks());
    pService->start();

    BLEAdvertising *pAdvertising = pServer->getAdvertising();
    pAdvertising->start();

    Serial.println("Waiting for a client connection...");
}

void loop() {
    delay(2000);
}
