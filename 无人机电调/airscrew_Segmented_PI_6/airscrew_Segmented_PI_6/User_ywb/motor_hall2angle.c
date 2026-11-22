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
#include "motor_hall2angle.h"

/**
  ***********************************************************************************************************
  * ����
  * ********************************************************************************************************* 
  */ 
HALL_TO_ANGLE_UDT    hall2angle = HALL_TO_ANGLE_DEFAULTS;

 

int8_t sector_table[8] = 
{	
	// Airscrew motor Hall table
	-1,    	//		0
	4,  		//		1   		4		150 -- 210   
	6,  		//		2   		6		270 -- 330  
	5,  		//		3   		5		210 -- 270      
	2,  		//		4   		2		30 -- 60  
	3,  		//		5   		3		90 -- 150    
	1,  		//		6   		1		330 -- 30  
	-1,			//		7
};

float hall_edge_angle[6] = 
{
		5.759586531f,		//11.0f / 6.0f * M_PI,
		0.523598775f,		//1.0f / 6.0f * M_PI,
		1.570796326f,		//1.0f / 2.0f * M_PI,
		2.617993878f,		//5.0f / 6.0f * M_PI,
		3.665191429f,		//7.0f / 6.0f * M_PI, 
		4.712388980f,		//9.0f / 6.0f * M_PI,
 
};

