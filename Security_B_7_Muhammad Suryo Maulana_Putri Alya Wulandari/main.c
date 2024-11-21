#include "project.h"
#include "Status_Reg_1.h"
#include "Status_Reg_2.h"
#include "Status_Reg_3.h"
#include "Status_Reg_4.h"
#include "Status_Reg_5.h"
#include "Status_Reg_6.h"
#include "Status_Reg_7.h"
#include "Control_Reg_1.h"
#include <stdbool.h>
#include <stdio.h>

#define ID_SIZE 3            // Ukuran ID
#define PASSWORD_SIZE 4      // Ukuran Password
#define STATUS_BUFFER_SIZE 1 // Buffer untuk menerima status dari ESP32

uint8_t idBuffer[ID_SIZE];       // Buffer untuk ID
uint8_t passwordBuffer[PASSWORD_SIZE]; // Buffer untuk Password
uint8_t statusBuffer[STATUS_BUFFER_SIZE]; // Buffer untuk menerima status dari ESP32
uint8_t confirmationCount = 0;   // Counter untuk jumlah konfirmasi karakter
uint8_t characterTable[37][6] = {
    {0, 0, 0, 0, 0, 0}, // A
    {0, 0, 0, 0, 0, 1}, // A
    {0, 0, 0, 0, 1, 0}, // B
    {0, 0, 0, 0, 1, 1}, // C
    {0, 0, 0, 1, 0, 0}, // 2
    {0, 0, 0, 1, 0, 1}, // D
    {0, 0, 0, 1, 1, 0}, // E
    {0, 0, 0, 1, 1, 1}, // F
    {0, 0, 1, 0, 0, 0}, // 3
    {0, 0, 1, 0, 0, 1}, // G
    {0, 0, 1, 0, 1, 0}, // H
    {0, 0, 1, 0, 1, 1}, // I
    {0, 0, 1, 1, 0, 0}, // 4
    {0, 0, 1, 1, 0, 1}, // J
    {0, 0, 1, 1, 1, 0}, // K
    {0, 0, 1, 1, 1, 1}, // L
    {0, 1, 0, 0, 0, 0}, // 5
    {0, 1, 0, 0, 0, 1}, // M
    {0, 1, 0, 0, 1, 0}, // N
    {0, 1, 0, 0, 1, 1}, // O
    {0, 1, 0, 1, 0, 0}, // 6
    {0, 1, 0, 1, 0, 1}, // P
    {0, 1, 0, 1, 1, 0}, // Q
    {0, 1, 0, 1, 1, 1}, // R
    {0, 1, 1, 0, 0, 0}, // 7
    {0, 1, 1, 0, 0, 1}, // S
    {0, 1, 1, 0, 1, 0}, // T
    {0, 1, 1, 0, 1, 1}, // U
    {0, 1, 1, 1, 0, 0}, // 8
    {0, 1, 1, 1, 0, 1}, // V
    {0, 1, 1, 1, 1, 0}, // W
    {0, 1, 1, 1, 1, 1}, // X
    {1, 0, 0, 0, 0, 0}, // 9
    {1, 0, 0, 0, 0, 1}, // Y
    {1, 0, 0, 0, 1, 0}, // Z
    {1, 0, 0, 0, 1, 1}, // 0
    {1, 0, 0, 1, 0, 0}  // 1
};


char characters[37] = "0ABC2DEF3GHI4JKLM5NOP6QRSTU8VWXY90Z1";

// Fungsi untuk mengonversi nilai 6-bit ke karakter alfanumerik
char convertToCharPW(uint8_t value) {
    if (value < 37) {
        return characters[value]; // Ambil karakter sesuai indeks
    }
    return '?'; // Jika nilai di luar jangkauan, tampilkan sebagai '?'
}
bool idReadyToSend = false;      // Flag untuk memastikan ID hanya dikirim jika sudah lengkap
bool passwordReadyToSend = false; // Flag untuk memastikan Password hanya dikirim jika sudah lengkap
bool idValidated = false;        // Flag untuk memastikan ID sudah divalidasi

// Fungsi untuk mengonversi nilai biner ke karakter alfanumerik
char convertToCharID(uint8_t value) {
    if (value <= 9) {
        return '0' + value; // Konversi angka 0-9 ke karakter '0'-'9'
    } else if (value >= 10 && value <= 15) {
        return 'A' + (value - 10); // Konversi angka 10-15 ke karakter 'A'-'F'
    } else {
        return '?'; // Jika nilai di luar jangkauan, tampilkan sebagai '?'
    }
}

// Fungsi untuk membaca ID dari Status Register
void readIDFromStatusRegisters() {
    if (confirmationCount == 1) {
        idBuffer[0] = Status_Reg_1_Read() & 0x0F; // Baca karakter pertama
    } else if (confirmationCount == 2) {
        idBuffer[1] = Status_Reg_2_Read() & 0x0F; // Baca karakter kedua
    } else if (confirmationCount == 3) {
        idBuffer[2] = Status_Reg_3_Read() & 0x0F; // Baca karakter ketiga
        idReadyToSend = true;  // Tandai bahwa ID lengkap dan siap dikirim
    }
}

