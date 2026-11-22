/**
  ***********************************************************************************************************
  * @file    motor_open_loop.c 
  * @author  WeibinYang
  * @version V1.0.0
  * @date    2023-08-02
  * @brief   ����������ش���
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
#include "motor_close_loop.h"

extern S_CAN_MSG_ESC_STAT1  CanData_Stat_1;



 /**
  ***********************************************************************************************************
  * 
  * ********************************************************************************************************* 
  */ 
FIELD_WEAKEN_UDT  fw_ctrl = FIELD_WEAKEN_DEFAULTS;

/**
  ***********************************************************************************************************
  * @brief  Close loop control: current control, speed control, field-weaking control
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_current_ctrl(void)
{
		//motor_current_read(MOTOR_CURRENT_SAMP_MODE);    // ���ݵ�����������ʽ����
    foc.i_u = current.i_u_filter;
    foc.i_v = current.i_v_filter;
	
		foc.angle = hall2angle.pll_angle_rad;		//vf_ctrl.VirtualAngle;		//
		motor_foc_sin_cos();
	  motor_foc_clarke();
    motor_foc_park();
	
	  current.id_demand = 0;
 
		motor_pid_calc(current.id_demand, foc.i_d, &foc.v_d, &axis_d_pid);
	  
 
		LPF_100Hz_UqMax.SigIn = sqrtf( myabs( MAX_VOLT_CIRCLE_LIMIT - foc.v_d * foc.v_d ) );
		LowPassFilter_Cal(&LPF_100Hz_UqMax);					//low pass filter
		axis_q_pid.max_out = LPF_100Hz_UqMax.SigFilterOut;
		axis_q_pid.min_out = - axis_q_pid.max_out;
		if( foc.v_q > axis_q_pid.max_out) foc.v_q = axis_q_pid.max_out;
		else if( foc.v_q < axis_q_pid.min_out) foc.v_q = axis_q_pid.min_out;
		motor_pid_calc(current.iq_demand, foc.i_q, &foc.v_q, &axis_q_pid);
    
//		foc.v_q= 0.05;
//    foc.v_d= 0;

		foc.speed_rad_s = hall2angle.pll_speed_rad_s;
		motor_foc_invpark_delay_compensation();
 
		motor_foc_svpwm_normal(&foc);
}

/**
  ***********************************************************************************************************
  * @brief  FOC speed loop
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_speed_ctrl(void)
{
		if(++velocity.calc_velocity_cnt >= VELOCITY_CALC_PERIOD)
    {
        velocity.calc_velocity_cnt = 0;
        
        velocity.real_velocity = hall2angle.pll_speed_rpm_filter / BASE_SPEED;

        velocity.abs_real_velocity = myabs(velocity.real_velocity);

        // �ٶȻ�PI����
        motor_pid_calc(velocity.demand_velocity, velocity.real_velocity, &current.iq_demand, &velocity_pid);

    }    
		
		current.id_demand = 0;
		motor_current_ctrl();
}

 

 

void field_weakening_init(FIELD_WEAKEN_UDT *pV)
{
		pV->IqRef_max = BASE_CURRENT;
		pV->IdRef = 0;
		pV->IqRef = 0;
		pV->SpdRef = 0;
 }

 

