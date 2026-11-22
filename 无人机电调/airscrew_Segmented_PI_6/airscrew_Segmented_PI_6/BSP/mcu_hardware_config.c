#include "motor_all_header.h"
 

void mcu_peripheral_init(void)
{
    system_clock_config();                                          // ϵͳʱ�����ã�240M�ڲ�����ʱ��                                                        
    systick_clock_source_config(SYSTICK_CLOCK_SOURCE_AHBCLK_DIV8);  // SYSTICKʱ�ӷ�Ƶ����
    SysTick_Config(system_core_clock/1000);                         // SYSTICK����Ϊ1ms�ж�һ��
    nvic_priority_group_config(NVIC_PRIORITY_GROUP_4);
    timer5_init();
    pwm_init();
    hall_init();
    adc_config();	   
    PWM_Input_Init();	 
    can_configuration(); 
    speed_dac_output_init();	
}
void timer5_init(void)
{
	crm_periph_clock_enable(CRM_TMR5_PERIPH_CLOCK, TRUE);                       // ʹ��TMR5ʱ��
	tmr_32_bit_function_enable(TMR5, TRUE);
	tmr_base_init(TMR5, 0xFFFFFFFF, TIMER5_12_DIV-1);                                      // TMR1��Ƶ0����������
	
	tmr_counter_value_set(TMR5, 0);
	tmr_counter_enable(TMR5, TRUE);                                              // ʹ��TMR5	
}

