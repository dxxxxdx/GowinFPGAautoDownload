

#include <stdio.h>
#include "main.h"
#include "stm32f1xx_hal_uart.h"
#include "FPGAcap.h"

// this is a fpga capture module for STM32F103c8t6
//here is io config and basic uart/iic/spi functions
//for more info please go schema

#include "stm32f1xx_hal_gpio.h"
void input_init(void)
{
    //here is FO0-FO7
    GPIO_TypeDef* ports[] = {GPIOB, GPIOB, GPIOB, GPIOA, GPIOA, GPIOA, GPIOA, GPIOA};
    uint16_t pins[]       = {GPIO_PIN_5, GPIO_PIN_4, GPIO_PIN_3,
                             GPIO_PIN_15, GPIO_PIN_12, GPIO_PIN_11,
                             GPIO_PIN_10, GPIO_PIN_9};
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    for (int i = 0; i < 8; i++) {
        GPIO_InitStruct.Pin = pins[i];
        GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
        GPIO_InitStruct.Pull = GPIO_NOPULL;
        HAL_GPIO_Init(ports[i], &GPIO_InitStruct);
    }
}
void output_init(void) {
    // here is MTF0 - MTF7
    GPIO_TypeDef* ports[] = {
        GPIOB, GPIOB, GPIOB, GPIOB,
        GPIOB, GPIOB, GPIOB, GPIOB
    };
    uint16_t pins[] = {
        GPIO_PIN_0, GPIO_PIN_1, GPIO_PIN_10,
        GPIO_PIN_11, GPIO_PIN_15, GPIO_PIN_14,
        GPIO_PIN_13, GPIO_PIN_12
    };

    GPIO_InitTypeDef GPIO_InitStruct = {0};

    for (int i = 0; i < 8; ++i) {
        GPIO_InitStruct.Pin   = pins[i];
        GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
        GPIO_InitStruct.Pull  = GPIO_PULLDOWN;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
        HAL_GPIO_Init(ports[i], &GPIO_InitStruct);


        HAL_GPIO_WritePin(ports[i], pins[i], GPIO_PIN_RESET);
    }
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, GPIO_PIN_SET);
}

void send_uart_output(void) {
    //here is output via uart
    //you'd better bind it to your clk upstairs callback
    //you may need python.series to generate a wave on your pc side
    //use USART2 port plz,8bit without parity,you can also change python side to fit your config

    uint32_t time = HAL_GetTick();
    char data[8];
    GPIO_TypeDef* ports[] = {GPIOB, GPIOB, GPIOB, GPIOA, GPIOA, GPIOA, GPIOA, GPIOA};
    uint16_t pins[]       = {GPIO_PIN_5, GPIO_PIN_4, GPIO_PIN_3,
                             GPIO_PIN_15, GPIO_PIN_12, GPIO_PIN_11,
                             GPIO_PIN_10, GPIO_PIN_9};
    for (int i = 0; i < 8; ++i) {
        data[i] = HAL_GPIO_ReadPin(ports[i], pins[i]) ? '1' : '0';
    }
    // 拼接成字符串：时间 + GPIO 状态
    // 例如: "FPGA AT 1234: 10110011\n"
    char buf[64];
    int len = snprintf(buf, sizeof(buf),
                       "FPGA AT %lu: %c%c%c%c%c%c%c%c\n",
                       time,
                       data[0], data[1], data[2], data[3],
                       data[4], data[5], data[6], data[7]);

    HAL_UART_Transmit(&huart2, (uint8_t*)buf, len,100);
}
/* 简单 NOP 循环回退（需校准，精度差）*/
static inline void nop_delay_loops(uint32_t loops)
{
    for (volatile uint32_t i = 0; i < loops; ++i) {
        __NOP();
    }
}
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {

    if (GPIO_Pin == GPIO_PIN_0)
    {
        // 读取当前 PA0 电平，决定 PA8 输出
        GPIO_PinState state = HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_0);

        if (state == GPIO_PIN_SET) {
            // 上升沿：拉高 PA8
            HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_SET);
            HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET);
            nop_delay_loops(100000);
            HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_RESET);
        } else {
            // 下降沿：拉低 PA8
            HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_RESET);
            HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET);
            nop_delay_loops(100000);
            HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_RESET);
        }
        HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
    }
}