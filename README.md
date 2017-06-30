# Avryp

Avryp is a Python package to build and flash AVR and Arduino code.

## Getting Started

### Prerequisites
Avryp needs AVR tools to work, you can install them by running the following command.
``` sudo apt-get install avr-libc avrdude binutils-avr gcc-avr ```

### Installing
Avryp is on PyPI so installing it is easy with *pip*.
``` sudo pip install avryp ```

## Examples

Examples can be found in the [examples](https://github.com/tovam/avryp/tree/master/examples) directory.

## Configuration

Avryp reads ~/.avryprc for binaries and Arduino library path.

If not given, the default values are the following:

```
#[arduino]
#haa = /path/to/hardware/arduino/avr/  #no default, but optional
[binaries]
avrdude = avrdude
avrdude_progtype = linuxgpio
avrobjcopy = avr-objcopy
avrsize = avr-size
avrgcc = avr-gcc
avrgpp = avr-g++
```

## License
This project is licensed under the MIT License - see the [LICENSE](https://github.com/tovam/avryp/blob/master/LICENSE) file for details