/**
  ***********************************************************************************************************
  * @brief  ������������ʼ��
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall2angle_params_init(HALL_TO_ANGLE_UDT *pV)
{
    pV->sector = 0;
    pV->last_sector = 0;
    pV->hall_dir = 0;
		pV->error_cnt = 0;
		pV->error_flag = 0;
		pV->cap_cnt_overflow_flag = 0;
}
/**
  ***********************************************************************************************************
  * @brief  ��ʼ��������Ƕ�
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall2angle_electrical_angle_init(HALL_TO_ANGLE_UDT *pV)
{
//    pV->pll_kp = 2000.0f;
//    pV->pll_ki = 20000.0f;
		LB_MotionObsv_Init(&MotionObsv);
	
		//pV->filterK1 = 1.0f/( 1 + PWM_FOC_PERIOD*2*PI*10 );		/* Low-pass cut-off frequency = 10 Hz */
		pV->filterK1 = 1.0f/( 1 + PWM_FOC_PERIOD*2*PI*50 );		/* Low-pass cut-off frequency = 50 Hz */
		pV->filterK2 = 1.0f - pV->filterK1;
		pV->pll_speed_rpm_filter = 0;
	
		pV->capture_clk_period = 1.0f / HALL_CAPTURE_TIMER_CLK;
}
/**
  ***********************************************************************************************************
  * @brief  ����ֵ��������ʼ��
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall2angle_sector_init(HALL_TO_ANGLE_UDT *pV)
{
    pV->last_value = pV->value = HALL_PORTS_CBA & 0x7;
    pV->sector = sector_table[pV->value];
    pV->last_sector = pV->sector;
		motor_hall_sector_angle(pV);
}

/**
  ***********************************************************************************************************
  * @brief  ��ȡ����ֵ�ͻ�������
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall_sector(HALL_TO_ANGLE_UDT *pV)
{
		pV->hall_edgeTime = HALL_CAPTURE_EDGE_CNT;
	
    pV->last_value = pV->value;
    pV->value = HALL_PORTS_CBA & 0x7;
	
    pV->last_sector = pV->sector;
    pV->sector = sector_table[pV->value];
	
	    //�ж�hall�Ƿ����
    if((pV->value == 0 || pV->value == 7))
    {
        pV->error_cnt ++;
        if(pV->error_cnt >= 20)
        {
						pV->error_flag = 1;
            //motor_error_status |= MOTOR_ERROR_ID_WRONGHALL;    // ��������
        }
    }
    else 
    {
        pV->error_cnt --;
        if(pV->error_cnt < 0)
        {
            pV->error_cnt = 0;
        }
    }
}

/**
  ***********************************************************************************************************
  * @brief  ���ݻ����ź��жϵ��ת��
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall_sector_direction(HALL_TO_ANGLE_UDT *pV)
{
    int8_t sector_increment=0;                                // ��������

    sector_increment = pV->sector - pV->last_sector;        // ��������ǰ����

    if(sector_increment != 0)                                 // �����ı�
    {
        pV->new_sector_flg = 1;                              // ������������ı䣬������������־λ
        
        switch(sector_increment)
        {
            // ��ת��CCW��������ʱ��
            case 1:
            case -5:
                pV->hall_dir = MOTOR_TURN_CCW;               // �赱ǰת���ʶΪ��ת��CCW
								HALL_CAPTURE_CNT = 0;												// if the sector is changed correctly, clear the capture timer
            break;
            // ��ת��CW������˳ʱ��
            case -1:
            case 5:                   
                pV->hall_dir = MOTOR_TURN_CW;
								HALL_CAPTURE_CNT = 0;												// if the sector is changed correctly, clear the capture timer
            break;
            // 3.��������(Ԥ��)
            default:
								pV->hall_dir = MOTOR_TURN_UCW;
            break; 
        }
    }
			  //�ж�hall�Ƿ����
    if((pV->hall_dir == MOTOR_TURN_UCW))
    {
        pV->error_cnt ++;
        if(pV->error_cnt >= 20)
        {
						pV->error_flag = 1;
            //motor_error_status |= MOTOR_ERROR_ID_WRONGHALL;    // ��������
        }
    }
    else 
    {
        pV->error_cnt --;
        if(pV->error_cnt < 0)
        {
            pV->error_cnt = 0;
        }
    }
    return;
}
/**
  ***********************************************************************************************************
  * @brief  calculate the angle of hall sector edge according to the rotating direction
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall_sector_angle(HALL_TO_ANGLE_UDT *pV)  
{
		 if( pV->sector > 0 )
		 {
				switch(pV->hall_dir){
					case MOTOR_TURN_CCW:
						pV->hall_edgeAngle = hall_edge_angle[ pV->sector - 1 ];
						break;
					case MOTOR_TURN_CW:
						pV->hall_edgeAngle = hall_edge_angle[ (pV->sector > 5) ? 0 : pV->sector ];
						break;
					default:
						pV->hall_edgeAngle = hall_edge_angle[ pV->sector - 1 ] + 0.523598775f;		//	pi/6 = 0.523598775f
						break;
				}
		 }
}
/**
  ***********************************************************************************************************
  * @brief  in the CAP IRQHandler, calculate the angle of hall sector edge according to the rotating direction
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */   
void motor_hall_speed_calc(HALL_TO_ANGLE_UDT *pV)  
{	
		if ( pV->cap_cnt_overflow_flag == 1 ){			// if the cap cnt is overflow, the speed should be 0;
				pV->cap_cnt_overflow_flag = 0;					// in the next cap interrupt, calculate speed
				pV->cap_speed_rad_s_abs = 0;
				pV->cap_speed_rad_s = 0;
				pV->cap_speed_rad_s_filter = 0;
		}
		else{
				if ( (pV->sector > 0) && (pV->hall_dir != MOTOR_TURN_UCW) ){
						pV->cap_speed_rad_s_abs = (float)HALL_CAPTURE_RAD_S_SCALE / pV->hall_edgeTime;
						pV->cap_speed_rad_s = pV->hall_dir * pV->cap_speed_rad_s_abs;
				}
		}
}

/**
  ***********************************************************************************************************
  * @brief  in the CAP IRQHandler, calculate the speed in sector 1
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */   
void motor_hall_circle_speed_calc(HALL_TO_ANGLE_UDT *pV)  
{	
		pV->circle_freq = (float)HALL_CIRCLE_TIMER_CLK / pV->circle_period_cnt;
		pV->circle_speed_rad_s = 2 * PI * pV->hall_dir * pV->circle_freq;
}