// Fungsi untuk membaca Password dari Status Register
void readPasswordFromStatusRegisters() {
    if (confirmationCount == 1) {
        passwordBuffer[0] = Status_Reg_4_Read() & 0x0F; // Baca karakter pertama
    } else if (confirmationCount == 2) {
        passwordBuffer[1] = Status_Reg_5_Read() & 0x0F; // Baca karakter kedua
    } else if (confirmationCount == 3) {
        passwordBuffer[2] = Status_Reg_6_Read() & 0x0F; // Baca karakter ketiga
    } else if (confirmationCount == 4) {
        passwordBuffer[3] = Status_Reg_7_Read() & 0x0F; // Baca karakter keempat
        passwordReadyToSend = true;  // Tandai bahwa Password lengkap dan siap dikirim
    }
}

// Fungsi untuk mempersiapkan ID untuk dikirim ke ESP32
void prepareIDForSending() {
    for (int i = 0; i < ID_SIZE; i++) {
        idBuffer[i] = convertToCharID(idBuffer[i]); // Konversi ke karakter alfanumerik
    }
}

// Fungsi untuk mempersiapkan Password untuk dikirim ke ESP32
void preparePasswordForSending() {
    for (int i = 0; i < PASSWORD_SIZE; i++) {
        passwordBuffer[i] = convertToCharPW(passwordBuffer[i]); // Konversi ke karakter alfanumerik
    }
}

int main(void) {
    CyGlobalIntEnable;  // Mengaktifkan global interrupt

    // Inisialisasi I2C dan buffer data
    I2CS_Start();
    I2CS_SlaveInitReadBuf(idBuffer, sizeof(idBuffer)); // Buffer untuk ID yang dikirim ke ESP32
    I2CS_SlaveInitWriteBuf(statusBuffer, sizeof(statusBuffer)); // Buffer untuk menerima status dari ESP32
    I2CS_SlaveClearReadStatus();
    I2CS_SlaveClearWriteStatus();

    // Matikan semua LED pada awalnya
    Control_Reg_1_Write(0x00);

    for (;;) {
        // Proses input ID
        if (!idValidated && KonfirmasiID_Read() == 0) { // Asumsi tombol KonfirmasiID aktif rendah
            CyDelay(20); // Debounce delay
            if (KonfirmasiID_Read() == 0) { // Pastikan tombol masih ditekan
                confirmationCount++; // Menambah counter konfirmasi

                // Baca ID dari Status Registers
                readIDFromStatusRegisters();

                // Jika konfirmasi karakter selesai (3 karakter sudah dikonfirmasi)
                if (confirmationCount == ID_SIZE) {
                    prepareIDForSending();  // Siapkan ID untuk dikirim
                    confirmationCount = 0;  // Reset counter setelah konfirmasi selesai
                    idValidated = true;     // Tandai bahwa ID sudah divalidasi
                }

                // Tunggu sampai tombol dilepas sebelum pembacaan berikutnya
                while (KonfirmasiID_Read() == 0);
            }
        }

        // Proses input Password
        if (idValidated && KonfirmasiPassword_Read() == 0) { // Asumsi tombol KonfirmasiPassword aktif rendah
            CyDelay(20); // Debounce delay
            if (KonfirmasiPassword_Read() == 0) { // Pastikan tombol masih ditekan
                confirmationCount++; // Menambah counter konfirmasi

                // Baca Password dari Status Registers
                readPasswordFromStatusRegisters();

                // Jika konfirmasi karakter selesai (4 karakter sudah dikonfirmasi)
                if (confirmationCount == PASSWORD_SIZE) {
                    preparePasswordForSending();  // Siapkan Password untuk dikirim
                    confirmationCount = 0;        // Reset counter setelah konfirmasi selesai
                }

                // Tunggu sampai tombol dilepas sebelum pembacaan berikutnya
                while (KonfirmasiPassword_Read() == 0);
            }
        }

        // Kirim ID ke ESP32 hanya jika ID lengkap
        if (idReadyToSend && (I2CS_SlaveStatus() & I2CS_SSTAT_RD_CMPLT)) {
            I2CS_SlaveClearReadStatus(); // Clear status setelah data dibaca
            I2CS_SlaveInitReadBuf(idBuffer, sizeof(idBuffer)); // Siapkan buffer untuk input berikutnya
            idReadyToSend = false; // Reset flag setelah ID dikirim
        }

        // Kirim Password ke ESP32 hanya jika Password lengkap
        if (passwordReadyToSend && (I2CS_SlaveStatus() & I2CS_SSTAT_RD_CMPLT)) {
            I2CS_SlaveClearReadStatus(); // Clear status setelah data dibaca
            I2CS_SlaveInitReadBuf(passwordBuffer, sizeof(passwordBuffer)); // Siapkan buffer untuk input berikutnya
            passwordReadyToSend = false; // Reset flag setelah Password dikirim
        }

        // Cek apakah status login diterima dari ESP32
        if (I2CS_SlaveStatus() & I2CS_SSTAT_WR_CMPLT) {
            // Jika status login berhasil atau gagal diterima
            if (statusBuffer[0] == 0x01) {
                Control_Reg_1_Write(0x02);  // Login berhasil, nyalakan LED_password
            } else if (statusBuffer[0] == 0x02) {
                Control_Reg_1_Write(0x00);  // Matikan LED_password, ID atau Password salah
                confirmationCount = 0;      // Reset counter konfirmasi
                idValidated = false;        // Reset validasi ID
            }
            I2CS_SlaveClearWriteStatus(); // Clear status setelah data diterima
        }

        CyDelay(500); // Delay untuk stabilisasi sistem
    }
}
