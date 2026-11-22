 #include "motor_speed_output.h"
 #define SPEED_DAC_MAX_RPM       5000.0f     /* 对应 3.3V 满量程输出的转速 */

  /**
    * @brief  将机械转速转换为 DAC 数值并输出到 PA4
    * @param  mechanical_rpm: 当前机械转速 (RPM)
    * @retval none
    *
    * 调用位置建议: 在 SysTick 中断 (motor_ctrl_state_loop) 或
    *              ADC 中断的速度计算完成后调用。
    *              hall2angle.pll_speed_rpm_filter 可作为输入参数。
    */

	
	void speed_dac_output_set_val(uint16_t dac_val)
  {
      if (dac_val > 4095)
      {
          dac_val = 4095;
      }
      dac_1_data_set(DAC1_12BIT_RIGHT, dac_val);
  }
	
	  void motor_speed_dac_update(float mechanical_rpm)
  {
      uint16_t dac_val;
      float ratio;

      /* 取绝对值 (反转时也输出正电压) */
      if (mechanical_rpm < 0.0f)
      {
          mechanical_rpm = -mechanical_rpm;
      }

      /* 限制在 0 ~ MAX_RPM 范围内 */
      if (mechanical_rpm > SPEED_DAC_MAX_RPM)
      {
          mechanical_rpm = SPEED_DAC_MAX_RPM;
      }

      /* 线性映射: RPM →DAC 数值 (0~4095) */
      ratio = mechanical_rpm / SPEED_DAC_MAX_RPM;
      dac_val = (uint16_t)(ratio * 4095.0f);

      /* 写入 DAC 寄存器，立即更新输出电压 */
      speed_dac_output_set_val(dac_val);
  }