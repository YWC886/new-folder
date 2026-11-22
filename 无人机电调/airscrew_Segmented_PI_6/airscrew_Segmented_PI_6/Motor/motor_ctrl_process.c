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
#include "motor_ctrl_process.h"

/**
  ***********************************************************************************************************
  * ��������
  * ********************************************************************************************************* 
  */ 
MOTOR_CTRL_STATE_UDT motor_ctrl_state;    // ����״̬��
MOTOR_ERROR_ID_UDT   motor_error_status;  // ����״̬
MOTOR_RUN_FLG_UDT    motor_run_status;    // ����״̬
MOTOR_CTRL_REF_UDT   motor_ctrl_ref;      // ���Ƹ���

MOTOR_CTRL_SET_UDT   motor_ctrl_duty_set;
MOTOR_CTRL_SET_UDT   motor_ctrl_speed_set;
MOTOR_CTRL_SET_UDT   motor_ctrl_torque_set;
MOTOR_CTRL_SET_UDT   motor_ctrl_position_set;
uint8_t              motor_ctrl_mode;
uint8_t              motor_ctrl_wave_mode;
 
uint8_t              motor_run_flg;
#define CCR_TABLE  {0x00001041,0x00001401,0x00001410,0x00001014,0x00001104,0x00001140}
s16 BLDC_Duty;    // ��ˢ��������� Q12 : 0 -- 100% : 0 -- 4096
uint32_t TIMx_CCER_Table[6] = CCR_TABLE;

uint8_t              motor_run_mode;
uint8_t              positon_cmd_source;
uint8_t              brake_flg;

uint8_t              iap_flag;
uint8_t              timer_1ms_Flag = 0;

extern S_CAN_MSG_ESC_STAT1  CanData_Stat_1;

extern float velocity_kp;
extern float velocity_ki;

 

float pwm_to_ref_velocity(uint16_t pwm)
{
	float y;
	y = (float)pwm;	      //k = 0.006347   b = 0.129 , pwm->ref_velocity   
  if (y < CMD_START_TH)
	//if (y < 14.0f)
	{ 
		y = 0;
	}
	else
	{		
		if (y < 30.0f)
		{
			y *= 0.0105f;
		}
		else
		{			
			if ( y < 44.0f)
			{
				y *= 0.008038f;    // y = 0.008038 * x + 0.0784
				y += 0.0784f;
			}
			else
			{
				if (y < 68.0f)
				{
					y *= 0.006313f;    // y = 0.006313 * x + 0.154268
					y += 0.154268f;
				}
				else
				{			
					y *= 0.0056325f;    // y = 0.0056325 * x + 0.20055
					y += 0.20055f;
				}				
			}
		}
	}

	return (y);
}

float ADDVAL = 0.0004f; 
uint8_t StartVoerFlag = 0;
uint16_t StartTime = 0, Esc_Cmd = 0;
 
/**
  ***********************************************************************************************************
  * @brief  ����״̬��ѭ������systick�ж�����ã�����1ms
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */
          

