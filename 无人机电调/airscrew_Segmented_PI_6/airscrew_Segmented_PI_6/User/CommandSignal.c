/*
 * CommandSignal.c
 *
 *  Created on: 2024-06-23
 *      Author: WeibinYang
 */

#include "CommandSignal.h"

SIN_SIG	 SinSignal = SIN_SIG_DEFAULTS;
 

 

void SinSig_Cal(SIN_SIG *v)
{
    v->angle = v->angle + v->Ts * v->freq * 2 * PI;
    if(v->angle > 2*PI)	v->angle -= 2*PI;

    v->out = v->Amp * arm_sin_f32( v->angle);
		if ( v->Enable == 0 ){
			if ( v->angle < v->Ts * v->freq * 8 * PI )
				v->angle = 0; 
		}
}

 