void pwm_init(void)
{
    gpio_init_type         gpio_init_struct;
    tmr_output_config_type tmr_output_struct;
    tmr_brkdt_config_type  tmr_brkdt_config_struct;
    crm_periph_clock_enable(CRM_TMR1_PERIPH_CLOCK, TRUE);                       // ʹ��TMR1ʱ��
    crm_periph_clock_enable(CRM_GPIOA_PERIPH_CLOCK, TRUE);                      // ʹ��GPIOAʱ��
    crm_periph_clock_enable(CRM_GPIOB_PERIPH_CLOCK, TRUE);                      // ʹ��GPIOBʱ��

    gpio_init_struct.gpio_pins = GPIO_PINS_8 | GPIO_PINS_9 | GPIO_PINS_10;      // PWM�Ϲ����ų�ʼ��
    gpio_init_struct.gpio_mode = GPIO_MODE_MUX;                                 // �������Ÿ��ù���
    gpio_init_struct.gpio_out_type = GPIO_OUTPUT_PUSH_PULL;                     // �������
    gpio_init_struct.gpio_pull = GPIO_PULL_NONE;                                // ��������
    gpio_init_struct.gpio_drive_strength = GPIO_DRIVE_STRENGTH_STRONGER;        // ǿ����ģʽ
    gpio_init(GPIOA, &gpio_init_struct);

    gpio_init_struct.gpio_pins = GPIO_PINS_13 | GPIO_PINS_14 | GPIO_PINS_15;    // PWM�¹����ų�ʼ��
    gpio_init(GPIOB, &gpio_init_struct);

    gpio_init_struct.gpio_pins = GPIO_PINS_12;                                  // break���ų�ʼ��
    gpio_init_struct.gpio_mode = GPIO_MODE_INPUT;                               // ����ģʽ
    gpio_init(GPIOB, &gpio_init_struct);

    tmr_base_init(TMR1, PWM_TIM_PULSE, 0);                                      // TMR1��Ƶ0����������
    tmr_clock_source_div_set(TMR1, TMR_CLOCK_DIV1);                             // ʱ�ӷָ�DIV1�����ָ
    tmr_cnt_dir_set(TMR1, TMR_COUNT_TWO_WAY_1);                                 // ���Ķ��룬���ϱȽ�ƥ��

    tmr_output_default_para_init(&tmr_output_struct);
    tmr_output_struct.oc_mode = TMR_OUTPUT_CONTROL_PWM_MODE_A;                  // PWMģʽ1
    tmr_output_struct.oc_output_state = TRUE;                                   // ͬ�����ʹ��
    tmr_output_struct.occ_output_state = TRUE;                                  // �������ʹ��
    tmr_output_struct.oc_polarity = TMR_OUTPUT_ACTIVE_HIGH;                     // ͬ���������Ч
    tmr_output_struct.occ_polarity = TMR_OUTPUT_ACTIVE_LOW;                     // �����������Ч
    tmr_output_struct.oc_idle_state = FALSE;                                    // ͬ�����״̬��Ч
    tmr_output_struct.occ_idle_state = FALSE;                                   // �����?  �״�?��Ч                
    tmr_output_channel_config(TMR1, TMR_SELECT_CHANNEL_1, &tmr_output_struct);  // ��ʼ������ͨ��1��2��3
    tmr_output_channel_config(TMR1, TMR_SELECT_CHANNEL_2, &tmr_output_struct);
    tmr_output_channel_config(TMR1, TMR_SELECT_CHANNEL_3, &tmr_output_struct);

//    tmr_output_channel_mode_select(TMR1, TMR_SELECT_CHANNEL_1, TMR_OUTPUT_CONTROL_FORCE_LOW);  // force low (AH is low; AL is high), upper and lower leg are close
//    tmr_output_channel_mode_select(TMR1, TMR_SELECT_CHANNEL_2, TMR_OUTPUT_CONTROL_FORCE_LOW);
//    tmr_output_channel_mode_select(TMR1, TMR_SELECT_CHANNEL_3, TMR_OUTPUT_CONTROL_FORCE_LOW);

    tmr_output_struct.oc_mode = TMR_OUTPUT_CONTROL_PWM_MODE_B;                  // PWMģʽ2
    tmr_output_struct.oc_output_state = TRUE;                                   // ͬ�����ʹ��
    tmr_output_struct.occ_output_state = FALSE;                                 // ��������ر�
    tmr_output_struct.oc_polarity = TMR_OUTPUT_ACTIVE_HIGH;                     // ͬ���������Ч
    tmr_output_struct.occ_polarity = TMR_OUTPUT_ACTIVE_LOW;                     // �����������Ч
    tmr_output_struct.oc_idle_state = FALSE;                                    // ͬ�����״̬��Ч
    tmr_output_struct.occ_idle_state = FALSE;                                   // �������״̬��Ч
    tmr_output_channel_config(TMR1, TMR_SELECT_CHANNEL_4, &tmr_output_struct);  // ��ʼ��ͨ��4�����ڴ�����������
    
    tmr_channel_value_set(TMR1, TMR_SELECT_CHANNEL_1, ((uint16_t)PWM_TIM_PULSE)>>1);   // ռ�ձȳ�ʼ��
    tmr_channel_value_set(TMR1, TMR_SELECT_CHANNEL_2, ((uint16_t)PWM_TIM_PULSE)>>1);
    tmr_channel_value_set(TMR1, TMR_SELECT_CHANNEL_3, ((uint16_t)PWM_TIM_PULSE)>>1);
    tmr_channel_value_set(TMR1, TMR_SELECT_CHANNEL_4, (uint16_t)PWM_TIM_PULSE-1);      // �����������ʼ��
    
    tmr_brkdt_default_para_init(&tmr_brkdt_config_struct);
    tmr_brkdt_config_struct.brk_enable = FALSE;                                  // ����break
    tmr_brkdt_config_struct.auto_output_enable = FALSE;                          // ��ֹ�Զ����
    tmr_brkdt_config_struct.deadtime = PWM_DEAD_TIME;                            // ��������ʱ��
    tmr_brkdt_config_struct.fcsodis_state = TRUE;                                // �����������е�ƽ
    tmr_brkdt_config_struct.fcsoen_state = TRUE;
    tmr_brkdt_config_struct.brk_polarity = TMR_BRK_INPUT_ACTIVE_HIGH;            // brk���뼫��Ϊ����Ч���͵�ƽ��������
    tmr_brkdt_config_struct.wp_level = TMR_WP_LEVEL_3;                           // ����3��д����
    tmr_brkdt_config(TMR1, &tmr_brkdt_config_struct);

    tmr_primary_mode_select(TMR1, TMR_PRIMARY_SEL_C4ORAW);                       // ͨ��4�Ƚ��¼����Ϊ�����źţ����ƹ��������

    tmr_output_enable(TMR1, TRUE);                                               // ʹ��PWM���
    tmr_counter_enable(TMR1, TRUE);                                              // ʹ��TMR1
}

