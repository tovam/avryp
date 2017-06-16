#include "__avryp.h"
#include <avr/io.h>
#include <util/delay.h>

void delayms(int ms){
	for(int i=0;i<ms;i+=10)_delay_ms(10);
}

int dt();

int main(){
    SETOUTPUT(DDRB, 0);
    SETOUTPUT(DDRB, 2);
    SETHIGH(PORTB, 0);
    SETHIGH(PORTB, 2);

	int delay = dt();

    while(1){
        delayms(delay);
        SETHIGH(PORTB, 0);
        delayms(delay);
        SETHIGH(PORTB, 2);
        delayms(delay);
        SETLOW(PORTB, 0);
        delayms(delay);
        SETLOW(PORTB, 2);
    }
}
