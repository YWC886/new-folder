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
#ifndef _MOTOR_CTRL_PROCESS_H_
#define _MOTOR_CTRL_PROCESS_H_

#include "motor_all_header.h"

/* *********************************************************************************************************************
* 枚举结构定义
**********************************************************************************************************************/

#define MOTOR_TURN_CCW              1         // 电机正转，轴视逆时针为正
#define MOTOR_TURN_CW               -1        // 电机反转，轴视顺时针为反
#define MOTOR_TURN_UCW              0         // 转向不定，电机未转或转速特别慢，探测不出转向或电机摆动，转向随机更改

#define MOTOR_RUN_MODE_TORQUE       1         // 转矩模式
#define MOTOR_RUN_MODE_SPEED        2         // 速度模式
#define MOTOR_RUN_MODE_POSITION     3         // 位置模式 

#define MOTOR_POSITION_SOURCE_COMM  1         // 通信命令
#define MOTOR_POSITION_SOURCE_AN    2         // 模拟量

extern  uint8_t                     motor_run_mode;
extern  uint8_t                     positon_cmd_source;
extern  uint8_t              brake_flg;
#define myabs(Q)  					( (Q < 0) ? (-Q) : (Q) )

typedef enum MOTOR_CTRL_STATE_MACHINE
{
	MOTOR_CTRL_SM_INIT                          = 0U,       // 外设初始化，上电后执行一次
    MOTOR_CTRL_SM_STOP                          = 1U,       // 停止态，上电或复位后的状态
    MOTOR_CTRL_SM_START                         = 2U,       // 启动态，调用启动函数后的状态
    MOTOR_CTRL_SM_MOTOR_STATE_IDENTIFICATION    = 3U,       // 电机状态鉴别，看看是否在自由旋转
    MOTOR_CTRL_SM_BOOTSTRAP                     = 4U,       // 自举电容充电态
    MOTOR_CTRL_SM_HALL_LEARNING                 = 5U,       // 霍尔自学习状态
    MOTOR_CTRL_SM_ROTOR_POSITION_IDENTIFICATION = 6U,       // 转子初始位置识别
    MOTOR_CTRL_SM_TRANSITION                    = 7U,       // 自由旋转态切换到闭环运行，此版本软件不支持
    MOTOR_CTRL_SM_NORMAL_OPERATION              = 8U,       // 闭环控制
    MOTOR_CTRL_SM_ERROR                         = 9U,       // 故障状态，电机停转
    MOTOR_CTRL_SM_IDLE                          = 10U,      // 空闲状态，启动后给定为0的状态
    MOTOR_CTRL_SM_RAMP_DOWN                     = 11U,      // 斜坡下降状态
    MOTOR_CTRL_SM_ZERO_CHECK                    = 12U       // 零点校准检查状态
} MOTOR_CTRL_STATE_UDT;
extern MOTOR_CTRL_STATE_UDT motor_ctrl_state;               // 期望电机状态

// 运行中的一些故障类型定义
typedef enum MOTOR_ERROR_ID
{
    MOTOR_ERROR_ID_NO_ERROR                      = 0x0000U,       // 陷阱故障                error_status = 0
    MOTOR_ERROR_ID_OVERCURRENT                   = 0x0001U,       // 过流故障                error_status = 1
    MOTOR_ERROR_ID_SHORTCIRCUIT                  = 0x0002U,       // 短路故障                error_status = 2
    MOTOR_ERROR_ID_WRONGHALL                     = 0x0004U,       // 错误霍尔                error_status = 4
    MOTOR_ERROR_ID_HALL_LEARNING_TIMEOUT         = 0x0008U,       // 霍尔学习失败            error_status = 8 
    MOTOR_ERROR_ID_STALL                         = 0x0010U,       // 堵转故障                error_status = 16
    MOTOR_ERROR_ID_UNDER_OVER_VOLTAGE            = 0x0020U,       // 过欠压故障              error_status = 32
    MOTOR_ERROR_ID_MOTOR_FREE_RUNNING            = 0x0040U,       // 电机自由旋转并捕获失败  error_status = 64
    MOTOR_ERROR_ID_MOTOR_FREE_REV_RUNNING        = 0x0080U,       // 电机反向自由旋转        error_status = 128
    MOTOR_ERROR_ID_STARTUP_FAILURE               = 0x0100U        // 多次启动失败            error_status = 256
} MOTOR_ERROR_ID_UDT;
extern MOTOR_ERROR_ID_UDT motor_error_status;

typedef union MOTOR_RUN_FLG
{
    u16 all;
    struct {
                u8 enable   :1;          // 使能开关动作
                u8 disable  :1;          // OFF2,自由停车，直接断逆变桥
                u8 start    :1;          // 启动命令
                u8 stop     :1;          // 停转命令，斜坡减速停车，等速度降到最低转速时再关闭逆变桥 
                u8 revert   :1;          // 反转命令
								u8 OpenLoop	:1;					 // VF control and Voltage open loop
								u8 SpdLoop	:1;
								u8 FWctrl		:1;
            }bits;
}MOTOR_RUN_FLG_UDT;
extern MOTOR_RUN_FLG_UDT motor_run_status;

typedef struct 
{
    float position;
    float velocity;
    float i_q;
    float i_d;
    float v_q;
    float v_d;
    float theta;
    float duty;
}MOTOR_CTRL_REF_UDT;
extern MOTOR_CTRL_REF_UDT motor_ctrl_ref;

typedef struct 
{
    float target;
    float present;
    float acc;
    float dec;
}MOTOR_CTRL_SET_UDT;
extern MOTOR_CTRL_SET_UDT motor_ctrl_duty_set;
extern MOTOR_CTRL_SET_UDT motor_ctrl_speed_set;
extern MOTOR_CTRL_SET_UDT motor_ctrl_torque_set;
extern MOTOR_CTRL_SET_UDT motor_ctrl_position_set;

extern uint16_t timer_1s_flg, timer_1s_cnt;
extern uint8_t              motor_run_flg;
void motor_ctrl_state_init(void);
void motor_ctrl_state_loop(void);
void motor_ctrl_state_start(void);
void motor_ctrl_state_stop(void);
void motor_ctrl_vector_loop(void);
void motor_ctrl_scalar_loop(void);
void motor_ctrl_loop(void);
void motor_ctrl_start_pwm(void);
void motor_ctrl_stop_pwm(void);
void motor_ctrl_start_stop(void);

float motor_ctrl_ramp_change(float ramp_now, float ramp_target, float ramp_inc, float ramp_dec);
float motor_ctrl_ramp_set(MOTOR_CTRL_SET_UDT set, uint8_t cnt);

void motor_ctrl_scalar_pwm_generate(float bldc_duty);


extern uint8_t iap_flag;
	
void iap_command_handle(void);
void iap_init(void);


#endif











