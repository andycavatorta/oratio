# Simple example of reading the MCP3008 analog input channels and printing
# them all out.
# Author: Tony DiCola
# License: Public Domain
import time

# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

# Software SPI configuration:
CLK  = 11
MISO = 9
MOSI = 10
CS   = 21

def test_adc(chip_select_pin):
    mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=chip_select_pin, miso=MISO, mosi=MOSI)
    print ""
    print "Reading MCP3008 values on chip select pin", chip_select_pin
    # Print nice channel column headers.
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*range(8)))
    print('-' * 57)
    # Main program loop.
    for i in range(10) :
        # Read all the ADC channel values in a list.
        values = [0]*8
        for i in range(8):
            # The read_adc function will get the value of the specified channel (0-7).
            values[i] = mcp.read_adc(i)
        # Print the ADC values.
        print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*values))
        # Pause for half a second.
        #time.sleep(0.1)


for chip_select_pin in [7,7,7,7,7,7,7,7,7,7]:
    test_adc(chip_select_pin)




