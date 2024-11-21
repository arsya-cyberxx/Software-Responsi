#include "project.h"
#include <string.h>  // Untuk fungsi memset dan strtok
#include <stdlib.h>  // Untuk konversi string ke integer
#include <stdio.h>   // Untuk fungsi snprintf
#include <stdbool.h>
#include "Stock.h"
#include "Umur.h"

#define BUFFER_SIZE 50
#define LIST_SIZE 10

char slaveBuffer[BUFFER_SIZE];
char masterBuffer[BUFFER_SIZE];
char list[LIST_SIZE][5];  // Array untuk menyimpan data yang sudah diproses
int list_index = 0;       // Index untuk list

void I2C_InitCustom(void) {
    I2C_Start();
    I2C_SlaveInitWriteBuf((unsigned char*)slaveBuffer, sizeof(slaveBuffer)); // Buffer tulis dari ESP32
    I2C_SlaveClearWriteStatus();
    I2C_SlaveInitReadBuf((unsigned char*)masterBuffer, sizeof(masterBuffer)); // Buffer baca untuk ESP32
    I2C_SlaveClearReadStatus();
}

void batasStock(uint8_t stok[]) {
    BatasA_Write(stok[0]);
    BatasB_Write(stok[1]);
    BatasC_Write(stok[2]);
    BatasD_Write(stok[3]);
}
void updateControlRegister(uint8_t stok[]) {
    uint8 controlValue = 0;
    if (stok[0] > 0) {
        controlValue |= 0x01; }
    if (stok[1] > 0) {
        controlValue |= 0x02; }
    if (stok[2] > 0) {
        controlValue |= 0x04; }
    if (stok[3] > 0) {
        controlValue |= 0x08; }
    Stock_Write(controlValue);
}
void aturanUmur(uint8_t umur) {
    uint8_t controlValue = 0;

    // Periksa apakah umur lebih dari 17
    if (umur > 17) {
        controlValue |= 0x01; // Mengatur bit jika umur lebih dari 17
    } else {
        controlValue = 0; // Jika umur kurang atau sama dengan 17, nilai diatur ke 0
    }

    // Menulis nilai kontrol ke register
    Umur_Write(controlValue);
}

void writeToControlRegisters(char* data) {
    char produk[4] = {0};  // Array untuk produk (maksimal 4 produk)
    uint8_t stok[4] = {0}; // Array untuk stok (maksimal 4 stok)
    uint8_t umur = 0;      // Variabel untuk usia

    // Memisahkan data berdasarkan delimiter ","
    char* token;
    token = strtok(data, ",");
    int index = 0;

    while (token != NULL) {
        if (index < 4) {
            // Produk (4 token pertama)
            produk[index] = token[0];  // Ambil karakter pertama dari token
        } else if (index < 8) {
            // Stok (4 token berikutnya)
            stok[index - 4] = (uint8_t)atoi(token);  // Konversi string ke integer
        } else {
            // Usia (token terakhir)
            umur = (uint8_t)atoi(token);
        }
        token = strtok(NULL, ",");  // Ambil token berikutnya
        index++;
    }
    
    aturanUmur(umur);
    updateControlRegister(stok);
    batasStock(stok);
}

