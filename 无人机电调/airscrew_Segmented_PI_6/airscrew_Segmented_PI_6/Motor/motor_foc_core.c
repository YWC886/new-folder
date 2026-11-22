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
#include "motor_foc_core.h"

/**
  ***********************************************************************************************************
  * ����
  * ********************************************************************************************************* 
  */ 
FOC_UDT foc;

/**
  ***********************************************************************************************************
  * @brief  motor_foc_init
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_foc_init(void)
{
    foc.i_u = 0.0f;
    foc.i_v = 0.0f;
    foc.i_w = 0.0f;

    foc.i_alpha = 0.0f;
    foc.i_beta  = 0.0f;
    
    foc.angle = 0.0f;
    foc.sin   = 0.0f;
    foc.cos   = 0.0f;

    foc.i_q = 0.0f;
    foc.i_d = 0.0f;

    foc.v_q = 0.0f;
    foc.v_d = 0.0f;
    foc.v_alpha = 0.0f;
    foc.v_beta  = 0.0f;

    foc.v_u = 0.0f;
    foc.v_v = 0.0f;
    foc.v_w = 0.0f;
    return;
}
/**
  ***********************************************************************************************************
  * @brief  
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_foc_clarke(void)
{
    foc.i_alpha = foc.i_u;
    foc.i_beta = (foc.i_u + 2.0f*foc.i_v) * 0.57735027f;
    return;
}

/**
  ***********************************************************************************************************
  * @brief  
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_foc_sin_cos(void)
{
    foc.cos = arm_cos_f32(foc.angle);
    foc.sin = arm_sin_f32(foc.angle);
}

/**
  ***********************************************************************************************************
  * @brief  
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_foc_park(void)
{
    foc.i_d =  foc.i_alpha * foc.cos + foc.i_beta * foc.sin;
    foc.i_q = -foc.i_alpha * foc.sin + foc.i_beta * foc.cos;
}

/**
  ***********************************************************************************************************
  * @brief  
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_foc_invpark(void)
{
    foc.v_alpha = foc.cos * foc.v_d - foc.sin * foc.v_q;
    foc.v_beta  = foc.sin * foc.v_d + foc.cos * foc.v_q;
}

/**
  ***********************************************************************************************************
  * @brief  
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_foc_invpark_delay_compensation(void)
{
		float m, theta_delay;
		float tmp, tmpTheta;
		float tmpcos, tmpsin;
		
		tmp = foc.speed_rad_s * PWM_FOC_PERIOD;	

		m = 1;
		
		theta_delay = foc.angle + 1.5 * tmp;
		if( theta_delay >= 2*PI )	theta_delay -= 2*PI;
		else if ( theta_delay < 0 )	theta_delay += 2*PI;
		tmpcos = arm_cos_f32(theta_delay);
		tmpsin = arm_sin_f32(theta_delay);
		
    foc.v_alpha = m * ( tmpcos * foc.v_d - tmpsin * foc.v_q );
    foc.v_beta  = m * ( tmpsin * foc.v_d + tmpcos * foc.v_q );
}

/**
  ***********************************************************************************************************
  * @brief   
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_foc_invclarke(void)
{  	
    foc.v_u = foc.v_beta;                            
    foc.v_v = (foc.v_alpha *1.73205078F + foc.v_beta)/2.0f;
    foc.v_w = (foc.v_alpha *1.73205078F - foc.v_beta)/2.0f;
   return;
}
 


void motor_foc_svpwm(float pwm_period, float volt_bus)
{
    int8_t sv_factor = 0;
    float t0_half, t1, t2, t_all, t_sum;
	float tu,tv,tw;

    t_all = (float)pwm_period;

	sv_factor = 3;
	sv_factor=(foc.v_v> 0.0f)?( sv_factor-1):sv_factor;						
	sv_factor=(foc.v_w> 0.0f)?( sv_factor-1):sv_factor;						
	sv_factor=(foc.v_u< 0.0f)?(7-sv_factor) :sv_factor;	 

    foc.v_u = (foc.v_u * (float)t_all)/volt_bus;
    foc.v_v = (foc.v_v * (float)t_all)/volt_bus;
    foc.v_w = (foc.v_w * (float)t_all)/volt_bus;

    switch (sv_factor)
    {
        case 1:  
		case 4:  
            t1 = foc.v_w;
            t2 = foc.v_u;
            t_sum = t1 + t2;
            if(t_sum > t_all)
            {
                t1 = t1/t_sum * t_all;
                t2 = t_all -t1;
            }    
            t0_half = (t_all - t1 - t2) * 0.5f; 
            tu = t1 + t2 + t0_half;
            tv = t2 + t0_half;
            tw = t0_half;
        break;    

        case 2:  
		case 5: 
            t1 = -foc.v_w;
            t2 = foc.v_v;
            t_sum = t1 + t2;
            if(t_sum > t_all)
            {
                t1 = t1/t_sum * t_all;
                t2 = t_all -t1;
            }  
            t0_half = (t_all - t1 - t2) * 0.5f;
            tu = t2 + t0_half;
            tv = t1 + t2 + t0_half;
            tw = t0_half;
        break; 

        case 3:  
        case 6:  
            t1 = foc.v_u;
            t2 = -foc.v_v;
            t_sum = t1 + t2;
            if(t_sum > t_all)
            {
                t1 = t1/t_sum * t_all;
                t2 = t_all -t1;
            }  
            t0_half = (t_all - t1 - t2) * 0.5f; 
            tu = t0_half;
            tv = t1 + t2 + t0_half;
            tw = t2 + t0_half;     
        break;  

        default:  
            tu = tv = tw = 0.0f;
        break;

    }
    PWM_DUTY_U = (uint16_t)(tu);
    PWM_DUTY_V = (uint16_t)(tv);
    PWM_DUTY_W = (uint16_t)(tw); 
    return;
}

/**
  ***********************************************************************************************************
  * @brief  Normilized SVPWM from TI
	* @param  Voltage unit: Udc/��3 = 1
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_foc_svpwm_normal(FOC_UDT *pV)
{
	float tmp1, tmp2, tmp3;
	int8_t sv_factor = 0;
	uint16_t pwm_HalfPeriod = PWM_TIM_PULSE>>1;
	
  tmp1= pV->v_beta;    
	tmp2= 0.5f * pV->v_beta + 0.8660254f * pV->v_alpha;  
  tmp3= tmp2 - tmp1;
      
	sv_factor=3;    
	sv_factor=(tmp2 > 0)?( sv_factor-1):sv_factor;
	sv_factor=(tmp3 > 0)?( sv_factor-1):sv_factor;
	sv_factor=(tmp1 < 0)?(7-sv_factor) :sv_factor;
    
	  if  (sv_factor==1 || sv_factor==4)  //  
		{  
			pV->Ta = tmp2;
			pV->Tb = tmp1 - tmp3;
			pV->Tc = -tmp2;
		}
    else if(sv_factor==2 || sv_factor==5)
		{  
			pV->Ta = tmp3 + tmp2;
			pV->Tb = tmp1;
			pV->Tc = -tmp1;
		}
    else
		{   
			pV->Ta = tmp3;
			pV->Tb = -tmp3;
			pV->Tc = -(tmp1 + tmp2);
		}
		PWM_DUTY_U = (uint16_t)(pV->Ta * pwm_HalfPeriod) + pwm_HalfPeriod;
    PWM_DUTY_V = (uint16_t)(pV->Tb * pwm_HalfPeriod) + pwm_HalfPeriod;
    PWM_DUTY_W = (uint16_t)(pV->Tc * pwm_HalfPeriod) + pwm_HalfPeriod; 
    return;
}


