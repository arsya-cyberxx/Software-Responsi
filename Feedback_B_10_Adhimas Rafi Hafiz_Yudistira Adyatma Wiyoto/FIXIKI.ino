#include <Arduino.h>
#include <SPI.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <ArduinoJson.h>

#define SERVICE_UUID "84c4e7af-b494-461b-8c55-125f88183792"
#define CHARACTERISTIC_UUID "84c4e7af-b494-461b-8c55-125f88183792"

static const int spiClk = 1000000; // SPI clock speed
SPIClass *hspi = NULL;
#define HSPI_CS 18 // CS pin

BLECharacteristic *pCharacteristic;
bool deviceConnected = false;
String spi_response = "";

// Function declarations
String jsonToString(const String &json);
String addSPIResponseToString(const String &ble_data, const String &spi_data);
String stringToJson(const String &data);
void send_SPI_data(const String &data);
String extractSPIResponse(const String &data);

// BLE Server Callbacks
class MyServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) { deviceConnected = true; }
    void onDisconnect(BLEServer* pServer) { deviceConnected = false; }
};

// BLE Characteristic Callbacks
class MyCharacteristicCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* pCharacteristic) {
        String value = pCharacteristic->getValue().c_str();
        if (value.length() > 0) {
            Serial.println("Received JSON from BLE client:");
            Serial.println(value);

            // Convert JSON to string
            String spi_data = jsonToString(value);
            if (spi_data.length() > 0) {
                // Send string to PSoC via SPI
                send_SPI_data(spi_data);

                // Filter PSoC response
                String filtered_response = extractSPIResponse(spi_response);

                // Add PSoC response to BLE data
                String combined_data = addSPIResponseToString(spi_data, filtered_response);

                // Convert the updated string back to JSON
                String json_response = stringToJson(combined_data);

                // Send updated JSON back to BLE client
                if (deviceConnected) {
                    pCharacteristic->setValue(json_response.c_str());
                    pCharacteristic->notify();
                }
            }
        }
    }
};

void setup() {
    Serial.begin(115200);

    // Initialize BLE
    BLEDevice::init("ESP32_Server");
    BLEServer *pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    BLEService *pService = pServer->createService(SERVICE_UUID);
    pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_NOTIFY
    );
    pCharacteristic->addDescriptor(new BLE2902());
    pCharacteristic->setCallbacks(new MyCharacteristicCallbacks());
    pService->start();

    BLEAdvertising *pAdvertising = pServer->getAdvertising();
    pAdvertising->start();

    // Initialize SPI
    hspi = new SPIClass(HSPI);
    hspi->begin(14, 12, 13, HSPI_CS); // SCK=14, MISO=12, MOSI=13, CS=15
    pinMode(HSPI_CS, OUTPUT);
    digitalWrite(HSPI_CS, HIGH);

    Serial.println("ESP32 BLE Server ready.");
}

void loop() {
    // Optional delay or BLE functionality
}

// Convert JSON string to SPI-compatible string
String jsonToString(const String &json) {
    StaticJsonDocument<1024> doc;
    DeserializationError error = deserializeJson(doc, json);
    if (error) {
        Serial.println("Failed to parse JSON");
        return "";
    }

    String result = "";
    result += doc["user_ID"].as<String>() + ",";
    result += (doc["user_voucherEligible"] ? "1," : "0,");

    JsonObject cart = doc["cart"];
    for (const char* key : {"Product A", "Product B", "Product C", "Product D"}) {
        if (cart.containsKey(key)) {
            int ratingTotal = cart[key]["rating_total"].as<int>();
            int ratingFrequency = cart[key]["rating_frequency"].as<int>();
            result += String(ratingTotal) + ",";
            result += String(ratingFrequency) + ",";
        } else {
            result += "00,00,"; // Default value for missing products
        }
    }

    JsonObject restock = doc["restock_frequency"];
    for (const char* key : {"A", "B", "C", "D"}) {
        if (restock.containsKey(key)) {
            int restockFreq = restock[key].as<int>();
            result += String(restockFreq) + ",";
        } else {
            result += "00,"; // Default value for missing restock frequency
        }
    }

    if (result.endsWith(",")) result.remove(result.length() - 1);
    return result;
}

