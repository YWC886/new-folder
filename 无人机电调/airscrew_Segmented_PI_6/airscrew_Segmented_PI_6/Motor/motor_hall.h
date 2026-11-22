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
  * 头文件
  * ********************************************************************************************************* 
  */ 
#ifndef _MOTOR_HALL_H_
#define _MOTOR_HALL_H_

#include "motor_all_header.h"

#define  HALL_BUFF_SIZE          6
#define  A30D                    (0xffff/12)
#define  A30D_RAD                (A30D/65535.0f)
#define  ANGLE_60D               (2*A30D)

#define  HALL1_MID_RAD           (10*A30D_RAD)
#define  HALL2_MID_RAD           (2*A30D_RAD)
#define  HALL3_MID_RAD           (0*A30D_RAD)
#define  HALL4_MID_RAD           (6*A30D_RAD)
#define  HALL5_MID_RAD           (8*A30D_RAD)
#define  HALL6_MID_RAD           (4*A30D_RAD) 

#define Offset  0 //(90.0f   + (30.0f)      + 30.0f              -30.0f)       * ANGLE_2PI / 360.0f   // 计算结果为2.0943951
#define hall0offset(Q)  ( (Q < 0) ? (Q + ANGLE_2PI) : (Q) )

typedef struct
{
    int8_t   value;
    int8_t   last_value;
	
	int8_t   sector_table[8];                 // 霍尔扇区表
    int8_t   sector;                          // 当前扇区 
    uint16_t sector_stay_cnt;                 // 扇区停留时间计数器，扇区未发生变化，则PWM周期数累计
    uint16_t last_sector_stay_cnt;            // 上一扇区经历的PWM周期数，用于估算本扇区计数值
    uint16_t stalled_cnt;                     // 霍尔堵转计时器
    int8_t   last_sector;                     // 上次霍尔扇区
    int8_t   con_sector;                      // 反向扇区
	 
    int8_t   hall_dir;                        // 霍尔方向
	int8_t   last_hall_dir;                   // 上次霍尔方向
    uint16_t uni_sector_cnt;                  // 转向未变的扇区计数器       
    uint16_t past_sector_cnt;                 // 总共转过的扇区数
    uint8_t  new_sector_flg;

    float    pll_kp;
    float    pll_ki;
    float    old_rad_s;
    float    new_rad_s;
    float    abs_speed_rpm;
    float    speed_rpm;
    float    pll_angle_rad;
    float    pll_average_angle_rad;
    float    pll_dt_s;
    float    sector_mid_angle_rad;
    float    sector_mid_angle_read_rad;
    float    sector_mid_angle_read_last_rad;
    int8_t   error_cnt;
    
}HALL_UDT;
extern HALL_UDT hall;
#define  HALL_DEFAULTS  {0, 0, {-1,1,3,2,5,0,4,-1}, 0, 0, 0, 0, 0, 0, 0}  // 霍尔参数初始化
extern uint16_t hall_angle_ccw[8];// 转向和角度对应表
extern uint16_t hall_angle_cw[8];

void motor_hall_sensor_params_init(void);
void motor_hall_sensor_electrical_angle_init(void);
void motor_hall_sensor_sector_init(void);
void motor_hall_sensor_sector(void);
void motor_hall_sensor_direction(void);
void motor_hall_sensor_utils_norm_angle_rad(float *angle);
void motor_hall_sensor_pll_run(float phase, float dt, volatile float *phase_var,volatile float *speed_var);
void motor_hall_sensor_angle_cal(void);
void motor_hall_sensor_sampled(void);

#endif











