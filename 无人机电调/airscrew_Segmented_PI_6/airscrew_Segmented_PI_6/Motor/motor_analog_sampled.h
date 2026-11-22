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
  * Í·ÎÄ¼þ
  * ********************************************************************************************************* 
  */ 
#ifndef _MOTOR_ANALOG_SAMPLED_H_
#define _MOTOR_ANALOG_SAMPLED_H_

#include "motor_all_header.h"

typedef struct
{
    float    volt_bus;
    float    temperature;
		float			filterK1;
		float			filterK2;
		float			volt_filter;
		float			temp_filter;
}ANALOG_UDT;
extern ANALOG_UDT analog;
#define  ANALOG_DEFAULTS {0.0f,0.0f}


void motor_volt_bus(void);
 
void motor_volt_temp_filter_init(void);

#endif










