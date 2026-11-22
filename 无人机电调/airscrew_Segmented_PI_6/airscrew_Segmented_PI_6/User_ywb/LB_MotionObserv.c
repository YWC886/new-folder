/* =================================================================================
File name:        LB_MotionObserver.C  
the luenberger style motion observer
===================================================================================*/
#include "motor_hall2angle.h"

LB_MotionObserv MotionObsv = LB_MOTION_OBSERV_DEFAULTS;

void LB_MotionObsv_Init(LB_MotionObserv* v)
{
// Initialize the LB_MotionObserv module for theta estimation
     v->Kp = 12980.0f;              //1.082183f;    					//32000.0f;						//
     v->Ki = 10.0f;              		//10.0f;       					//10.0f
     v->Kb = 16.57f;                 
     v->Inertia_Inv = 189.4f;       
 
}

void LB_MotionObsv_Cal(LB_MotionObserv* v)
{
	float SpeedAvg;
	float Ts = PWM_FOC_PERIOD;
	
/* Theta Error computation   */								
		v->ThetaErr = v->ActTheta - v->EstTheta;   
		if (v->ThetaErr > PI) v->ThetaErr -= 2*PI;
		else if (v->ThetaErr < -PI ) v->ThetaErr += 2*PI;
/*--------------------------------------------------------*/                                                                  
		v->Ui += v->Ki * Ts * v->ThetaErr;           
		v->TL = v->Ui + v->ThetaErr * v->Kp;               
/*--------------------------------------------------------*/        
                                
		v->EstAccel = (v->TE + v->TL) * v->Inertia_Inv;                               												
 
		v->EstSpd_Filt += Ts * v->EstAccel;					
		v->EstSpd_Regu = v->EstSpd_Filt + v->ThetaErr * v->Kb * v->Inertia_Inv;										
		SpeedAvg = (v->EstSpd_Regu + v->EstSpd_Regu_Old) * 0.5;
 							
    v->EstSpd_Regu_Old = v->EstSpd_Regu;									
 				
    v->EstTheta += Ts * SpeedAvg;
		if (v->EstTheta > 2*PI) v->EstTheta -= 2*PI;
		else if (v->EstTheta < 0 ) v->EstTheta += 2*PI;
		
		v->EstMechTheta += Ts * SpeedAvg / MOTOR_POLE_PAIRS;
}											