void motor_ctrl_state_loop(void)
{
    
    motor_volt_bus();                                                // �ɼ���ѹ
    motor_ctrl_start_stop();                                         // ��ͣ����
    motor_speed_dac_update(hall2angle.pll_speed_rpm_filter);        //ת���������1khz

    switch (motor_ctrl_state)
    {
      case MOTOR_CTRL_SM_INIT:                                     // ϵͳ��ʼ��
        
			motor_ctrl_state_init();                             // ����״̬��ʼ��
        
			motor_ctrl_state = MOTOR_CTRL_SM_STOP;
        break;

        case MOTOR_CTRL_SM_ZERO_CHECK:

            motor_ctrl_state = MOTOR_CTRL_SM_STOP;
            break;

        case MOTOR_CTRL_SM_STOP:
            motor_run_flg = 0;

            if(motor_run_status.bits.start == 1)
            {
                motor_run_status.bits.start = 0;
                motor_ctrl_state = MOTOR_CTRL_SM_START;
            }
            break;
        
        case MOTOR_CTRL_SM_START:

            motor_run_flg = 1;       
        

		        current.id_demand = 0.0f;
            current.iq_demand = 0.0f;
            if(motor_current_offset())                               // �ɼ������ƫ��ֵ����ܴ�PWM���ƣ���ֹPWMӰ���ʼ�����ɼ�
            {
                motor_run_status.bits.enable = 1;                    // դ������ʹ��
                motor_ctrl_start_pwm();                              // ʹ��PWM��ʱ������
                motor_ctrl_state = MOTOR_CTRL_SM_NORMAL_OPERATION;   // ״̬�л�����������ģʽ

                                  
            }
            break;
        
        case MOTOR_CTRL_SM_MOTOR_STATE_IDENTIFICATION:               // λ��У׼���ܳ�Ʒ��ֱ�������������ڣ�������ȡ��


            break;
        
        case MOTOR_CTRL_SM_BOOTSTRAP:

            break;
        
        case MOTOR_CTRL_SM_ROTOR_POSITION_IDENTIFICATION:

            break;
        
        case MOTOR_CTRL_SM_TRANSITION:

            break; 
        
        case MOTOR_CTRL_SM_NORMAL_OPERATION:
					
					
          Esc_Cmd = CanData_Stat_1.esc_cmd;
				
          if (StartVoerFlag == 0)
          {  
            Esc_Cmd = 14;              
            if (myabs(velocity.real_velocity) > 0.13 )  //����˦���ٶ�650rpm,ά��1s
            {
              if (++StartTime >= 1000)
              {
                StartTime = 0;
                StartVoerFlag = 1;                
              }
            }                   
          }              

          float set_spd = pwm_to_ref_velocity(Esc_Cmd);
          if (set_spd > 0.23) ADDVAL = 0.0012;  else ADDVAL = 0.0004;        // 1150rpm     
          motor_ctrl_ref.velocity = SPEED_DIR * set_spd;               
          
          SinSignal.Amp = 0.005;
          SinSignal.freq = 1;
          SinSignal.Ts = 0.001;
//					SinSignal.Enable = 1;
          SinSig_Cal(&SinSignal);
          motor_ctrl_speed_set.target = motor_ctrl_ref.velocity + SinSignal.out;

          motor_ctrl_speed_set.acc = ADDVAL;//0.0012;                   // reach 1500rpm in 500ms
          motor_ctrl_speed_set.dec = ADDVAL;//0.0012;

          if( hall2angle.pll_speed_rpm > MOTOR_MAX_HALL_SPEED_RPM )
          {
              motor_ctrl_speed_set.acc = 0.000;       // when speed bigger than the max, the speedRef cannot increase
              motor_ctrl_speed_set.dec = ADDVAL;//0.0012;
          }
          else if ( hall2angle.pll_speed_rpm < -MOTOR_MAX_HALL_SPEED_RPM )
          {
              motor_ctrl_speed_set.acc = ADDVAL;//0.0012;				// when speed smaller than the minus max, the speedRef cannot decrease
              motor_ctrl_speed_set.dec = 0.000;
          }

          motor_ctrl_speed_set.present = motor_ctrl_ramp_set(motor_ctrl_speed_set, 0);
          velocity.demand_velocity = motor_ctrl_speed_set.present;								
          //foc.v_q = motor_ctrl_speed_set.present;          

          float set_demand_velocity = myabs(velocity.demand_velocity);             
          
          //---------------------------------------------------------------------------------------------
//          if( set_demand_velocity < 0.01 )
//          {
//            velocity_pid.kp =0.2;
//            velocity_pid.ki = 0.001;
//            velocity_pid.sum = 0;			// intergration term
//          }
//          else 
          {              
            if( set_demand_velocity < 0.18)  //900rpm    
            { 
              velocity_pid.kp = 4.2;
              velocity_pid.ki = 0.004;
              velocity_pid.sum = 0;			// intergration term
            }
            else
            {
              if( set_demand_velocity < 0.2)  //1000rpm      
              { 
//                velocity_pid.kp = set_demand_velocity * 220 - 35.4f; //Kp=24
//                velocity_pid.ki = 0.002;
//                velocity_pid.sum = 0;			// intergration term
                
                velocity_pid.kp = set_demand_velocity * 86.67 - 11.4f; //Kp=12
                velocity_pid.ki = 0.002;
//                velocity_pid.sum = 0;			// intergration term
                
//                velocity_pid.kp = set_demand_velocity * 42.22 - 3.4f; //Kp=8
//                velocity_pid.ki = 0.002;
                
//                velocity_pid.kp = set_demand_velocity * 20 + 0.6;    //Kp=6
//                velocity_pid.ki = 0.002;
                //velocity_pid.sum = 0;			// intergration term
              }
              else
              {
                velocity_pid.kp = 12;//velocity_kp;
                velocity_pid.ki = velocity_ki;                
              }              
            }
          }          	
          break;

        case MOTOR_CTRL_SM_ERROR:

        break;
        
        case MOTOR_CTRL_SM_IDLE:

        break;
		
        case MOTOR_CTRL_SM_RAMP_DOWN:                        // ����ͣ��ģʽ
            motor_ctrl_speed_set.target = 0;                 // ���ٶ��趨ֵ����Ϊ0
            motor_ctrl_speed_set.acc = 50;                   // ���ݼӼ���б��ʹ��ǰ�ٶȽ�Ϊ0
            motor_ctrl_speed_set.dec = 50;
            motor_ctrl_speed_set.present = motor_ctrl_ramp_set(motor_ctrl_speed_set, 50);
            velocity.demand_velocity = motor_ctrl_speed_set.present;
            //if(velocity.abs_real_velocity < 100)             // �˴���100���Ի��ɲ���������Ϊ��С�����ٶ�
            {
                    motor_ctrl_stop_pwm();                       // ����ͣ��ʱ����б�¼���ͣ��
                    motor_ctrl_state = 0;                        // ��״̬���л���ͣ��ģʽ
            }
        break;

        default:
        break;

    }

    if (motor_error_status != 0U)
    {
        motor_ctrl_state = MOTOR_CTRL_SM_ERROR;
    }
    if(motor_run_status.bits.stop == 1)
    {
				//BRAKE_BAO_JIN;
				brake_flg = 0;
        motor_run_status.bits.stop = 0;
        if (motor_ctrl_state > 0U)           
        {
            motor_ctrl_state = MOTOR_CTRL_SM_STOP;
        }
    }
    if(motor_run_status.bits.disable == 1)
    {
        motor_run_status.bits.disable = 0;                   // ��⵽OFF2����ͣ��ָ�����ͣ����һ�����ڹ���ͣ��
        motor_ctrl_speed_set.present = 0;
        motor_run_status.all = 0x0;															// clear all the status flag bit
        
        motor_ctrl_stop_pwm();                               // ͣ��ʱӦ�ر�PWM
        motor_ctrl_state = MOTOR_CTRL_SM_INIT;//MOTOR_CTRL_SM_STOP;               // �κ�ʱ������ͣ��������״̬���л�������ģʽ

    }
 
    
}

