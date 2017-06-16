#include "__avryp.h"
#include <avr/io.h>
#include <util/delay.h>

//void delayms(int ms){
//	for(int i=0;i<ms;i+=10)_delay_ms(10);
//}

//int dt(){return 500;}

int main(){
    SETOUTPUT(DDRD, 0);
    SETOUTPUT(DDRD, 1);
    SETHIGH(PORTD, 0);
    SETHIGH(PORTD, 1);

	int delay = 500; //dt();

    while(1){
//        delayms(delay);
        _delay_ms(500);
        SETHIGH(PORTD, 0);
        _delay_ms(500);
        SETHIGH(PORTD, 1);
        _delay_ms(500);
        SETLOW(PORTD, 0);
        _delay_ms(500);
        SETLOW(PORTD, 1);
    }
}
