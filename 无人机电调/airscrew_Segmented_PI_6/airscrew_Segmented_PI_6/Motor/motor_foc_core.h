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
#ifndef _MOTOR_FOC_CORE_H_
#define _MOTOR_FOC_CORE_H_

#include "motor_all_header.h"

typedef struct
{
    float i_u;
    float i_v;
    float i_w;
    
    float i_alpha;
    float i_beta;
    
    float angle;
    float sin;
    float cos;
    
    float i_q;
    float i_d;
    
    float v_q;
    float v_d;
    
    float v_alpha;
    float v_beta;
    
    float v_u;
    float v_v;
    float v_w;
		
		float Ta;
		float Tb;
		float Tc;
		
		float	speed_rad_s;
}FOC_UDT;
extern FOC_UDT foc;



void motor_foc_init(void);
void motor_foc_clarke(void);
void motor_foc_sin_cos(void);
void motor_foc_park(void);
void motor_foc_invpark(void);
void motor_foc_invclarke(void);
void motor_foc_svpwm(float pwm_period, float volt_bus);
void motor_foc_svpwm_normal(FOC_UDT *pV);
void motor_foc_invpark_delay_compensation(void);


#endif

 









