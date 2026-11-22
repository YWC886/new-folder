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
#include "motor_hall.h"

/**
  ***********************************************************************************************************
  * ����
  * ********************************************************************************************************* 
  */ 
HALL_UDT    hall    = HALL_DEFAULTS;

 
uint16_t hall_angle_mid[8] = {0, 10*A30D, 2*A30D, 0*A30D, 6*A30D, 8*A30D, 4*A30D, 0};// ����ֵ��Ӧ�����ĵ�Ƕ�
const uint8_t hall_next_value_index[8] = {1,3,6,2,5,1,4,1};                          // ���������������Ը��ݴ˱������һ�λ���ֵ

float hall_mid_val[8] = 
{
	// Maxon motor Hall table
	-10,    //0
	hall0offset(2.09360528f - Offset),  //1   120   
	hall0offset(4.18879032f - Offset),  //2   240��   
	hall0offset(3.14060521f - Offset),  //3   180      
	hall0offset(6.28279018f - Offset),  //4   0��  
	hall0offset(1.04660535f - Offset),  //5   60    
	hall0offset(5.23579025f - Offset),  //6   300��  
	-70,//7
	
 
};

/**
  ***********************************************************************************************************
  * @brief  ������������ʼ��
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall_sensor_params_init(void)
{

    hall.sector = 0;
    hall.last_sector = 0;
    hall.con_sector = 0;
    hall.new_sector_flg = 0;
    hall.hall_dir = 0;
    hall.uni_sector_cnt = 0;
    hall.past_sector_cnt = 0;
}
/**
  ***********************************************************************************************************
  * @brief  ��ʼ��������Ƕ�
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall_sensor_electrical_angle_init(void)
{
    hall.pll_dt_s = PWM_FOC_PERIOD;
    hall.pll_kp = 2000.0f;
    hall.pll_ki = 20000.0f;
}
/**
  ***********************************************************************************************************
  * @brief  ����ֵ��������ʼ��
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall_sensor_sector_init(void)
{
    hall.last_value = hall.value = HALL_PORTS_CBA & 0x7;
    hall.sector = hall.sector_table[hall.value];
    if(hall.sector < 3)                                                         // ��ǰ����С��3
        hall.con_sector = hall.sector + 3;                                      // 0~3��1~4��2~5 
    else hall.con_sector = hall.sector - 3;                                     // 3~0��4~1��5~2
    hall.last_sector = hall.sector;
}

/**
  ***********************************************************************************************************
  * @brief  ��ȡ����ֵ�ͻ�������
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall_sensor_sector(void)
{
    hall.last_value = hall.value;
    hall.value = HALL_PORTS_CBA & 0x7;
    hall.last_sector = hall.sector;
    hall.sector = hall.sector_table[hall.value];
    if(hall.sector < 3)                                                         // ��ǰ����С��3
        hall.con_sector = hall.sector + 3;                                      // 0~3��1~4��2~5 
    else hall.con_sector = hall.sector - 3;                                     // 3~0��4~1��5~2
}

/**
  ***********************************************************************************************************
  * @brief  ���ݻ����ź��жϵ��ת��
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall_sensor_direction(void)
{
    int8_t sector_increment=0;                                // ��������

    sector_increment = hall.sector - hall.last_sector;        // ��������ǰ����
    hall.sector_stay_cnt++;

    if(sector_increment != 0)                                 // �����ı�
    {
        hall.new_sector_flg = 1;                              // ������������ı䣬������������־λ
        
        switch(sector_increment)
        {
            // ��ת��CCW��������ʱ��
            case 1:
            case -5:
                if(hall.hall_dir != MOTOR_TURN_CCW)           // �ж��Ƿ�ת��ı�
                {
                    hall.uni_sector_cnt = 1;                  // ת�����仯�����¼���Ϊ1
                } 
                else if(hall.hall_dir == MOTOR_TURN_CCW)
                {
                    hall.uni_sector_cnt++;                    // ת�򲻱䣬�������ۼ�
                }
                hall.hall_dir = MOTOR_TURN_CCW;               // �赱ǰת���ʶΪ��ת��CCW
                hall.past_sector_cnt++;                       // ������������
            break;
            // ��ת��CW������˳ʱ��
            case -1:
            case 5:      
                if(hall.hall_dir != MOTOR_TURN_CW)    
                {
                    hall.uni_sector_cnt = 1;  
                }             
                else if(hall.hall_dir == MOTOR_TURN_CW)                
                {
                    hall.uni_sector_cnt++;                    // ת�򲻱䣬�������ۼ�
                }              
                hall.hall_dir = MOTOR_TURN_CW;                  
                hall.past_sector_cnt--;                       // ���������ݼ�                 
            break;
            // 3.��������(Ԥ��)
            default:
            break; 
        }
        // ��������һ��Ȧ��ֹͣ����������������
        if(hall.uni_sector_cnt > 30000)
        {
            hall.uni_sector_cnt = 30000;
        }
    }
    return;
}

// �Ƕ����ƣ����໷����ĽǶ���Ҫ������-PI~PI֮��
void motor_hall_sensor_utils_norm_angle_rad(float *angle) 
{
	while (*angle < -M_PI) 
    {
		*angle += 2.0f * M_PI;
	}

	while (*angle >  M_PI) 
    {
		*angle -= 2.0f * M_PI;
	}
}
// �������໷��������ǶȺͻ����ٶ�
void motor_hall_sensor_pll_run(float phase, float dt, volatile float *phase_var, volatile float *speed_var) 
{
    float delta_theta = 0;
    delta_theta = phase - *phase_var;                         // ����ǶȲ�ֵ
    motor_hall_sensor_utils_norm_angle_rad(&delta_theta);            // �淶�Ƕȷ�Χ
    *phase_var += (*speed_var + hall.pll_kp * delta_theta) * dt;
    motor_hall_sensor_utils_norm_angle_rad((float*)phase_var);
    *speed_var += hall.pll_ki * delta_theta * dt;
}

void motor_hall_sensor_angle_cal(void)
{
    float hall_diff = 0;
    // ��������ٶȣ��������ֵ
    hall.speed_rpm = hall.new_rad_s * 60.0f / ((ANGLE_2PI)  * MOTOR_POLE_PAIRS);
    hall.abs_speed_rpm = myabs(hall.speed_rpm);

    //�ж�hall�Ƿ����
    if((hall.value == 0 || hall.value == 7))
    {
        hall.error_cnt ++;
        if(hall.error_cnt >= 20)
        {
            //motor_error_status |= MOTOR_ERROR_ID_WRONGHALL;    // ��������
        }
    }
    else 
    {
        hall.error_cnt --;
        if(hall.error_cnt < 0)
        {
            hall.error_cnt = 0;
        }
    }

    // ���໷�ĽǶȻ�׼ֵΪ��ǰ�������������ĽǶ�ֵ����ǰ����Ϊ������������������Ż�Ϊ��ѧϰ���飬���������װƫ��
    hall.sector_mid_angle_read_rad = hall_mid_val[ hall.value ];
    hall.sector_mid_angle_rad = hall.sector_mid_angle_read_rad; // ��¼�˿�hall�ĽǶ�

    //������hallֵ����ȷ��
    if(hall.sector_mid_angle_read_rad > 0)
    {
        // �ϴλ������ϻ��״�����ʱ��ֱ�����õ�ǰ�Ƕȸ�ֵ
        if(hall.sector_mid_angle_read_last_rad < 0) 
        {
            // ���±��ζ�ȡ�Ļ����ǶȲ�ֱ�ӽ������õ����ջ����Ƕ������
            hall.sector_mid_angle_read_last_rad = hall.sector_mid_angle_read_rad;
            hall.pll_angle_rad = hall.sector_mid_angle_read_rad;
        }
        // ����ǻ����任����˵��������������
        else if(hall.sector_mid_angle_read_rad != hall.sector_mid_angle_read_last_rad)
        {
            // ���������������ٶ�Ƶ���ź�
            #if _FG == 1
            if(hallval == 1 || hallval == 6)
            {
                FGTG;
            }
            #endif
            // �����������������ĽǶȼ���ƽ��ֵ����ƽ��ֵ������Ϊ�ǻ��������ؽǶ�
            hall.pll_average_angle_rad = myabs((hall.sector_mid_angle_read_rad - hall.sector_mid_angle_read_last_rad));
            if(hall.pll_average_angle_rad < M_PI)
            {
                hall.pll_average_angle_rad = (hall.sector_mid_angle_read_rad + hall.sector_mid_angle_read_last_rad) / 2.0f;
            }
            else if(hall.pll_average_angle_rad != M_PI)
            {
                hall.pll_average_angle_rad = (hall.sector_mid_angle_read_rad + hall.sector_mid_angle_read_last_rad) / 2.0f + M_PI;
            }
            
            while(hall.pll_average_angle_rad > ANGLE_2PI)        // �淶�Ƕ�
            {
                hall.pll_average_angle_rad -= ANGLE_2PI;
            }
            while(hall.pll_average_angle_rad < 0)                // �淶�Ƕ�
            {
                hall.pll_average_angle_rad += ANGLE_2PI;
            }
            hall.pll_angle_rad = hall.pll_average_angle_rad;     // �����������������ĽǶȽ���У׼
        }
        // ��һ�νǶȸ�ֵΪ��ǰ�Ƕ� �����ж�hall�Ƿ�仯
        hall.sector_mid_angle_read_last_rad = hall.sector_mid_angle_read_rad;

        //�����ǰת��С�� N����ôhallֱ�ӵ��ڵ�ǰ�Ƕȣ��������ۼ��ˣ��൱�ڷ���
        if(hall.abs_speed_rpm < 100)       
        {
            // ʹ�����������ĽǶ�
            hall.pll_angle_rad = hall.sector_mid_angle_read_rad;      
        }
        else 
        {
            // ���㵱ǰ�ۼ�ֵ�Ƿ񳬳��Ƕȷ�Χ��hall,Ang�ǻ��ֽ����midAng��У׼ֵ
            hall_diff = hall.pll_angle_rad - hall.sector_mid_angle_rad;
            
            // �����ֵ������-PI��PI��Χ��
            while (hall_diff > M_PI) 
            {
                hall_diff -= ANGLE_2PI;
            }
            while (hall_diff < -M_PI) 
            {
                hall_diff += ANGLE_2PI;
            }
            // ��������30��֮�ڣ�˵���Ƕ���ȷ�������ٶȻ��ּ�������Ƕȣ��˴����ò岹��������Ƕ�
            if( myabs(hall_diff) < (ANGLE_2PI / 12.0f) )
            {
                hall.pll_angle_rad += hall.new_rad_s * hall.pll_dt_s;
            }
            // ���������30�㣬�򽫽Ƕ�ǿ�Ƽ�С��������С���
            else 
            {
                hall.pll_angle_rad -= hall_diff / 100.0f;
            }
        }
        // ���ǶȻ��ֽ��������0-2PI��Χ��
        while (hall.pll_angle_rad >  ANGLE_2PI) 
        {
            hall.pll_angle_rad -= ANGLE_2PI;
        }
        while (hall.pll_angle_rad < 0) 
        {
            hall.pll_angle_rad += ANGLE_2PI;
        }
        
    }
    //�Ƕ�Ϊ�����
    else 
    {
        // ���ϴε�ֵ��ֵΪ-1�������´ζ�����ֵ����ȷ�������������
        hall.sector_mid_angle_read_last_rad = -1;  
    }
    // ���岹����ĽǶ��������໷������ǶȺ�ת��
    motor_hall_sensor_pll_run(hall.pll_angle_rad, hall.pll_dt_s, &hall.old_rad_s, &hall.new_rad_s);
}
/**
  ***********************************************************************************************************
  * @brief  ������������������������ȡ�ͷ����ж�
  * @param  None
  * @retval None
  * ********************************************************************************************************* 
  */ 
void motor_hall_sensor_sampled(void)
{
    motor_hall_sensor_sector();
    motor_hall_sensor_direction();
    motor_hall_sensor_angle_cal();
}
 



