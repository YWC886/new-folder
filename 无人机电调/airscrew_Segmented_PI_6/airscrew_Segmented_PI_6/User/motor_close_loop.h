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
#ifndef _MOTOR_CLOSE_LOOP_H_
#define _MOTOR_CLOSE_LOOP_H_

#include "motor_all_header.h"

typedef struct
{
		float		IdRef;
		float		IqRef;
		float		SpdRef;  
		float		Vd_max;
		float		Vq_max;
		float		Vs_max;
		float 	IqRef_max;
}FIELD_WEAKEN_UDT;
extern FIELD_WEAKEN_UDT fw_ctrl;
#define  FIELD_WEAKEN_DEFAULTS {0.0f, 0.0f, 0.0f}

void motor_current_ctrl(void);
void motor_speed_ctrl(void);
 
void field_weakening_init(FIELD_WEAKEN_UDT *pV);
#endif

 




