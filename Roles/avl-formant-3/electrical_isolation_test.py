import wiringpi as wpi
import time

wpi.wiringPiSetup()
wpi.wiringPiSPISetup(0, 500000)

while True:
    for gain in range(192):
        print gain
        wpi.wiringPiSPIDataRW(0, chr(gain) + chr(0))
        time.sleep(0.02)
    for ungain in range(192):
        print 192-ungain
        wpi.wiringPiSPIDataRW(0, chr(192-ungain) + chr(0))
        time.sleep(0.02)
