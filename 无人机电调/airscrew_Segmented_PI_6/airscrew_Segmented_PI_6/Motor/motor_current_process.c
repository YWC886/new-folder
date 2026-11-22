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
#include "motor_current_process.h"

/**
  ***********************************************************************************************************
  * ����
  * ********************************************************************************************************* 
  */ 
CURRENT_UDT current = CURRENT_DEFAULTS;

/**
  ***********************************************************************************************************
  * @brief  �������Ʊ�������
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_current_init(void)
{
    current.iq_demand = 0.0f;
    current.id_demand = 0.0f;

    current.offset_cnt = 0;
    current.offset_flg = 0;
    current.i_u_offset = 0;
    current.i_v_offset = 0;
    current.i_w_offset = 0;

    current.i_u = 0.0f;
    current.i_v = 0.0f;
    current.i_w = 0.0f;
	
		current.filterK1 = 1.0f/( 1 + PWM_FOC_PERIOD*2*PI*5000 );		/* Low-pass cut-off frequency = 1000 Hz */
		current.filterK2 = 1.0f - current.filterK1;
		current.i_u_filter = 0.0f;
    current.i_v_filter = 0.0f;
    current.i_w_filter = 0.0f;
	
		current.filter500HzK1 = 1.0f/( 1 + PWM_FOC_PERIOD*2*PI*500 );		/* Low-pass cut-off frequency = 1000 Hz */
		current.filter500HzK2 = 1.0f - current.filter500HzK1;
		current.i_bus_filter = 0.0f;
}

/**
  ***********************************************************************************************************
  * @brief  ����ƫ��ֵ����
  * @param  None
  * @retval У׼���״̬
  * ********************************************************************************************************* 
  */ 
uint8_t motor_current_offset(void)
{
    if(current.offset_flg == 0)
    {
        if(current.offset_cnt < 128)
        {
            current.i_u_offset += CURR_PHASE_A_REGISTER;
            current.i_v_offset += CURR_PHASE_B_REGISTER;
					  current.i_w_offset += CURR_PHASE_C_REGISTER;
            //current.i_bus_offset += CURR_BUS_REGISTER;
            current.offset_cnt++;
        }
        else
        {
            current.i_u_offset >>= 7;
					  current.i_v_offset >>= 7;
            current.i_w_offset >>= 7;
            //current.i_bus_offset >>= 7;
            current.offset_cnt = 0;
            current.offset_flg = 1;
            return 1;
        }
    }
    if(current.offset_flg == 1)
        return 1;
    else
        return 0;
}

/**
  ***********************************************************************************************************
  * @brief  ��ȡ����ֵ����������ű۲�������
  * @param  ����ģʽ�����ű۵������ʱmode=-1,�����������������ʱmode=1
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_current_read(int8_t mode)
{
		float Unit_factor = SAMPLE_CURR_CON_FACTOR / BASE_CURRENT;			//normalization: base current is 100A
	
 
	
    //current.i_u = mode * ((float)((CURR_PHASE_A_REGISTER - (int16_t)current.i_u_offset) * Unit_factor)); 
		current.i_u = mode * ((float)((CURR_PHASE_A_REGISTER - (int16_t)current.i_u_offset) * Unit_factor));
		current.i_v = mode * ((float)((CURR_PHASE_B_REGISTER - (int16_t)current.i_v_offset) * Unit_factor)); 
    current.i_w = mode * ((float)((CURR_PHASE_C_REGISTER - (int16_t)current.i_w_offset) * Unit_factor));
	
		current.i_u_filter = current.filterK1 * current.i_u_filter + current.filterK2 * current.i_u;
		current.i_v_filter = current.filterK1 * current.i_v_filter + current.filterK2 * current.i_v;
		current.i_w_filter = current.filterK1 * current.i_w_filter + current.filterK2 * current.i_w;     

		current.i_bus = (foc.Ta + 1)*0.5 * current.i_u_filter + (foc.Tb + 1)*0.5 * current.i_v_filter + (foc.Tc + 1)*0.5 * current.i_w_filter;
    current.i_bus_filter = current.filter500HzK1 * current.i_bus_filter + current.filter500HzK2 * current.i_bus;
		return;
}

 


 

