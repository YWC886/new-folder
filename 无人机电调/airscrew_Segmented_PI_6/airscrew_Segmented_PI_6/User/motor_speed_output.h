#ifndef _MOTOR_SPEED_OUTPUT_H_
#define _MOTOR_SPEED_OUTPUT_H_

#include "motor_all_header.h"

void speed_dac_output_set_val(uint16_t dac_val);
void motor_speed_dac_update(float mechanical_rpm);

#endif
