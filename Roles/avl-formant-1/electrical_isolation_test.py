import wiringpi as wpi
import time

wpi.wiringPiSetup()
wpi.wiringPiSPISetup(0, 500000)

while True:
    for gain in range(255):
        print gain
        wpi.wiringPiSPIDataRW(0, chr(gain) + chr(0))
        time.sleep(0.05)
    for ungain in range(255):
        print 255-ungain
        wpi.wiringPiSPIDataRW(0, chr(255-ungain) + chr(0))
        time.sleep(0.05)
