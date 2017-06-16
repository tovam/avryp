import avryp

# This example makes B0 and B2 blink
# The C code is is given as an argument to the add_source method


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
int main(){
	SETOUTPUT(DDRD, 0);
	SETOUTPUT(DDRD, 1);
	SETHIGH(PORTD, 0);
	SETHIGH(PORTD, 1);

	while(1){
		_delay_ms(300);
		SETHIGH(PORTD, 0);
		_delay_ms(300);
		SETHIGH(PORTD, 1);
		_delay_ms(300);
		SETLOW(PORTD, 0);
		_delay_ms(300);
		SETLOW(PORTD, 1);
	}
}'''
)
c.build_flash()
