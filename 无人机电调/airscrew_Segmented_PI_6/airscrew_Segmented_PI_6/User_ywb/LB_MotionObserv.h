/* =================================================================================
File name:        LB_MotionObserv.H  
the luenberger style motion observer
===================================================================================*/


#ifndef __LB_MOTION_OBSERVER_H__
#define __LB_MOTION_OBSERVER_H__

#include "motor_all_header.h"

typedef struct {
       float ActTheta;  		// Input: Electrical angle to be filtered _IQ
       float EstTheta; 			// Output: Estimated Electrical angle global Q
			 float ThetaErr;			// Variable: the error between actual theta and the estimated theta, (-pi, pi)
       float Ui;   					// Variable: integration part
       float TL;       			// Variable: load torque  
       float TE;      			// Input: Estimated electrical torque
       float EstAccel;      // Variable: Estatimated Acceleration
       float EstSpd_Filt;   // Output: Estimated speed before derivation part
       float EstSpd_Regu_Old;	// Variable: Estimated speed after derivation part in the last instant
       float EstSpd_Regu;     // Variable: Estimated speed after derivation part in this instant
       float Ki;						//Parameter: intergration coefficient
			 float Kp;						//Parameter: proportional coefficient
			 float Kb;						//Parameter: differential coefficient
			 float Inertia_Inv;		//Parameter: the inverse of inertia
	     float EstMechTheta;
       } LB_MotionObserv;   	// Data type created

extern  LB_MotionObserv		MotionObsv;
/*-----------------------------------------------------------------------------
Default initalizer for the LB_MotionObserv object.
-----------------------------------------------------------------------------*/                     
#define LB_MOTION_OBSERV_DEFAULTS   { 0, \
                                    0, \
																		0, \
                                    0, \
                                    0, \
                                    0, \
                                    0, \
                                    0, \
                                    0, \
                                    0, \
                                    0, \
                                    0, \
																		0, \
																		0, \
                               	  }	

/*------------------------------------------------------------------------------
 SPEED_FR Macro Definition
------------------------------------------------------------------------------*/
void LB_MotionObsv_Init(LB_MotionObserv* v);
void LB_MotionObsv_Cal(LB_MotionObserv* v);

 

#endif // __SPEED_FR_H__