/**
  ***********************************************************************************************************
  * @brief  ����״̬��ʼ��
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_ctrl_state_init(void)
{
    motor_run_status.bits.enable = 0;
    motor_ctrl_wave_mode = MOTOR_CTRL_MODE_VECTER;
    motor_ctrl_mode = MOTOR_CTRL_SPEED_MODE;
    motor_ctrl_stop_pwm();

	  motor_hall_sensor_electrical_angle_init();//
	  motor_hall_sensor_sector_init();//
	  motor_foc_init();//
    motor_pid_init(); //
    motor_current_init();//
    motor_velocity_init();//
	
		motor_volt_temp_filter_init();//
		field_weakening_init(&fw_ctrl);//
    
		motor_hall2angle_params_init(&hall2angle);//
		motor_hall2angle_electrical_angle_init(&hall2angle);//
		motor_hall2angle_sector_init(&hall2angle);//
	
		LowPassFilter_Init(&LPF_100Hz_UqMax);//
}

/**
  ***********************************************************************************************************
  * @brief  ����״̬����ֻ����ͣ��ģʽʱ�����л�������ģʽ
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_ctrl_state_start(void)
{
    if (motor_ctrl_state == MOTOR_CTRL_SM_STOP)
    {
        motor_ctrl_state = MOTOR_CTRL_SM_START;
    }
}

/**
  ***********************************************************************************************************
  * @brief  ͣ��״̬�����κη�ͣ��ģʽ�������л���ͣ��״̬
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_ctrl_state_stop(void)
{
    if (motor_ctrl_state > 0U)             
    {
        motor_ctrl_state = MOTOR_CTRL_SM_STOP;       
    }
}

/**
  ***********************************************************************************************************
  * @brief  ���Ŀ��ƻ�����ADC�����ж������
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
extern float angle_read_back;


u32 ind = 0;
uint8_t MeasFlag = 0;

float TestMotorFK_Spd = 0.0;
 
 
void motor_ctrl_loop(void)
{ 
        
		motor_hall_to_angle_cal(&hall2angle);
		motor_current_read(MOTOR_CURRENT_SAMP_MODE);    // ���ݵ�����������ʽ����
	
    if(motor_run_status.bits.enable == 1)
    {
			if(motor_run_status.bits.OpenLoop == 1){
				motor_open_loop();
			}
			else if (motor_run_status.bits.SpdLoop == 1){
				motor_speed_ctrl();
			}		
    }
    
    TestMotorFK_Spd = velocity.abs_real_velocity * BASE_SPEED; 
}
 
/**
  ***********************************************************************************************************
  * @brief  ����PWM
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_ctrl_start_pwm(void)
{
 
  PWM_DUTY_U = PWM_TIM_PULSE>>1;
  PWM_DUTY_V = PWM_TIM_PULSE>>1;
  PWM_DUTY_W = PWM_TIM_PULSE>>1;  
	
//	tmr_output_enable(TMR1, TRUE);
  
  gpio_init_type         gpio_init_struct;
  
  gpio_init_struct.gpio_pins = GPIO_PINS_8 | GPIO_PINS_9 | GPIO_PINS_10;      // PWM�Ϲ����ų�ʼ��
  gpio_init_struct.gpio_mode = GPIO_MODE_MUX;                                 // �������Ÿ��ù���
  gpio_init_struct.gpio_out_type = GPIO_OUTPUT_PUSH_PULL;                     // �������
  gpio_init_struct.gpio_pull = GPIO_PULL_NONE;                                // ��������
  gpio_init_struct.gpio_drive_strength = GPIO_DRIVE_STRENGTH_STRONGER;        // ǿ����ģʽ
  gpio_init(GPIOA, &gpio_init_struct);

  
  gpio_init_struct.gpio_pins = GPIO_PINS_13 | GPIO_PINS_14 | GPIO_PINS_15;    // PWM�¹����ų�ʼ��                                 
  gpio_init(GPIOB, &gpio_init_struct);  
 
}

/**
  ***********************************************************************************************************
  * @brief  �ر�PWM
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_ctrl_stop_pwm(void)
{
//		tmr_output_enable(TMR1, FALSE);
		
    gpio_init_type         gpio_init_struct;
  
    PWM_DUTY_U = 0;
    PWM_DUTY_V = 0;
    PWM_DUTY_W = 0;
  
    gpio_init_struct.gpio_pins = GPIO_PINS_8 | GPIO_PINS_9 | GPIO_PINS_10;      // PWM�Ϲ����ų�ʼ��
    gpio_init_struct.gpio_mode = GPIO_MODE_INPUT;//GPIO_MODE_MUX;                                 // �������Ÿ��ù���
    gpio_init_struct.gpio_out_type = GPIO_OUTPUT_PUSH_PULL;                     // �������
    gpio_init_struct.gpio_pull = GPIO_PULL_NONE;                                // ��������
    gpio_init_struct.gpio_drive_strength = GPIO_DRIVE_STRENGTH_STRONGER;        // ǿ����ģʽ
    gpio_init(GPIOA, &gpio_init_struct);

    gpio_init_struct.gpio_pins = GPIO_PINS_13 | GPIO_PINS_14 | GPIO_PINS_15;    // PWM�¹����ų�ʼ��
    gpio_init(GPIOB, &gpio_init_struct); 
}

/**
  ***********************************************************************************************************
  * @brief  ��ͣ����ʵ�ֺ�������systick�ж�����ã�����1ms,���Ը���ʵ�ʿ����ź�ѡ�񣬰�����ͨ�ŵ�
  *         ������Ʒ�ʽ��Ϊ�������ƣ�ʹ�ú��ַ�ʽ��������ʹ����ͬ��ʽͣ������֧�ַ�ʽ����
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
uint8_t enable_modbus_ctrl;
uint8_t enable_usb_ctrl;
uint8_t disable_key_flg;
void motor_ctrl_start_stop(void)
{ 
 
	if ((CanData_Stat_1.esc_cmd >= CMD_START_TH) && (motor_run_flg == 0))	
	{
		motor_run_status.bits.start = 1;
		motor_run_flg = 1; 
		motor_run_status.bits.SpdLoop = 1;
	}	
  else
	{
		if ((CanData_Stat_1.esc_cmd <= CMD_STOP_TH) && (motor_run_flg == 1))		
		{			
			motor_run_status.bits.disable = 1;
			motor_run_flg = 0;
			motor_run_status.bits.SpdLoop = 0;
      StartTime = 0;
      StartVoerFlag = 0;
		}
	}		   
}
/**
  ***********************************************************************************************************
  * @brief  б�º���
  * @param  ��ǰֵ��Ŀ��ֵ������������
  * @retval ��ǰֵ
  * ********************************************************************************************************* 
  */ 
