import avryp

# This example makes B0 and B2 blink
# The project has two existing .c files


c = avryp.Avryp()

# Frequency is 16MHz
c.freq(16000000)

# Chip is ATmega328P
c.chip('atmega328p')

# Add source files
c.add_source('blink.c')
c.add_source('dt.c')

c.build_flash()