// Add PSoC SPI response to BLE data string
String addSPIResponseToString(const String &ble_data, const String &spi_data) {
    String result = ble_data;
    String psoc_data = spi_data;
    psoc_data.trim(); // Remove extra spaces or line breaks

    // Parse and combine data
    int voucher = psoc_data.substring(0, psoc_data.indexOf(',')).toInt();
    psoc_data.remove(0, psoc_data.indexOf(',') + 1);

    result.replace(",1,", "," + String(voucher) + ","); // Replace voucherEligible with voucher

    String ble_parts[12];
    String psoc_parts[5];
    int idx = 0;

    // Parse BLE cart
    for (int i = 0; i < result.length() && idx < 12; i = result.indexOf(',', i) + 1) {
        ble_parts[idx++] = result.substring(i, result.indexOf(',', i + 1));
    }

    // Parse PSoC cart
    idx = 0;
    for (int i = 0; i < psoc_data.length() && idx < 5; i = psoc_data.indexOf(',', i) + 1) {
        psoc_parts[idx++] = psoc_data.substring(i, psoc_data.indexOf(',', i + 1));
    }

    // Update ratings with PSoC data
    for (int i = 0; i < 4; i++) {
        int rating_total = ble_parts[i * 2].toInt() + psoc_parts[i].toInt();
        int rating_freq = ble_parts[i * 2 + 1].toInt() + 1;
        ble_parts[i * 2] = String(rating_total);
        ble_parts[i * 2 + 1] = String(rating_freq);
    }

    result = String(ble_parts[0]);
    for (int i = 1; i < 12; i++) {
        result += "," + ble_parts[i];
    }
    return result;
}

// Convert updated string back to JSON
String stringToJson(const String &data) {
    StaticJsonDocument<1024> doc;

    int idx = 0;
    String parts[13];
    for (int i = 0; i < data.length() && idx < 13; i = data.indexOf(',', i) + 1) {
        parts[idx++] = data.substring(i, data.indexOf(',', i + 1));
    }

    doc["user_ID"] = parts[0];
    doc["user_voucher"] = parts[1].toInt();

    JsonObject cart = doc.createNestedObject("cart");
    const char* products[] = {"Product A", "Product B", "Product C", "Product D"};
    for (int i = 0; i < 4; i++) {
        JsonObject product = cart.createNestedObject(products[i]);
        product["rating_total"] = parts[i * 2 + 2].toInt();
        product["rating_frequency"] = parts[i * 2 + 3].toInt();
    }

    String json;
    serializeJson(doc, json);
    return json;
}

// Extract filtered SPI response
String extractSPIResponse(const String &data) {
    if (data.length() > 30) {
        return data.substring(1, 31); // Extract data from index 1 to 30
    } else if (data.length() > 1) {
        return data.substring(1); // Extract from index 1 to the end
    } else {
        return ""; // If data is too short
    }
}

// Send data to PSoC via SPI
void send_SPI_data(const String &data) {
    uint8_t spi_tx_buf[data.length() + 1];
    data.getBytes(spi_tx_buf, data.length() + 1);

    hspi->beginTransaction(SPISettings(spiClk, MSBFIRST, SPI_MODE0));
    digitalWrite(HSPI_CS, LOW);

    for (size_t i = 0; i < data.length(); i++) {
        hspi->transfer(spi_tx_buf[i]);
        delay(10);
    }
    hspi->transfer('\0'); // Null terminator

    // Wait for response
    delay(100);
    spi_response = "";
    for (size_t i = 0; i < 128; i++) {
        char received = hspi->transfer(0x00);
        if (received == '\0') break;
        spi_response += received;
    }

    digitalWrite(HSPI_CS, HIGH);
    hspi->endTransaction();

    Serial.print("Received SPI response: ");
    Serial.println(spi_response);
}