//// �Ƕ����ƣ����໷����ĽǶ���Ҫ������-PI~PI֮��
//void motor_hall_sensor_utils_norm_angle_rad(float *angle) 
//{
//	while (*angle < -M_PI) 
//    {
//		*angle += 2.0f * M_PI;
//	}

//	while (*angle >  M_PI) 
//    {
//		*angle -= 2.0f * M_PI;
//	}
//}
//// �������໷��������ǶȺͻ����ٶ�
//void motor_hall_sensor_pll_run(float phase, float dt, volatile float *phase_var, volatile float *speed_var) 
//{
//    float delta_theta = 0;
//    delta_theta = phase - *phase_var;                         // ����ǶȲ�ֵ
//    motor_hall_sensor_utils_norm_angle_rad(&delta_theta);            // �淶�Ƕȷ�Χ
//    *phase_var += (*speed_var + hall.pll_kp * delta_theta) * dt;
//    motor_hall_sensor_utils_norm_angle_rad((float*)phase_var);
//    *speed_var += hall.pll_ki * delta_theta * dt;
//}
uint16_t AngleMode = 0;
void motor_hall_to_angle_cal(HALL_TO_ANGLE_UDT *pV)
{
		float TmpAngle;
		// filtering the capture speed
		pV->cap_speed_rad_s_filter = pV->filterK1 * pV->cap_speed_rad_s_filter + pV->filterK2 * pV->cap_speed_rad_s;
		pV->circle_speed_rad_s_filter = pV->filterK1 * pV->circle_speed_rad_s_filter + pV->filterK2 * pV->circle_speed_rad_s;
	
		// calculate the raw output angle
		if ( myabs(pV->cap_speed_rad_s_filter) < MOTOR_MIN_HALL_SPEED_RPM * MOTOR_POLE_PAIRS * 0.2f ){	// MinSpeed * PolePairs * 2PI/60 * 2 
				pV->raw_angle_rad = pV->hall_edgeAngle;
				pV->pll_angle_rad = pV->raw_angle_rad;
				pV->pll_speed_rad_s = pV->cap_speed_rad_s_filter;  
		} 
		else {
				pV->capture_time = (float)HALL_CAPTURE_CNT * pV->capture_clk_period;
				pV->raw_angle_rad = pV->hall_edgeAngle + pV->cap_speed_rad_s_filter * pV->capture_time;
				
				// the estimated angle should be within (hall_edgeAngle +/- PI/3), the hall_edgeAngle is updated in caputre IRQHandler
				if( pV->raw_angle_rad > pV->hall_edgeAngle + PI/3 )
						pV->raw_angle_rad = pV->hall_edgeAngle + PI/3;
				else if( pV->raw_angle_rad < pV->hall_edgeAngle - PI/3 )
						pV->raw_angle_rad = pV->hall_edgeAngle - PI/3;
				
				// the estimated angle within 0 -- 2PI
				if( pV->raw_angle_rad > 2*PI )
						pV->raw_angle_rad -= 2*PI;
				else if ( pV->raw_angle_rad < 0 )
						pV->raw_angle_rad += 2*PI;
				
				pV->circle_time_cnt = HALL_CIRCLE_CNT;
				pV->circle_angle_calib_sum += pV->circle_angle_calib_delta;
				pV->raw_angle_rad_test = pV->raw_angle_rad_test + pV->circle_speed_rad_s_filter * (float)PWM_FOC_PERIOD - pV->circle_angle_calib_delta; 

				while( pV->raw_angle_rad_test > 2*PI )
						pV->raw_angle_rad_test -= 2*PI;
				while( pV->raw_angle_rad_test < 0 )
						pV->raw_angle_rad_test += 2*PI;
				
				// filltering the estimated angle with PLL
//				TmpAngle = pV->raw_angle_rad;
//				motor_hall_sensor_utils_norm_angle_rad(&TmpAngle);
//				motor_hall_sensor_pll_run(TmpAngle, PWM_FOC_PERIOD, &( pV->pll_angle_rad ), &( pV->pll_speed_rad_s ));
				
				// filltering the estimated angle with luenberger motion observer
				if( AngleMode == 0 )
						MotionObsv.ActTheta = pV->raw_angle_rad;  // 0 -- 2*pi
				else
						MotionObsv.ActTheta = pV->raw_angle_rad_test;
				MotionObsv.TE = 0;
				LB_MotionObsv_Cal(&MotionObsv);
				pV->pll_angle_rad = MotionObsv.EstTheta;
				pV->pll_speed_rad_s = MotionObsv.EstSpd_Filt;
				pV->pll_speed_rpm = pV->pll_speed_rad_s * 30.0f / (PI * MOTOR_POLE_PAIRS);
				pV->pll_speed_rpm_filter = pV->filterK1 * pV->pll_speed_rpm_filter + pV->filterK2 * pV->pll_speed_rpm;
		}
			
}

 

