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
  * 
  * ********************************************************************************************************* 
  */ 
#ifndef _MOTOR_CTRL_CONFIG_H_
#define _MOTOR_CTRL_CONFIG_H_

#include "motor_all_header.h"

//#define NOTE_ID  1
//#define NOTE_ID  2
//#define NOTE_ID  3
//#define NOTE_ID  4

#define NOTE_ID  3


#define SPEED_DIR_CW		 -1
#define SPEED_DIR_CCW			1


#if ((NOTE_ID == 1) || (NOTE_ID == 3))  
  #define SPEED_DIR  SPEED_DIR_CW
#else
  #define SPEED_DIR  SPEED_DIR_CCW 
#endif


#define CMD_START_TH  12
#define CMD_STOP_TH  11


#define CPU_SYSTEM_CLOCK            240000000

#define M_PI                        PI
#define ANGLE_2PI                   2*M_PI

// ʹ���ĸ��������ȥ���ĸ���������Σ���һ��ֻ��ѡ��һ�ֵ��
//#define MOTOR_MODEL_30BL_H03        // ���Ӳִ��������
#define MOTOR_MODEL_60ST_M10A       // 60������2500ppr�������������

// ���ݵ���ͺ�ѡ����������
#ifdef MOTOR_MODEL_60ST_M10A
#define MOTOR_POLE_PAIRS            21
#endif

#ifdef MOTOR_MODEL_30BL_H03
#define MOTOR_POLE_PAIRS            3
#endif

// ���ݹ��ʰ�ĵ���������ʽѡ��ͬ�Ĳ�����ʽ
#define MOTOR_SAMP_RESISTANCE       -1        // �������ʹ�������Σ�����Ϊ��ֵ
#define MOTOR_SAMP_CURRENT_SENSOR   1         // ����������ʹ���������������Ϊ��ֵ
#define MOTOR_CURRENT_SAMP_MODE     MOTOR_SAMP_RESISTANCE       // ѡ����������ʽ

// �˴�Ӧ����Ϊ���ݹ��ʰ��ͺŶ����Ƿѹ�͹���ֵ
#define MOTOR_LOW_VOLT              15.0f            // Ƿѹֵ��V
#define MOTOR_HIGH_VOLT             28.0f            // ��ѹֵ��V

#define MOTOR_OVER_CURRENT          10.0f            // ����ֵ��A


// λ�ô��������ͣ����ܶ���һ����������Ҫ����
// #define MOTOR_POSITION_SENSOR_HALL                   // �������� 
// #define MOTOR_POSITION_SENSOR_INC_ENCODER_HALL       // �������������ϱ�����
// #define MOTOR_POSITION_SENSOR_INC_ENCODER                // ����������
#define MOTOR_POSITION_SENSOR_ABS_ENCODER            // ����ֵ������
// #define MOTOR_POSITION_SENSOR_ROTARY_TRANSFORMER     // ����
// #define MOTOR_POSITION_SENSORLESS                    // �޴�����

#ifdef MOTOR_POSITION_SENSOR_INC_ENCODER_HALL           // �����������������˸���������������������Ҫͬʱ�������������
    #ifndef MOTOR_POSITION_SENSOR_HALL
        #define MOTOR_POSITION_SENSOR_HALL
    #endif
#endif // MOTOR_POSITION_SENSOR_INC_ENCODER_HALL
// �����㷨״̬��ѡ��,���ܶ���һ����������Ҫ����
#define MOTOR_CTRL_SPEED_MODE                        1
#define MOTOR_CTRL_TORQUE_MODE                       2
#define MOTOR_CTRL_POSITION_MODE                     3
#define MOTOR_CTRL_OPEN_VD_MODE                      4
#define MOTOR_CTRL_OPEN_VQ_MODE                      5
#define MOTOR_CTRL_OPEN_DUTY_MODE                    6      // ������������

// ���Ʒ�ʽ
#define MOTOR_CTRL_MODE_SCALAR                       1      // ��������
#define MOTOR_CTRL_MODE_VECTER                       2       // ʸ������

// �޸��㷨
#define MOTOR_SL_BEMF_COMPARER                       // ���������ƱȽ���
#define MOTOR_SL_BEMF_ADC                            // ����ADC������
#define MOTOR_SL_SMO                                 // ���Ҳ���ģ
#define MOTOR_SL_PLL                                 // ���Ҳ����໷
#define MOTOR_SL_NONLINEAR_OBSERVER                  // �����Դ����۲���
#define MOTOR_SL_LU

// normalization
#define BASE_CURRENT					100
#define BASE_SPEED						5000

#define MAX_VOLT_CIRCLE_LIMIT		0.81				//the square of voltage circle limit



// motor parameters
#define RESISTANCE						1
#define INDUCTANCE						1
#define PERMANENT_FLUX				1


// �������
#define MOTOR_MIN_HALL_SPEED_RPM                     10
#define MOTOR_MAX_HALL_SPEED_RPM                     4600

// ����ʽ���������
// �����������Z���壬���趨��˾�
// #define QE_MECH_Z_MARK  
#define INC_ENCODER_MECH_PULSE                        2500                                      // ����ʽ����������
            
#endif

 









