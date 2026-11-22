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
#include "motor_open_loop.h"

 /**
  ***********************************************************************************************************
  * 
  * ********************************************************************************************************* 
  */ 
VFCONTROL_UDT vf_ctrl = VFCONTROL_DEFAULTS;

/**
  ***********************************************************************************************************
  * @brief  Open loop control, VF control; or Vq\Vd direct input
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_open_loop(void)
{
		//motor_current_read(MOTOR_CURRENT_SAMP_MODE);    // ���ݵ�����������ʽ����
    foc.i_u   = current.i_u;
    foc.i_v   = current.i_v;
	
		//vf_ctrl.VirtualAngle = vf_ctrl.VirtualAngle + PWM_FOC_PERIOD * vf_ctrl.RefFreq * 2 * PI;
		if( vf_ctrl.VirtualAngle > 2*PI )
			vf_ctrl.VirtualAngle -= 2*PI;
		else if ( vf_ctrl.VirtualAngle < 0 )
			vf_ctrl.VirtualAngle += 2*PI;
	
		foc.angle = vf_ctrl.VirtualAngle;		//hall2angle.pll_angle_rad;		//
		motor_foc_sin_cos();
		motor_foc_clarke();
    motor_foc_park();
		
		foc.v_d = vf_ctrl.RefVolt;	 
		foc.v_q = 0;	 

    motor_foc_invpark();
 
		motor_foc_svpwm_normal(&foc);
}

 

 

