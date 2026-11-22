/* =================================================================================
File name:        LB_MotionObserver.C  
the luenberger style motion observer
===================================================================================*/
#include "motor_hall2angle.h"

LOW_PASS_FILTER	 LPF_100Hz_UqMax = LOW_PASS_FILTER_DEFAULTS;

void LowPassFilter_Init(LOW_PASS_FILTER* v)
{
		v->SigFilterOut = 0;
		v->FilterK1 = 1.0f/( 1 + PWM_FOC_PERIOD*2*PI*100 );		/* Low-pass cut-off frequency = 100 Hz */
		v->FilterK2 = 1.0f - v->FilterK1;
}

void LowPassFilter_Cal(LOW_PASS_FILTER* v)
{
		v->SigFilterOut = v->FilterK1 * v->SigFilterOut + v->FilterK2 * v->SigIn;
}											