float motor_ctrl_ramp_change(float ramp_now, float ramp_target, float ramp_inc, float ramp_dec)
{
    // б�µ���
    if(ramp_now < ramp_target)
    {
        ramp_now += ramp_inc;
        if(ramp_now >= ramp_target)
            ramp_now = ramp_target;
    }
    // б�µݼ�
    else // if(ramp_now > ramp_target)
    {
        ramp_now -= ramp_dec;
        if(ramp_now <= ramp_target)
            ramp_now = ramp_target;
    }
    return ramp_now;
}

/**
  ***********************************************************************************************************
  * @brief  б���趨
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
float motor_ctrl_ramp_set(MOTOR_CTRL_SET_UDT set, uint8_t cnt)
{
    static uint8_t execution_frequency;
    if(++execution_frequency >= cnt)
    {
        execution_frequency = 0;
        set.present = motor_ctrl_ramp_change(set.present, set.target, set.acc, set.dec);
    }
    return set.present;
}
/**
  ***********************************************************************************************************
  * @brief  ADC�жϣ�����������ƺ����߼�
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void ADC1_2_IRQHandler(void)
{
    if(adc_flag_get(ADC1, ADC_PCCE_FLAG) != RESET)
    {	
		adc_flag_clear(ADC1, ADC_PCCE_FLAG);
		motor_ctrl_loop();
    }
    if(adc_flag_get(ADC2, ADC_PCCE_FLAG) != RESET)
    {
		adc_flag_clear(ADC2, ADC_PCCE_FLAG);
    }
}
/**
  ***********************************************************************************************************
  * @brief  systick�жϣ�����״̬���ȵ�Ƶ�¼��߼�
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 

void SysTick_Handler(void)
{
	motor_ctrl_state_loop();     
	timer_1ms_Flag = 1;	
}

 


 

 





