#include <project.h>
#include <stdlib.h>
#include <stdio.h>

uint8 uartData;
char uartBuffer[50];
uint8 bufferIndex = 0;
uint8 produkStatus[4][4];
uint8 statusRegValue[4];


// Tambahkan nilai BCD (untuk status register)
uint8 addBCD(uint8 bcdValue, uint8 increment) {
    uint8 puluhan = (bcdValue >> 4) & 0x0F;
    uint8 satuan = bcdValue & 0x0F;

    satuan += increment;

    if (satuan > 9) {
        satuan -= 10;
        puluhan += 1;
    }

    if (puluhan > 9) {
        puluhan = 0;
    }

    return (puluhan << 4) | satuan;
}

int main(void) {
    CyGlobalIntEnable;

    UARTT_Start(); // Memulai UART

    for (;;) {
        // Menerima Data
        if (UARTT_GetRxBufferSize() > 0) {

                    

            uartData = UARTT_GetChar(); // Membaca satu karakter dari UART buffer

            if (uartData == '<') {
                // Awal paket data, reset buffer
                bufferIndex = 0;
                uartBuffer[bufferIndex++] = uartData;

            } else if (uartData == '>') {
                // Akhir paket data, tambahkan null-terminator
                uartBuffer[bufferIndex++] = uartData;
                uartBuffer[bufferIndex] = '\0'; // Akhiri string
                bufferIndex = 0; // Reset buffer index

                
                // Validasi format paket data
                if (uartBuffer[0] == '<' && uartBuffer[strlen(uartBuffer) - 1] == '>') {



                    // Parsing data CSV
                    char *dataStart = strtok(uartBuffer + 1, ",>");
                    int count = 0;
                    while (dataStart != NULL && count < 16) {
                        int productIndex = count / 4;
                        int dataIndex = count % 4;

                        int value = atoi(dataStart);
                        if (value == 0 || value == 1) {
                            produkStatus[productIndex][dataIndex] = (uint8)value;
                        }
                        dataStart = strtok(NULL, ",>");
                        count++;
                    }

                    // Menggunakan data jika valid
                    if (count == 16) {
                        ControlReg1_Write((produkStatus[0][0] << 0) |
                                          (produkStatus[0][1] << 1) |
                                          (produkStatus[0][2] << 2) |
                                          (produkStatus[0][3] << 3) |
                                          (produkStatus[1][0] << 4) |
                                          (produkStatus[1][1] << 5) |
                                          (produkStatus[1][2] << 6) |
                                          (produkStatus[1][3] << 7));

                        ControlReg2_Write((produkStatus[2][0] << 0) |
                                          (produkStatus[2][1] << 1) |
                                          (produkStatus[2][2] << 2) |
                                          (produkStatus[2][3] << 3) |
                                          (produkStatus[3][0] << 4) |
                                          (produkStatus[3][1] << 5) |
                                          (produkStatus[3][2] << 6) |
                                          (produkStatus[3][3] << 7));

                    } else {
                        UARTT_PutString("Error: Invalid data count.\n");
                    }
                } else {
                    UARTT_PutString("Error: Invalid packet format.\n");
                }
            } else if (bufferIndex < sizeof(uartBuffer) - 1) {
                uartBuffer[bufferIndex++] = uartData;
            }
        }


        // Pengiriman Data
        statusRegValue[0] = restockA_Read() & 0xFF;
        statusRegValue[1] = restockB_Read() & 0xFF;
        statusRegValue[2] = restockC_Read() & 0xFF;
        statusRegValue[3] = restockD_Read() & 0xFF;

        for (int i = 0; i < 4; i++) {
            statusRegValue[i] = addBCD(statusRegValue[i], 0);
        }


        char outputData[10];
        snprintf(outputData, sizeof(outputData), "%02X%02X%02X%02X",
                 statusRegValue[0], statusRegValue[1],
                 statusRegValue[2], statusRegValue[3]
                 );

        UARTT_PutString(outputData);
        CyDelay(599);
        UARTT_PutString("\n");
    }
}
