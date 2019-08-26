import wiringpi as wpi
import time

wpi.wiringPiSetup()
wpi.wiringPiSPISetup(0, 500000)

while True:
    for gain in range(92):
        gain_offset = gain + 100
        print gain_offset
        wpi.wiringPiSPIDataRW(0, chr(gain_offset) + chr(0))
        time.sleep(0.1)
    for ungain in range(92):
        gain_offset = 192-ungain
        #print 192-ungain
        wpi.wiringPiSPIDataRW(0, chr(gain_offset) + chr(0))
        time.sleep(0.1)
