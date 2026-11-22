/**
  ***********************************************************************************************************
  * @file    motor_velocity_loop.h
  * @author  mandzy
  * @version V1.0.0
  * @date    2023-08-02
  * @brief   速度环变量定义
  ***********************************************************************************************************
  * @attention
  *
  *
  ***********************************************************************************************************
  */
 
/**
  ***********************************************************************************************************
  * 头文件
  * ********************************************************************************************************* 
  */ 
#ifndef _MOTOR_VELOCITY_LOOP_H_
#define _MOTOR_VELOCITY_LOOP_H_

#include "motor_all_header.h"

#define VELOCITY_CALC_FREQ        (float)(PWM_TIM_FREQ/VELOCITY_CALC_PERIOD)      // 速度计算频率,单位hz
#define VELOCITY_CALC_PERIOD      10                    // PWM_TIM_FREQ/VELOCITY_CALC_FREQ,以PWM周期为基准

typedef struct
{
    int8_t   calc_velocity_cnt;           // 速度计算周期计数器，以PWM周期为基准
    int32_t  encoder_pulse_number;        // 编码器脉冲数
    int32_t  last_encoder_pulse_number;   // 上次编码器脉冲数
    float    demand_velocity;             // 速度需求值
    float    real_velocity;               // 实际速度，单位0.001rps
    float    abs_real_velocity;           // 实际速度绝对值，单位0.001rps
    float    speed;                       // 速度，单位rpm
    float    abs_speed;                   // 速度绝对值，单位rpm    
}VELOCITY_UDT;

extern VELOCITY_UDT velocity;
void motor_velocity_init(void);
void motor_velocity_loop(void);
extern int32_t  qei_pulse_number;        // 编码器脉冲数
#endif

/************************************* (C) COPYRIGHT mandzy *******END OF FILE******************************/



