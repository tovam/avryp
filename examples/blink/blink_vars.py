import avryp

'''This example make B0 and B2 blink'''

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
c.setvar('dt',300)
c.build_flash()
