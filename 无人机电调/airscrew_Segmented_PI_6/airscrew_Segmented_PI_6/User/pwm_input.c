/**
  ***********************************************************************************************************
 
  ***********************************************************************************************************
  */
 
 
#include "pwm_input.h"

 

extern S_CAN_MSG_ESC_STAT1  CanData_Stat_1;
uint32_t t_global;
PWM pwm = PWM_DEF;

uint32_t T2_C1DT_Val = 0;
uint16_t PWM_Thr_Loss_Time = 0;
 


/* TIM6 ����ģʽ��ʼ�� -------------------------------------------- */
void tmr6_Count_config(void)
{
	crm_periph_clock_enable(CRM_TMR6_PERIPH_CLOCK, TRUE);      // ʹ��TMR6ʱ��
	tmr_reset(TMR6);
   //tmr_32_bit_function_enable(TMR6, TRUE);
   tmr_base_init(TMR6, 2400*3, TMR_CHANNEL_INPUT_DIV_1);  // TMR6��Ƶ0����������	
	 tmr_cnt_dir_set(TMR6, TMR_COUNT_UP);                       // �������ϼ���ģʽ
   tmr_counter_value_set(TMR6, 0);

  tmr_interrupt_enable(TMR6, TMR_OVF_INT, TRUE);             // ʹ������ж�
	nvic_irq_enable(TMR6_GLOBAL_IRQn, 3, 0);  // ��ռ���ȼ�0�������ȼ�0
}

/* TIM2 ����ģʽ��ʼ�� -------------------------------------------- */
void tmr2_Count_config(void)
{
	crm_periph_clock_enable(CRM_TMR2_PERIPH_CLOCK, TRUE);      // ʹ��TMR2ʱ��
	tmr_reset(TMR2);
  tmr_32_bit_function_enable(TMR2, TRUE);
  tmr_base_init(TMR2, 0xFFFFFFFF, TMR_CHANNEL_INPUT_DIV_1);  // TMR2��Ƶ0����������	
	tmr_cnt_dir_set(TMR2, TMR_COUNT_UP);                       // �������ϼ���ģʽ
  tmr_counter_value_set(TMR2, 0);  
}

void PWM_Input_Init(void)
{
  gpio_init_type gpio_init_struct;
  crm_periph_clock_enable(CRM_GPIOB_PERIPH_CLOCK, TRUE);

  gpio_default_para_init(&gpio_init_struct);    
  gpio_init_struct.gpio_pins = GPIO_PINS_3;  
  gpio_init_struct.gpio_mode = GPIO_MODE_INPUT;
  gpio_init_struct.gpio_pull = GPIO_PULL_NONE;
  gpio_init(GPIOB, &gpio_init_struct);

  // �� PB3 ӳ�䵽 EXTI Line3
  gpio_exint_line_config(GPIO_PORT_SOURCE_GPIOB, GPIO_PINS_SOURCE3);

  // ���� EXTI
  exint_init_type exint_init_struct;
  exint_default_para_init(&exint_init_struct);
  exint_init_struct.line_enable = TRUE;
  exint_init_struct.line_mode = EXINT_LINE_INTERRUPUT;    // �ж�ģʽ
  exint_init_struct.line_select = EXINT_LINE_3;           // EXTI Line3 ��Ӧ PB3
  exint_init_struct.line_polarity = EXINT_TRIGGER_BOTH_EDGE; // ˫���ش��� (������)
  exint_init(&exint_init_struct);

  exint_interrupt_enable(EXINT_LINE_3, TRUE);

  // PB3 ��Ӧ EXTI Line3��ʹ�� EXINT3_IRQn
   nvic_irq_enable(EXINT3_IRQn, 0, 0);  // ��ռ���ȼ�0�������ȼ�0

  tmr2_Count_config();   
	tmr6_Count_config();
}


// �жϷ�����
void EXINT3_IRQHandler(void)
{
  uint32_t t;
  if(exint_interrupt_flag_get(EXINT_LINE_3) != RESET)
  {
    exint_flag_clear(EXINT_LINE_3);

    t = tmr_counter_value_get(TMR2);// ��ȡT2ʱ�����  1ms�ļ���ֵΪ240000
    t_global=t;
		tmr_counter_value_set(TMR2, 0);
		
		pwm.Th += t;
		if (pwm.Th > 1950 * 240) 
		{
			pwm.Th = 1950 * 240;			
			
		}
		
		// �����ж�
		if(gpio_input_data_bit_read(GPIOB, GPIO_PINS_3) == SET)
		{ // ������				
			tmr_counter_enable(TMR6, FALSE); 
			tmr_counter_value_set(TMR6, 0);          // TMR4����
			
			if (pwm.StopFlag == 1)
			{
				pwm.StopFlag = 0;
			 tmr_counter_enable(TMR2, TRUE);
			}
			
		}
    else
    { // �½���   
      //pwm.Th += t;
			tmr_counter_value_set(TMR6, 0);          // TMR4����
			tmr_counter_enable(TMR6, TRUE); 
    }     
  }
}

 

/**
  ***********************************************************************************************************
  * @brief  TMR6����жϴ�������
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void TMR6_GLOBAL_IRQHandler(void)
{
	// ����ж�
	if(tmr_flag_get(TMR6, TMR_OVF_FLAG) != RESET)
	{
		tmr_flag_clear(TMR6, TMR_OVF_FLAG);      // �������жϱ�־
		tmr_counter_enable(TMR6, FALSE);         // ��ֹTMR4
		tmr_counter_value_set(TMR6, 0);          // TMR4����

		tmr_counter_enable(TMR2, FALSE);         // ��ֹTMR2		 
		tmr_counter_value_set(TMR2, 0);          // TMR2���� 
		
 
		
		T2_C1DT_Val = pwm.Th / 240;  //�ߵ�ƽʱ�䣬��λus


		pwm.Th = 0;
		pwm.Tl= 0;	 
		pwm.StopFlag = 1;
		
				
		if (T2_C1DT_Val > 1950) T2_C1DT_Val = 1040;
		if (T2_C1DT_Val < 1040) T2_C1DT_Val = 1040;    
    
		
		CanData_Stat_1.esc_cmd = (T2_C1DT_Val - 1040) / 9; //1040~1940us ��Ӧ�� 0% ~ 100%
    
 

		if (CanData_Stat_1.esc_cmd > 95) CanData_Stat_1.esc_cmd = 95;
		CanData_Stat_1.esc_mode.bit.pwm_thr_online = 1;
		PWM_Thr_Loss_Time = 0;	 
		
	}     
}
 

