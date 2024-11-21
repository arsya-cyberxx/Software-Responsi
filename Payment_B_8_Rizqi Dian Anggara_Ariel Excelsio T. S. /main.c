#include "project.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#include "Control_Reg_Ratusan.h"  
#include "Control_Reg_Puluhan.h"
#include "Control_Reg_Satuan.h"
#include "Status_Reg_Success.h"
#include "Status_Reg_LoginStatus.h"

#define DIGIT_COUNT 1  // Jumlah digit untuk setiap control register

// Definisi fungsi control register
#define RATUSAN_CONTROL_REG Control_Reg_Ratusan_Write
#define PULUHAN_CONTROL_REG Control_Reg_Puluhan_Write
#define SATUAN_CONTROL_REG Control_Reg_Satuan_Write

// Fungsi Untuk menulis pada control register
void set_control_registers(const char *data) {
    // Ekstrak setiap 1 digit dan buffer masing-masing untuk setiap digit.
    char ratusan_data[DIGIT_COUNT + 1] = {0};
    char puluhan_data[DIGIT_COUNT + 1] = {0};
    char satuan_data[DIGIT_COUNT + 1] = {0};

    strncpy(ratusan_data, data, DIGIT_COUNT);       // Mengambil digit ratusan 
    strncpy(puluhan_data, data + DIGIT_COUNT, DIGIT_COUNT);  // Digit puluhan
    strncpy(satuan_data, data + 2 * DIGIT_COUNT, DIGIT_COUNT); // Digit satuan

    // Konversi tipe data yang diperoleh melalui UART agar dapat ditulis pada control register
    RATUSAN_CONTROL_REG(atoi(ratusan_data)); // Write digit ratusan
    PULUHAN_CONTROL_REG(atoi(puluhan_data)); // Write digit puluhan
    SATUAN_CONTROL_REG(atoi(satuan_data));   // Write digit satuan
}

// Fungsi komparasi input dan total harga lalu mengirim status register untuk update data server
void send_status_via_uart(void) {
    uint8_t success_status = Status_Reg_Success_Read();
    uint8_t login_status = Status_Reg_LoginStatus_Read();

    if (success_status == 1) {
        UART_PutString("Payment Success");
    } else if (login_status == 1) {
        UART_PutString("Payment Failed");
    }
}

int main(void) {
    CyGlobalIntEnable;
    UART_Start();
    UART_PutString("UART Initialized\n");

    char received_data[3] = {0}; // Buffer 3 karakter
    int index = 0;
    
    for (;;) {
        char received = UART_GetChar();
            // Proses data sampai 3 karakter terbaca
        if (received != 0) {
            if (index < 4) {
                received_data[index++] = received;
            }
                // Setelah memperoleh semua karakter, diproses 
            else {
                received_data[index] = '\0';  // Null-terminate untuk satu string
                set_control_registers(received_data); // Mengirim data pada control register
                send_status_via_uart(); // Fungsi komparasi pembayaran
                    
                index = 0; // Reset index untuk proses selanjutnya
                memset(received_data, 0, sizeof(received_data)); // Clear buffer
                }
            } 
        }
}
