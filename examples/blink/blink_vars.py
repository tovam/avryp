import avryp

# This example makes B0 and B2 blink
# The C code is is given as an argument to the add_source method
#   and it uses Avryp variables
# Occurences of `$avryp_dt` are replaced by `300`


c = avryp.Avryp()

# Frequency is 16MHz
c.freq(16000000)

# Chip is ATmega328P
c.chip('atmega328p')

# Add one source file
# __avryp.h defines macros for SETOUTPUT, SETHIGH and SETLOW
c.add_source('a.c', '''#include "__avryp.h"
#include <avr/io.h>
#include <util/delay.h>
#include <AVRYPVariables>
int main(){
	SETOUTPUT(DDRB, 0);
	SETOUTPUT(DDRB, 2);
	SETHIGH(PORTB, 0);
	SETHIGH(PORTB, 2);

	while(1){
		_delay_ms($avryp_dt);
		SETHIGH(PORTB, 0);
		_delay_ms($avryp_dt);
		SETHIGH(PORTB, 2);
		_delay_ms($avryp_dt);
		SETLOW(PORTB, 0);
		_delay_ms($avryp_dt);
		SETLOW(PORTB, 2);
	}
}'''
)
c.setvar('dt', 1000)
c.build_flash()