/**
  ***********************************************************************************************************
  * @brief  ���������жϴ�������
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void HALL_CAPTURE_IRQHandler(void)
{
    uint8_t i = 0;
		float TimeDelta;
    // ����ж�
    if(tmr_flag_get(HALL_CAPTURE_TIMER, TMR_OVF_FLAG) != RESET)
    {
        tmr_flag_clear(HALL_CAPTURE_TIMER, TMR_OVF_FLAG);                             // �������жϱ�־
				hall2angle.cap_cnt_overflow_flag = 1;
				hall2angle.cap_speed_rad_s_abs = 0;								// if the cap cnt is overflow, the speed should be 0;
				hall2angle.cap_speed_rad_s = 0;
				hall2angle.cap_speed_rad_s_filter = 0;
    } 
    // �����ж�
    if(tmr_flag_get(HALL_CAPTURE_TIMER, TMR_TRIGGER_FLAG|TMR_C1_FLAG) != RESET)       // ��������������ͨ��1�ж�
    {
        tmr_flag_clear(HALL_CAPTURE_TIMER, TMR_TRIGGER_FLAG|TMR_C1_FLAG|TMR_OVF_FLAG);// ����жϱ�־
			
				motor_hall_sector(&hall2angle);
				motor_hall_sector_direction(&hall2angle);
				motor_hall_sector_angle(&hall2angle);
				motor_hall_speed_calc(&hall2angle);
				
				if(hall2angle.sector == 1){
					hall2angle.circle_period_cnt = HALL_CIRCLE_CNT;
					HALL_CIRCLE_CNT = 0;									
					motor_hall_circle_speed_calc(&hall2angle);
					//calculate the error angle
					TimeDelta = (float)(hall2angle.circle_period_cnt - hall2angle.circle_time_cnt) * HALL_CIRCLE_TIMER_PERIOD;
					hall2angle.circle_angle_init = hall2angle.raw_angle_rad_test + hall2angle.circle_speed_rad_s_filter * TimeDelta;	
					if( hall2angle.circle_angle_init > 2*PI )
							hall2angle.circle_angle_init -= 2*PI;
					else if( hall2angle.circle_angle_init < 0 )
							hall2angle.circle_angle_init += 2*PI;
					
					hall2angle.circle_angle_error = hall2angle.circle_angle_init - hall2angle.hall_edgeAngle;
					if( hall2angle.circle_angle_error > PI )
						hall2angle.circle_angle_error -= 2*PI;
					else if( hall2angle.circle_angle_error < -PI )
						hall2angle.circle_angle_error += 2*PI;
					//calibration angle = angle error / ( PWM_freq / FOC_freq )
					hall2angle.circle_angle_calib_delta = hall2angle.circle_angle_error * hall2angle.circle_freq / (float)PWM_TIM_FREQ;
					hall2angle.circle_angle_calib_sum = 0;					
				}
    }
}