void ProcessStatusRegisters(void) {
    // Membaca nilai dari status register
    uint8_t jumlah = KirimJumlah_Read() & 0x0F;
    uint8_t produk = KirimProduk_Read() & 0x0F;
    uint8_t sinyalKirim = SinyalKirim_Read(); // Membaca status register SinyalKirim

    // Debugging: Tampilkan nilai jumlah dan produk yang dibaca
    char statusStr[50];
    snprintf(statusStr, sizeof(statusStr), "Jumlah: %d, Produk: %02X", jumlah, produk);
    UART_1_PutString(statusStr);  // Kirim status register ke UART
    UART_1_PutString("\n");

    // Memastikan hanya mengambil data jika KirimJumlah != 0 dan KirimProduk != 0000
    if (jumlah != 0 && produk != 0b0000) {
        // Konversi jumlah ke desimal
        int jumlahDesimal = jumlah;

        // Konversi input biner produk ke karakter
        char produkChar;
        switch (produk) {
            case 0b0001: produkChar = 'A'; break;
            case 0b0010: produkChar = 'B'; break;
            case 0b0100: produkChar = 'C'; break;
            case 0b1000: produkChar = 'D'; break;
            default: produkChar = '?';  // Jika tidak sesuai, berikan simbol default
        }

        // Buat string hasil
        char result[5];
        snprintf(result, sizeof(result), "%c,%d", produkChar, jumlahDesimal);

        // Debugging: Tampilkan hasil yang diproses
        char resultStr[50];
        snprintf(resultStr, sizeof(resultStr), "Hasil: %s", result);
        UART_1_PutString(resultStr);  // Kirim hasil ke UART
        UART_1_PutString("\n");

        // Cek apakah hasil sudah ada dalam list
        int found = 0;
        for (int i = 0; i < list_index; i++) {
            if (strcmp(list[i], result) == 0) {
                found = 1;
                break;
            }
        }

        // Jika belum ada, tambahkan ke list
        if (!found && list_index < LIST_SIZE) {
            strcpy(list[list_index], result);
            list_index++;

            // Debugging: Tampilkan list setelah penambahan
            char listStr[100];
            snprintf(listStr, sizeof(listStr), "List Updated: ");
            for (int i = 0; i < list_index; i++) {
                strncat(listStr, list[i], sizeof(listStr) - strlen(listStr) - 1);
                if (i < list_index - 1) strncat(listStr, ", ", sizeof(listStr) - strlen(listStr) - 1);
            }
            UART_1_PutString(listStr);  // Kirim list yang telah diperbarui ke UART
            UART_1_PutString("\n");
        }
        int bufferIndex = 0;
         for (int i = 0; i < list_index; i++) {
            // Tambahkan data list ke masterBuffer
            int len = strlen(list[i]);
            if (bufferIndex + len < BUFFER_SIZE) {
                strcpy(&masterBuffer[bufferIndex], list[i]);
                bufferIndex += len;
                if (bufferIndex < BUFFER_SIZE - 1) {
                    masterBuffer[bufferIndex] = ','; 
                    bufferIndex++;
                }
            }        
        }
        // Kirim data via I2C
        if (sinyalKirim != 0){
            for (int retry = 0; retry < 10; retry++) {
                I2C_SlaveInitReadBuf((unsigned char*)masterBuffer, sizeof(masterBuffer));
                I2C_SlaveClearReadStatus();
        CyDelay(500); // Delay 500 ms untuk memberi waktu pada ESP
            }
        }
    }
}

int main(void) {
    CyGlobalIntEnable;
    I2C_InitCustom();
    UART_1_Start();

    for (;;) {
        // Jika data diterima dari master
        if (I2C_SlaveStatus() & I2C_SSTAT_WR_CMPLT) {
            UART_1_PutString("DITERIMA dari ESP: ");
            UART_1_PutString(slaveBuffer); 
            UART_1_PutString("\n");

            writeToControlRegisters(slaveBuffer);
            I2C_SlaveClearWriteStatus();
            memset(slaveBuffer, 0, sizeof(slaveBuffer));
            I2C_SlaveInitWriteBuf((unsigned char*)slaveBuffer, sizeof(slaveBuffer));
        }

        if (I2C_SlaveStatus() & I2C_SSTAT_RD_CMPLT) {
            ProcessStatusRegisters();
            

            UART_1_PutString("DIKIRIM ke ESP: ");
            UART_1_PutString(masterBuffer); 
            UART_1_PutString("\n");
            
            I2C_SlaveClearReadStatus();
            memset(masterBuffer, 0, sizeof(masterBuffer));
            I2C_SlaveInitReadBuf((unsigned char*)masterBuffer, sizeof(masterBuffer));
        }
        CyDelay(2000);
    }
}
