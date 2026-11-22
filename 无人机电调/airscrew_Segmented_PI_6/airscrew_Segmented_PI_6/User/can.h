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
#ifndef _CAN_H_
#define _CAN_H_

#include "motor_all_header.h"

 
#define CAN_BAUDRATE_1MBPS    0
#define CAN_BAUDRATE_500KBPS  1
#define CAN_BAUDRATE_250KBPS  2
#define CAN_BAUDRATE_125KBPS  3
#define CAN_BAUDRATE_100KBPS  4
#define CAN_BAUDRATE_50KBPS   5

//���״̬�ϱ�(��֡����) 
#define S_ESC_STAT1_PORT_ID ((uint32_t)1150)//���  -> �ⲿ, S_CAN_MSG_ESC_STAT1 
#define S_ESC_STAT2_PORT_ID ((uint32_t)1151)//���  -> �ⲿ, S_CAN_MSG_ESC_STAT2 
#define S_ESC_STAT3_PORT_ID ((uint32_t)1152)//���  -> �ⲿ, S_CAN_MSG_ESC_STAT3 
#define S_ESC_STAT4_PORT_ID ((uint32_t)1153)//���  -> �ⲿ, S_CAN_MSG_ESC_STAT4 
#define S_ESC_STAT5_PORT_ID ((uint32_t)1154)//���  -> �ⲿ, S_CAN_MSG_ESC_STAT5 



typedef union 
{ 
  uint32_t ID;
  struct
  {
    uint32_t Source_node_id      :7;  //b6~b0 
    uint32_t Servide_not_message :1;  //b7
    uint32_t Message_type_id     :16; //b23~b8
    uint32_t Priority            :5;  //b28~b24
  } ID_Bit;
} CAN_MSG_ID;

 
//order: bit0 -> bit15 
struct CAN_MSG_ESC_MODE_BITS  // bits    description 
{ 
  uint16_t esc_mode       : 8; //low 8 bit 
  uint16_t pwm_thr_online : 1; //0->lost, 1->online 
  uint16_t can_thr_online : 1; //0->lost, 1->online 
  uint16_t thr_pri        : 1; //0->pwm thr first, 1->can thr first 
  uint16_t resv           : 5; 
}; 
 
union CAN_MSG_ESC_MODE_UN 
{ 
  uint16_t  all;
  struct CAN_MSG_ESC_MODE_BITS    bit; 
}; 
 
typedef struct 
{ 
  union CAN_MSG_ESC_MODE_UN esc_mode; //����ģʽ 
  int16_t esc_cmd;                    //����ָ�� 
  int16_t spd_rpm;                    //���ת�� 
  uint16_t resv: 8; 
  uint16_t tail: 8; 
} S_CAN_MSG_ESC_STAT1; 

#define DEF_CAN_DATA_STAT1  {0, 0, 0, 0}
 
typedef struct 
{ 
  int16_t  vdc_100mv;   // ĸ�ߵ�ѹ 
  int16_t  irms_100ma;  // �������Чֵ 
  int16_t  idq0_100ma;  // d-q����� 
  uint16_t resv: 8; 
  uint16_t tail: 8; 
} S_CAN_MSG_ESC_STAT2; 

#define DEF_CAN_DATA_STAT2  {0, 0, 0, 0}

typedef struct 
{ 
  int16_t  alg_err;    //�㷨������ 
  int16_t  alg_warn;   //�㷨������ 
  int16_t  vdq0_duty;  // d-q��ָ�� 
  uint16_t resv: 8; 
  uint16_t tail: 8; 
} S_CAN_MSG_ESC_STAT3; 

#define DEF_CAN_DATA_STAT3  {0, 0, 0, 0}
 
typedef struct 
{ 
  int16_t  mos_temp;    //mos ���¶� 
  int16_t  idq1_100ma;  // d-q����� 
  int16_t  vdq1_duty;   // d-q��ָ�� 
  uint16_t resv: 8; 
  uint16_t tail: 8; 
} S_CAN_MSG_ESC_STAT4; 

#define DEF_CAN_DATA_STAT4  {0, 0, 0, 0}
 
typedef struct  
{
  int16_t  idc;        //ĸ�߹������   
  int16_t  cap_temp;   //�����¶ȣ���λ0.1���϶�   
  int16_t  motor_temp; //����¶ȣ���λ0.1���϶�   
  uint16_t resv: 8;  
  uint16_t tail: 8;  
} S_CAN_MSG_ESC_STAT5; 

#define DEF_CAN_DATA_STAT5  {0, 0, 0, 0}

 
//order: bit0 -> bit63 
typedef struct 
{ 
  uint64_t chan1_thr_cmd: 10; 
  uint64_t chan1_node_id: 3; 
  uint64_t chan1_enable: 1; 

  uint64_t chan2_thr_cmd: 10; 
  uint64_t chan2_node_id: 3; 
  uint64_t chan2_enable: 1; 

  uint64_t chan3_thr_cmd: 10; 
  uint64_t chan3_node_id: 3; 
  uint64_t chan3_enable: 1; 

  uint64_t chan4_thr_cmd: 10; 
  uint64_t chan4_node_id: 3; 
  uint64_t chan4_enable: 1; 

  uint64_t tail_byte: 8; 
} S_CAN_ESC_CMD; 

 

void can_updata(void);


#endif

 




