/**
  ***********************************************************************************************************
 
  ***********************************************************************************************************
  * @attention
  *
  *
  ***********************************************************************************************************
  */
 
/**
  ***********************************************************************************************************
  * ͷ�ļ�
  * ********************************************************************************************************* 
  */ 
#include "motor_pid_calc.h"

/**
  ***********************************************************************************************************
  * ����
  * ********************************************************************************************************* 
  */ 
float axis_d_kp = 1.2f;
float axis_d_ki = 0.08f;
float axis_d_kb = 0.2f;
float axis_d_max = 0.9f;

float axis_q_kp = 1.2f;
float axis_q_ki = 0.08f;
float axis_q_kb = 0.2f;
float axis_q_max = 0.9f;

float velocity_kp = 12;//24.2f;
float velocity_ki = 0.02f;
float velocity_kb = 0.2F;
float velocity_max = 1.0F;

float position_kp = 0.01f;
float position_ki = 0.0f;
float position_kb = 0.0f;
float position_max = 1800000.0f;

PID_UDT axis_d_pid, axis_q_pid, velocity_pid, position_pid;

/**
  ***********************************************************************************************************
  * @brief  PID����
  * @param  �����������������pid����
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_pid_calc(float ref,float fdb,float* out,PID_UDT* pid)
{
    float err;
    float temp;
    float exc;

    err  = ref - fdb;
    temp  = pid->sum + pid->kp * err;

    /* Limit checking for PI output */
    if( temp > pid->max_out )
    {
       *out = pid->max_out;
    }
    else if( temp < pid->min_out )
    {
       *out = pid->min_out;
    }
    else
    {
       *out = temp;
    }

    exc = temp - *out;
    pid->sum = pid->sum + pid->ki * err - pid->kb * exc;
    pid->err = err;
}

/**
  ***********************************************************************************************************
  * @brief  PID������ʼ��
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_pid_init(void)
{
    axis_d_pid.kp = axis_d_kp;
    axis_d_pid.ki = axis_d_ki;
    axis_d_pid.kb = axis_d_kb;
    axis_d_pid.max_out = axis_d_max;
    axis_d_pid.min_out = -axis_d_max;
    axis_d_pid.sum = 0.0f;

    axis_q_pid.kp = axis_q_kp;
    axis_q_pid.ki = axis_q_ki;
    axis_q_pid.kb = axis_q_kb;
    axis_q_pid.max_out = axis_q_max;
    axis_q_pid.min_out = -axis_q_max;
    axis_q_pid.sum = 0.0f;
    
    velocity_pid.kp = velocity_kp;
    velocity_pid.ki = velocity_ki;
    velocity_pid.kb = velocity_kb;
    velocity_pid.max_out = velocity_max;
    velocity_pid.min_out = -velocity_max;
    velocity_pid.sum = 0.0f;
    
    position_pid.kp = position_kp;
    position_pid.ki = position_ki;
    position_pid.kb = position_kb;
    position_pid.max_out = position_max;
    position_pid.min_out = -position_max;
}

 
