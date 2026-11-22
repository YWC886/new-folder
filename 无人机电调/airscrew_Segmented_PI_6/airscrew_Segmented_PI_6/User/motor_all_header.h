#ifndef _MOTOR_ALL_HEADER_H_
#define _MOTOR_ALL_HEADER_H_

#include "at32f403a_407.h"
#include "at32f403a_407_conf.h"
#include "at32f403a_407_clock.h"

#include "arm_math.h"
#include "math.h"


#include "motor_ctrl_config.h"
#include "mcu_hardware_config.h"
#include "motor_analog_sampled.h"
#include "motor_ctrl_process.h"
#include "motor_foc_core.h"

#include "motor_hall.h"
#include "motor_pid_calc.h"
#include "motor_protect_process.h"
#include "motor_current_process.h"
#include "motor_velocity_process.h"


#include "motor_open_loop.h"
#include "motor_close_loop.h"
#include "CommandSignal.h"

#include "can.h"
#include "pwm_input.h"
#include "motor_hall2angle.h"
#include "LB_MotionObserv.h"
#include "low_pass_filter.h"
#include "motor_speed_output.h"
#endif


