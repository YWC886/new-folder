/**
  **************************************************************************
  * @file     at32f403a_407_board.h
  * @version  v2.0.8
  * @date     2022-04-02
  * @brief    header file for at-start board. set of firmware functions to
  *           manage leds and push-button. initialize delay function.
  **************************************************************************
  *                       Copyright notice & Disclaimer
  *
  * The software Board Support Package (BSP) that is made available to
  * download from Artery official website is the copyrighted work of Artery.
  * Artery authorizes customers to use, copy, and distribute the BSP
  * software and its related documentation for the purpose of design and
  * development in conjunction with Artery microcontrollers. Use of the
  * software is governed by this copyright notice and the following disclaimer.
  *
  * THIS SOFTWARE IS PROVIDED ON "AS IS" BASIS WITHOUT WARRANTIES,
  * GUARANTEES OR REPRESENTATIONS OF ANY KIND. ARTERY EXPRESSLY DISCLAIMS,
  * TO THE FULLEST EXTENT PERMITTED BY LAW, ALL EXPRESS, IMPLIED OR
  * STATUTORY OR OTHER WARRANTIES, GUARANTEES OR REPRESENTATIONS,
  * INCLUDING BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY,
  * FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.
  *
  **************************************************************************
  */

#ifndef _MCU_HARDWARE_CONFIG_H_
#define _MCU_HARDWARE_CONFIG_H_

