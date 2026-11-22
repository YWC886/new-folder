/* =================================================================================
File name:        SPEED_FR.H  
		if(v.speedstartflag!=0)\
		{\
			v.speedstartflag=1\
			v.Tmp=0;	\
		}\
===================================================================================*/


#ifndef __COMMAND_SIGNAL_H__
#define __COMMAND_SIGNAL_H__

#include "motor_all_header.h"

typedef struct {
       int32_t AccelDelta;  	 // Variable: Acceleration (pu) _IQ
       int32_t VelocityDelta; // Variable: Direction of rotation (Q0) - independently with global Q
			 int32_t Velocity;
       int32_t PosOut;   	 // History: Electrical angle at previous step (pu)
       int32_t PosCmd;       	// Output: Speed in per-unit  (pu)- global Q
			 int32_t PosInit; 
	     int32_t Distance;
			 int32_t FinishFlag;
       } POS_RAMP;   	// Data type created

typedef struct {
			float 		out;
			float			freq;
			float			Ts;
			float			Amp;
			float			angle;
			uint8_t		Enable;
			} SIN_SIG;
 	

#define	SIN_SIG_DEFAULTS		{ 0,0,0,0,0 }
/*------------------------------------------------------------------------------
 Command signal Macro Definition
------------------------------------------------------------------------------*/
 
 		
void SinSig_Cal(SIN_SIG *v);

extern SIN_SIG	 SinSignal;

#endif // __SPEED_FR_H__