void hall_init(void)
{
    gpio_init_type        gpio_init_struct;
	  tmr_input_config_type tmr_input_config_struct;

    crm_periph_clock_enable(HALL_A_GPIO_CRM_CLK, TRUE);                    // ʹ��hall_a����ʱ��
    crm_periph_clock_enable(HALL_B_GPIO_CRM_CLK, TRUE);                    // ʹ��hall_b����ʱ��
    crm_periph_clock_enable(HALL_C_GPIO_CRM_CLK, TRUE);                    // ʹ��hall_c����ʱ��
	  crm_periph_clock_enable(HALL_CAPTURE_CRM_CLK, TRUE);
    gpio_default_para_init(&gpio_init_struct);                             // ��������Ĭ��ֵ

    gpio_init_struct.gpio_drive_strength = GPIO_DRIVE_STRENGTH_STRONGER;   // ��������Ϊǿ����ģʽ
    gpio_init_struct.gpio_mode = GPIO_MODE_INPUT;                          // ����ģʽ
    gpio_init_struct.gpio_pins = HALL_A_GPIO_PIN;                        
    gpio_init_struct.gpio_pull = GPIO_PULL_NONE;                           // ��������
    gpio_init(HALL_A_PORT, &gpio_init_struct);
	
    gpio_init_struct.gpio_pins = HALL_B_GPIO_PIN;                        
    gpio_init(HALL_B_PORT, &gpio_init_struct);
		
    gpio_init_struct.gpio_pins = HALL_C_GPIO_PIN;                        
    gpio_init(HALL_C_PORT, &gpio_init_struct);

    crm_periph_clock_enable(CRM_IOMUX_PERIPH_CLOCK, TRUE); //ʹ�ܸ���ʱ��
 

    tmr_base_init(HALL_CAPTURE_TIMER, HALL_CAPTURE_MAX_CNT, (HALL_CAPTURE_TIMER_DIV - 1));
    tmr_cnt_dir_set(HALL_CAPTURE_TIMER, TMR_COUNT_UP);

    // ����ͨ��1Ϊ���봥��Դ
    tmr_input_default_para_init(&tmr_input_config_struct);
    tmr_input_config_struct.input_channel_select = TMR_SELECT_CHANNEL_1;        // ����ͨ��ѡ��CH1
    tmr_input_config_struct.input_mapped_select = TMR_CC_CHANNEL_MAPPED_STI;    // ���������ź�ΪSTI
    tmr_input_config_struct.input_polarity_select = TMR_INPUT_BOTH_EDGE;        // �����غ��½��ض�����
    tmr_input_config_struct.input_filter_value = HALL_CAPTURE_FLITER;           // ���������ز����˲�
    tmr_input_channel_init(HALL_CAPTURE_TIMER, &tmr_input_config_struct, TMR_CHANNEL_INPUT_DIV_1);

    tmr_channel1_input_select(HALL_CAPTURE_TIMER, TMR_CHANEL1_2_3_CONNECTED_C1IRAW_XOR); // �����ź�������
    tmr_trigger_input_select(HALL_CAPTURE_TIMER, TMR_SUB_INPUT_SEL_C1INC);
    tmr_sub_mode_select(HALL_CAPTURE_TIMER, TMR_SUB_RESET_MODE);
    tmr_flag_clear(HALL_CAPTURE_TIMER, TMR_TRIGGER_FLAG | TMR_OVF_FLAG);          // ������������жϱ�־
    tmr_interrupt_enable(HALL_CAPTURE_TIMER, TMR_TRIGGER_INT | TMR_OVF_INT, TRUE);// ʹ�ܲ��������ж�
		//tmr_interrupt_enable(HALL_CAPTURE_TIMER, TMR_TRIGGER_INT, TRUE);							// enable the capture interrupt
    tmr_overflow_request_source_set(HALL_CAPTURE_TIMER, TRUE);
		tmr_counter_enable(HALL_CAPTURE_TIMER, TRUE);                                 // ʹ�ܲ���ʱ��
		nvic_irq_enable(HALL_CAPTURE_IRQn, 1, 0);
}