#ifdef __cplusplus
extern "C" {
#endif

#include "stdio.h"
#include "at32f403a_407.h"

#define PWM_TIM_CLOCK                       CPU_SYSTEM_CLOCK                    // PWMģ��ʱ��ʹ��ϵͳCPUʱ�ӣ�240Mhz
#define PWM_TIM_FREQ                        16000                               // PWM�ز�Ƶ�ʣ�10khz
#define PWM_TIM_PULSE                       ((u16)(PWM_TIM_CLOCK/(PWM_TIM_FREQ)/2)-1)  // PWM���ڱȽ�ֵ
#define PWM_FOC_PERIOD                      (float)(1.0f/(float)PWM_TIM_FREQ)   // PWM���ڣ���λs
#define PWM_DEAD_TIME_NS                    ((u16) 1000)                        // PWM����ʱ�䣬ON+OFF ��λns
#define PWM_DEAD_TIME                       (u16)((unsigned long long)PWM_TIM_CLOCK/2*(unsigned long long)PWM_DEAD_TIME_NS/1000000000uL)
	
#define PWM_TIMER                           TMR1
#define PWM_DUTY_U                          TMR1->c1dt
#define PWM_DUTY_V                          TMR1->c2dt
#define PWM_DUTY_W                          TMR1->c3dt

 
 

// ADC������Դ�������ݲ�ʹ��ADC��DMAģʽ��3��ADCģ���ע�����������
#define ADC_REF_V                           (float)(3.3f)
#define VBUS_UP_RES                         (float)(10000.0f) 
#define VBUS_DOWN_RES                       (float)(330.0f) 
#define VBUS_CONVERSION_FACTOR              (float)(ADC_REF_V*(VBUS_UP_RES+VBUS_DOWN_RES)/VBUS_DOWN_RES/4095.0f)
    
#define SAMPLE_RES                          (float)(0.001f) 
#define AMP_GAIN                            (float)(10.0f)
#define SAMPLE_CURR_CON_FACTOR              (float)(ADC_REF_V/4095.0f/AMP_GAIN/SAMPLE_RES)

#define SAMPLE_RES_BUS                      (float)(0.132f)
#define AMP_GAIN_BUS                        (float)(1.0f)
#define SAMPLE_CURR_BUS_CON_FACTOR          (float)(ADC_REF_V/4095.0f/AMP_GAIN_BUS/SAMPLE_RES_BUS)
	
#define SAMPLE_RES_ANALOG                   (float)(1.0f)
#define AMP_GAIN_ANALOG                     (float)(1.0f)
#define SAMPLE_ANALOG_CON_FACTOR            (float)(ADC_REF_V/4095.0f/AMP_GAIN_ANALOG/SAMPLE_RES_ANALOG)
 
// ADC1ע����ͨ������
#define CURR_PHASE_A_ADC_CH                 ADC_CHANNEL_0
#define CURR_PHASE_A_ADC_GPIO_CRM_CLK       CRM_GPIOC_PERIPH_CLOCK
#define CURR_PHASE_A_ADC_PORT               GPIOA
#define CURR_PHASE_A_ADC_GPIO_PIN           GPIO_PINS_0

#define CURR_PHASE_B_ADC_CH                 ADC_CHANNEL_1
#define CURR_PHASE_B_ADC_GPIO_CRM_CLK       CRM_GPIOC_PERIPH_CLOCK
#define CURR_PHASE_B_ADC_PORT               GPIOA
#define CURR_PHASE_B_ADC_GPIO_PIN           GPIO_PINS_1

#define CURR_PHASE_C_ADC_CH                 ADC_CHANNEL_2
#define CURR_PHASE_C_ADC_GPIO_CRM_CLK       CRM_GPIOC_PERIPH_CLOCK
#define CURR_PHASE_C_ADC_PORT               GPIOA
#define CURR_PHASE_C_ADC_GPIO_PIN           GPIO_PINS_2

#define CURR_BUS_ADC_CH                     ADC_CHANNEL_1
#define CURR_BUS_ADC_GPIO_CRM_CLK           CRM_GPIOC_PERIPH_CLOCK
#define CURR_BUS_ADC_PORT                   GPIOA
#define CURR_BUS_ADC_GPIO_PIN               GPIO_PINS_1

#define VOLT_BUS_ADC_CH                     ADC_CHANNEL_5
#define VOLT_BUS_ADC_GPIO_CRM_CLK           CRM_GPIOB_PERIPH_CLOCK
#define VOLT_BUS_ADC_PORT                   GPIOA
#define VOLT_BUS_ADC_GPIO_PIN               GPIO_PINS_5

#define CURR_PHASE_A_REGISTER               (int16_t)ADC1->pdt1
#define CURR_PHASE_B_REGISTER               (int16_t)ADC1->pdt2
#define CURR_PHASE_C_REGISTER               (int16_t)ADC1->pdt3
#define VOLT_BUS_REGISTER                   (((int16_t)ADC1->pdt4)&0x00000FFF)



// �����������ӿڶ���
#define HALL_NUMBER                         3
#define HALL_CAPTURE_TIMER                  TMR3
#define HALL_CAPTURE_CRM_CLK                CRM_TMR3_PERIPH_CLOCK
#define HALL_CAPTURE_TIM_CLOCK              CPU_SYSTEM_CLOCK
#define HALL_CAPTURE_MAX_CNT                0xFFFF
#define HALL_CAPTURE_IRQHandler             TMR3_GLOBAL_IRQHandler
#define HALL_CAPTURE_IRQn                   TMR3_GLOBAL_IRQn
#define HALL_CAPTURE_FLITER                 0x6						     /* 0x0 ~ 0xF */
#define HALL_CAPTURE_TIMER_CLK              (HALL_CAPTURE_MAX_CNT*MOTOR_MIN_HALL_SPEED_RPM/60*MOTOR_POLE_PAIRS*(6))   /* 2 times small Hall cycle time */
#define HALL_CAPTURE_TIMER_DIV              ((uint16_t) ((double)HALL_CAPTURE_TIM_CLOCK/HALL_CAPTURE_TIMER_CLK))

 
 
 
 

#define HALL_A_GPIO_CRM_CLK                 CRM_GPIOA_PERIPH_CLOCK
#define HALL_A_PORT                         GPIOA
#define HALL_A_GPIO_PIN                     GPIO_PINS_6
#define HALL_B_GPIO_CRM_CLK                 CRM_GPIOA_PERIPH_CLOCK
#define HALL_B_PORT                         GPIOA
#define HALL_B_GPIO_PIN                     GPIO_PINS_7
#define HALL_C_GPIO_CRM_CLK                 CRM_GPIOA_PERIPH_CLOCK
#define HALL_C_PORT                         GPIOB
#define HALL_C_GPIO_PIN                     GPIO_PINS_0

#define HALL_PORTS_CBA                      (((GPIOB->idt & 0x0001) << 2) | ((GPIOA->idt & 0x00C0) >> 6))   // HALLֵ    

 






/******************** functions ********************/

 
void mcu_peripheral_init(void);

void pwm_init(void);
void hall_init(void);
void adc_config(void);
void timer5_init(void); 
void can_configuration(void); 
void CanBaudRateSet(uint8_t rate);
void speed_dac_output_init(void);



#ifdef __cplusplus
}
#endif

#endif

