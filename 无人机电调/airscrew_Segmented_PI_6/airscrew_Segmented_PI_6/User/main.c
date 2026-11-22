#include "motor_all_header.h"

int main(void)
{
	mcu_peripheral_init(); 
	 
 

	while(1)
	{   
		can_updata();
	}
}






