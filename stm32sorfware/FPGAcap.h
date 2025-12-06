//
// Created by zys on 25-11-18.
//

#ifndef FPGACAP_H
#define FPGACAP_H
#include "stm32f1xx_hal_uart.h"


void output_init(void) ;
void input_init(void) ;
extern UART_HandleTypeDef huart2;
void send_uart_output() ;
#endif //FPGACAP_H