void adc_config(void)
{
    adc_base_config_type    adc_base_struct;
    gpio_init_type          gpio_init_struct;

    crm_periph_clock_enable(CRM_ADC1_PERIPH_CLOCK, TRUE);                         // ʹ��ADC1ʱ�� 
    crm_periph_clock_enable(CRM_ADC2_PERIPH_CLOCK, TRUE);                         // ʹ��ADC2ʱ��
    crm_adc_clock_div_set(CRM_ADC_DIV_6);                                         // ADCʱ������20Mhz,120M/6
    
    crm_periph_clock_enable(CRM_GPIOA_PERIPH_CLOCK, TRUE);                        // GPIOAʱ��
    crm_periph_clock_enable(CRM_GPIOB_PERIPH_CLOCK, TRUE);                        // GPIOBʱ��
    crm_periph_clock_enable(CRM_GPIOC_PERIPH_CLOCK, TRUE);                        // GPIOCʱ��
    
    gpio_default_para_init(&gpio_init_struct);
    gpio_init_struct.gpio_mode = GPIO_MODE_ANALOG;
    gpio_init_struct.gpio_out_type = GPIO_OUTPUT_OPEN_DRAIN;
    gpio_init_struct.gpio_pull = GPIO_PULL_NONE;
    // ADC1ͨ��
    gpio_init_struct.gpio_pins = CURR_PHASE_A_ADC_GPIO_PIN;
    gpio_init(CURR_PHASE_A_ADC_PORT, &gpio_init_struct);

	gpio_init_struct.gpio_pins = CURR_PHASE_B_ADC_GPIO_PIN;
    gpio_init(CURR_PHASE_B_ADC_PORT, &gpio_init_struct);
		
    gpio_init_struct.gpio_pins = CURR_PHASE_C_ADC_GPIO_PIN;
    gpio_init(CURR_PHASE_C_ADC_PORT, &gpio_init_struct);

 

    gpio_init_struct.gpio_pins = VOLT_BUS_ADC_GPIO_PIN;
    gpio_init(VOLT_BUS_ADC_PORT, &gpio_init_struct);

 

    adc_combine_mode_select(ADC_INDEPENDENT_MODE);                              // ADC��������ģʽ
    adc_base_default_para_init(&adc_base_struct);
    adc_base_struct.sequence_mode = TRUE;
    adc_base_struct.repeat_mode = FALSE;
    adc_base_struct.data_align = ADC_RIGHT_ALIGNMENT;
    adc_base_config(ADC1, &adc_base_struct);
    adc_base_config(ADC2, &adc_base_struct);
    
    adc_preempt_channel_length_set(ADC1, 4);
    adc_preempt_channel_set(ADC1, CURR_PHASE_A_ADC_CH, 1, ADC_SAMPLETIME_13_5);
    adc_preempt_channel_set(ADC1, CURR_PHASE_B_ADC_CH, 2, ADC_SAMPLETIME_13_5);
		adc_preempt_channel_set(ADC1, CURR_PHASE_C_ADC_CH, 3, ADC_SAMPLETIME_13_5);
 
    adc_preempt_channel_set(ADC1, VOLT_BUS_ADC_CH,     4, ADC_SAMPLETIME_13_5);

    adc_preempt_conversion_trigger_set(ADC1, ADC12_PREEMPT_TRIG_TMR1CH4, TRUE);
    adc_interrupt_enable(ADC1, ADC_PCCE_INT, TRUE);
 
    
    nvic_irq_enable(ADC1_2_IRQn, 2, 0);
    
    adc_enable(ADC1, TRUE);
    adc_enable(ADC2, TRUE);

    adc_calibration_init(ADC1);
    while(adc_calibration_init_status_get(ADC1));
    adc_calibration_start(ADC1);
    while(adc_calibration_status_get(ADC1));
    adc_calibration_init(ADC2);
    while(adc_calibration_init_status_get(ADC2));
    adc_calibration_start(ADC2);
    while(adc_calibration_status_get(ADC2));
}

 
/******************************************************************** 
 * 0 - 1Mbps
 * 1 - 500Kbps
 * 2 - 250Kbps
 * 3 - 125Kbps
 * 4 - 100Kbps
 * 5 - 50Kbps
*/

