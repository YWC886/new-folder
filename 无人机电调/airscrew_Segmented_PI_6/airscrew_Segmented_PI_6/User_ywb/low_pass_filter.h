/* =================================================================================
File name:        LB_MotionObserv.H  
the luenberger style motion observer
===================================================================================*/


#ifndef __LOW_PASS_FILTER_H__
#define __LOW_PASS_FILTER_H__

#include "motor_all_header.h"

typedef struct {
       float SigIn;  		// Input: Electrical angle to be filtered _IQ
       float SigFilterOut; 			// Output: Estimated Electrical angle global Q
			 float FilterK1;			// Variable: the error between actual theta and the estimated theta, (-pi, pi)
	     float FilterK2;
       } LOW_PASS_FILTER;   	// Data type created

extern  LOW_PASS_FILTER	 LPF_100Hz_UqMax;
/*-----------------------------------------------------------------------------
Default initalizer for the LB_MotionObserv object.
-----------------------------------------------------------------------------*/                     
#define LOW_PASS_FILTER_DEFAULTS   { 0, \
                                    0, \
																		0, \
                                    0, \
                               	  }	

/*------------------------------------------------------------------------------
 SPEED_FR Macro Definition
------------------------------------------------------------------------------*/
void LowPassFilter_Init(LOW_PASS_FILTER* v);
void LowPassFilter_Cal(LOW_PASS_FILTER* v);



#endif // __SPEED_FR_H__
