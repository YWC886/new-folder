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
#ifndef _MOTOR_CURRENT_PROCESS_H_
#define _MOTOR_CURRENT_PROCESS_H_

#include "motor_all_header.h"

typedef struct
{
    float    iq_demand;
    float    id_demand;
    
    uint8_t  offset_cnt;
    uint8_t  offset_flg;
    
    int32_t  i_u_offset;
    int32_t  i_v_offset;
    int32_t  i_w_offset;
    int32_t  i_bus_offset;
    
    float    i_u;
    float    i_v;
    float    i_w;

    float    i_bus;
	
		float		filterK1;
		float		filterK2;
	  float		i_u_filter;
		float		i_v_filter;
		float		i_w_filter;
		
		float		filter500HzK1;
		float		filter500HzK2;
		float		i_bus_filter;
}CURRENT_UDT;
extern CURRENT_UDT current;
#define  CURRENT_DEFAULTS {0.0f, 0.0f, 0, 0, 0, 0, 0, 0.0f, 0.0f,0.0f,0.0f, 0.0f,0.0f,0.0f,0.0f, 0.0f,0.0f}

void motor_current_init(void);
uint8_t motor_current_offset(void);
void motor_current_read(int8_t mode);
void motor_current_loop(void);
void motor_current_d_lock(void);
#endif