void CanBaudRateSet(uint8_t rate)
{
  uint16_t CanBaudRateBuf[6] = {15, 30, 60, 120, 150, 300};
  can_baudrate_type can_baudrate_struct;
  /* can baudrate, set baudrate = pclk/(baudrate_div *(1 + bts1_size + bts2_size)) = 1Mbps*/
  /* Sample_point = (1 + BTS1) / (1 + BTS1 + BTS2) �� 100 % */
  can_baudrate_struct.baudrate_div = CanBaudRateBuf[rate]; 
  can_baudrate_struct.rsaw_size = CAN_RSAW_1TQ;
  can_baudrate_struct.bts1_size = CAN_BTS1_6TQ;
  can_baudrate_struct.bts2_size = CAN_BTS2_1TQ;   
  can_baudrate_set(CAN1, &can_baudrate_struct);
}

/**
  *  @brief  can configiguration.
  *  @param  none
  *  @retval the result of can_configuration
  *          this parameter can be one of the following values:
  *          SUCCESS or ERROR
  */
void can_configuration(void)
{
  can_base_type can_base_struct;
  can_baudrate_type can_baudrate_struct;
  can_filter_init_type can_filter_init_struct;
  gpio_init_type gpio_init_struct;

  crm_periph_clock_enable(CRM_GPIOB_PERIPH_CLOCK, TRUE);
  crm_periph_clock_enable(CRM_CAN1_PERIPH_CLOCK, TRUE);
  crm_periph_clock_enable(CRM_IOMUX_PERIPH_CLOCK, TRUE);

  gpio_default_para_init(&gpio_init_struct);
  
  gpio_init_struct.gpio_drive_strength = GPIO_DRIVE_STRENGTH_MODERATE;
  gpio_init_struct.gpio_out_type = GPIO_OUTPUT_PUSH_PULL;
  gpio_init_struct.gpio_mode = GPIO_MODE_OUTPUT;
  gpio_init_struct.gpio_pins = GPIO_PINS_5;
  gpio_init_struct.gpio_pull = GPIO_PULL_NONE;
  gpio_init(GPIOB, &gpio_init_struct);

  gpio_bits_reset(GPIOB, GPIO_PINS_5);    
  
  /* can tx pin */
  gpio_init_struct.gpio_drive_strength = GPIO_DRIVE_STRENGTH_STRONGER;
  gpio_init_struct.gpio_out_type = GPIO_OUTPUT_PUSH_PULL;
  gpio_init_struct.gpio_mode = GPIO_MODE_MUX;
  gpio_init_struct.gpio_pins = GPIO_PINS_9;
  gpio_init_struct.gpio_pull = GPIO_PULL_NONE;
  gpio_init(GPIOB, &gpio_init_struct);
  /* can rx pin */
  gpio_init_struct.gpio_drive_strength = GPIO_DRIVE_STRENGTH_STRONGER;
  gpio_init_struct.gpio_mode = GPIO_MODE_MUX;//GPIO_MODE_INPUT;
  gpio_init_struct.gpio_pins = GPIO_PINS_8;
  gpio_init_struct.gpio_pull = GPIO_PULL_NONE;
  gpio_init(GPIOB, &gpio_init_struct);
  
    /* GPIO PIN remap */
  gpio_pin_remap_config(CAN1_GMUX_0010, TRUE);
  
  /* as specified in CAN protocol, the maximum allowable oscillator tolerance is 1.58%. 
     The HICK accuracy does not meet the clock requirements in CAN protocol. to guarantee normal 
     communication, it is recommended to use HEXT as the system clock source. */
  if(crm_flag_get(CRM_HEXT_STABLE_FLAG) != SET)
  {
    while(1);
  }

  
  /* can base init */
  can_default_para_init(&can_base_struct);
  can_base_struct.mode_selection = CAN_MODE_COMMUNICATE;  /* CAN ģʽ������ͨ��ģʽ */ 
  can_base_struct.ttc_enable  = FALSE;  /* CAN ʱ�䴥��ģʽ��ʱ��������ر� */ 
  can_base_struct.aebo_enable = TRUE;   /* �Զ��˳����߹��ܣ����� */ 
  can_base_struct.aed_enable  = TRUE;   /* �Զ��˳�˯�߹��ܣ����� */ 
  can_base_struct.prsf_enable = FALSE;  /* ��ֹ�Զ��ش����رգ��������Զ��ش���ͬ CAN ��׼Э�飩 */  
  can_base_struct.mdrsel_selection = CAN_DISCARDING_FIRST_RECEIVED;
  can_base_struct.mmssr_selection  = CAN_SENDING_BY_ID;
  can_base_init(CAN1, &can_base_struct);

	CanBaudRateSet(CAN_BAUDRATE_500KBPS); 

  /* can filter init */
  can_filter_init_struct.filter_activate_enable = TRUE;
  can_filter_init_struct.filter_mode = CAN_FILTER_MODE_ID_MASK;
  can_filter_init_struct.filter_fifo = CAN_FILTER_FIFO1;
  can_filter_init_struct.filter_number = 0;
  can_filter_init_struct.filter_bit = CAN_FILTER_32BIT;
  can_filter_init_struct.filter_id_high = 0;
  can_filter_init_struct.filter_id_low = 0;
  can_filter_init_struct.filter_mask_high = 0;
  can_filter_init_struct.filter_mask_low = 0;
  can_filter_init(CAN1, &can_filter_init_struct);

  /* can interrupt config */
 
  nvic_irq_enable(USBFS_L_CAN1_RX0_IRQn, 0x04, 0x00);
  can_interrupt_enable(CAN1, CAN_RF1MIEN_INT, TRUE);  
} 

