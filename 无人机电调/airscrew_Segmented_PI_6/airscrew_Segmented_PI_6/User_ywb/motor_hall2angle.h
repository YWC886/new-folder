/**
  ***********************************************************************************************************
  * @file    motor_hall_encoder.h
  * @author  mandzy
  * @version V1.0.0
  * @date    2023-08-02
  * @brief   霍尔传感器处理
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
#ifndef _MOTOR_HALL_TO_ANGLE_H_
#define _MOTOR_HALL_TO_ANGLE_H_

#include "motor_all_header.h"

 
#define		HALL_CAPTURE_EDGE_CNT			HALL_CAPTURE_TIMER->c1dt
#define		HALL_CAPTURE_CNT					HALL_CAPTURE_TIMER->cval
#define 	HALL_CAPTURE_RAD_S_SCALE  (PI/3*HALL_CAPTURE_TIMER_CLK)      // CaptureFreq /6 * 2*PI / Delta = scale / delta 

#define   TIMER5_12_DIV							12
#define 	HALL_CIRCLE_TIMER_CLK  		((float)CPU_SYSTEM_CLOCK/TIMER5_12_DIV)      //  Timer2_CLK / CNT_Timer2 = speed_Hz
#define 	HALL_CIRCLE_TIMER_PERIOD  ((float)TIMER5_12_DIV/CPU_SYSTEM_CLOCK)      //  Timer2_CLK / CNT_Timer2 = speed_Hz
#define		HALL_CIRCLE_TIMER					TMR5
#define		HALL_CIRCLE_CNT						HALL_CIRCLE_TIMER->cval

typedef struct
{
    int8_t   value;
    int8_t   last_value;
	
    int8_t   sector;                          // the hall sector
	  int8_t   last_sector;                     // the last hall sector
		int8_t   hall_dir;                        // hall direction
		
		float		 hall_edgeAngle;									// angle of sector edge
		uint32_t hall_edgeTime;										// time of sector edge
		uint8_t  new_sector_flg;
		
		float		 cap_speed_rad_s_abs;										// calculate by capture in rpm
		float		 cap_speed_rad_s;
		float		 cap_speed_rad_s_filter;
		float		 filterK1;
	  float		 filterK2;
	
		uint32_t	circle_period_cnt;
		float		 circle_freq;
		float		 circle_speed_rad_s;
		float		 circle_speed_rad_s_filter;
		float		 circle_angle_error;
		float    circle_angle_calib_sum;
		float    circle_angle_calib_delta;
		float		 circle_angle_init;
		uint32_t	circle_time_cnt;
		float		 raw_angle_rad_test;
	
	  int8_t   error_cnt;
		uint8_t	 error_flag;
		uint8_t  cap_cnt_overflow_flag;
	
		float		 raw_angle_rad;										// the Output angle before filtering
		float		 capture_time;										// the time in capture cnt
		float 	 capture_clk_period;							// the period of capture clk
		
		float    pll_angle_rad;										// the Output angle after filtering (-PI -- PI)
		float    pll_speed_rad_s;									// the Output speed
		float    pll_speed_rpm;
		float		 pll_speed_rpm_filter;

    float    pll_kp;
    float    pll_ki;
}HALL_TO_ANGLE_UDT;
extern HALL_TO_ANGLE_UDT hall2angle;
#define  HALL_TO_ANGLE_DEFAULTS  {0, 0, 0, 0, 0, 0, 0, 0, 0}  // 霍尔参数初始化

extern int8_t sector_table[8];
extern float hall_edge_angle[6];
 

void motor_hall2angle_params_init(HALL_TO_ANGLE_UDT *pV);
void motor_hall2angle_electrical_angle_init(HALL_TO_ANGLE_UDT *pV);
 
void motor_hall_sector(HALL_TO_ANGLE_UDT *pV);
void motor_hall_sector_direction(HALL_TO_ANGLE_UDT *pV);
void motor_hall_sector_angle(HALL_TO_ANGLE_UDT *pV);
void motor_hall_speed_calc(HALL_TO_ANGLE_UDT *pV);
void motor_hall_to_angle_cal(HALL_TO_ANGLE_UDT *pV);
void motor_hall2angle_sector_init(HALL_TO_ANGLE_UDT *pV);
 

#endif

/************************************* (C) COPYRIGHT mandzy *******END OF FILE******************************/









