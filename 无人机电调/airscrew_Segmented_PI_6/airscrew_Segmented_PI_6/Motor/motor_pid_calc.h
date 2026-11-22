/**
  ***********************************************************************************************************
  * @file    motor_pid_calc.h
  * @author  mandzy
  * @version V1.0.0
  * @date    2023-08-02
  * @brief   PID函数变量定义
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
#ifndef _MOTOR_PID_CALC_H_
#define _MOTOR_PID_CALC_H_

#include "motor_all_header.h"

typedef struct
{
    float kp;
    float ki;
    float kb;
    float max_out;
    float min_out;
    float sum;
    float period;
    float err;
}PID_UDT;
extern PID_UDT axis_d_pid, axis_q_pid, velocity_pid, position_pid;

void motor_pid_init(void);
void motor_pid_calc(float ref,float fdb,float* out,PID_UDT* pid);

#endif