void speed_dac_output_init(void)
  {
      gpio_init_type gpio_init_struct;

      /* 使能 GPIOA 和 DAC 时钟 */
      crm_periph_clock_enable(CRM_GPIOA_PERIPH_CLOCK, TRUE);
      crm_periph_clock_enable(CRM_DAC_PERIPH_CLOCK, TRUE);

      /* PA4 配置为模拟输入模式 (DAC 输出要求) */
      gpio_default_para_init(&gpio_init_struct);
      gpio_init_struct.gpio_pins = GPIO_PINS_4;
      gpio_init_struct.gpio_mode = GPIO_MODE_ANALOG;          // 模拟模式
      gpio_init_struct.gpio_out_type = GPIO_OUTPUT_OPEN_DRAIN;
      gpio_init_struct.gpio_pull = GPIO_PULL_NONE;
      gpio_init(GPIOA, &gpio_init_struct);

      /* 使能 DAC1，关闭触发（软件直接写入） */
      dac_enable(DAC1_SELECT, TRUE);
      dac_trigger_enable(DAC1_SELECT, FALSE);                 // 不使用硬件触发
      dac_output_buffer_enable(DAC1_SELECT, FALSE);           // 关闭输出缓冲（可选）
      dac_wave_generate(DAC1_SELECT, DAC_WAVE_GENERATE_NONE); // 不产生波形

      /* 初始输出 0V */
      dac_1_data_set(DAC1_12BIT_RIGHT, 0);
  }

