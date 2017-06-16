import avryp

# This example simulates a USB mouse
# Accepted frequencies are 12, 12.8, 15, 16, 16.5, 18 and 20 MHz
# Read and edit usbdrv/usbconfig.h to match your project (see USB_CFG_IOPORTNAME, USB_CFG_DMINUS_BIT, USB_CFG_DPLUS_BIT)
# The cursor movements are random
# The B0 pin blinks


c = avryp.Avryp()

# Frequency is 16MHz
c.freq(16000000)

# Chip is ATmega328P
c.chip('atmega328p')

# Add USB library
c.add_include_dir('usbdrv')
c.add_source('usbdrv/usbdrv.c')
c.add_source('usbdrv/usbdrvasm.S')

# Add the program itself
c.add_source('main.c')

# LED is on the pin B0
c.setvar('port_led', 'B')
c.setvar('pin_led', 0)

# Build binaries for different blinking speeds
for i in [10, 30, 100, 300, 1000]:
	c.setvar('speed', i)
	c.build(output = 'usbmouse_%d'%i)

# Flash one of the binaries
c.flash('usbmouse_100.hex')
