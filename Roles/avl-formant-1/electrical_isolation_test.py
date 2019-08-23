import wiringpi as wpi
import time

wpi.wiringPiSetup()
wpi.wiringPiSPISetup(0, 500000)

while True:
    for gain in range(220):
        wpi.wiringPiSPIDataRW(0, chr(gain) + chr(0))
        time.sleep(0.01)
    for ungain in range(220):
        wpi.wiringPiSPIDataRW(0, chr(220-ungain) + chr(0))
        time.sleep(0.01)
