import wiringpi as wpi
import time
import random

wpi.wiringPiSetup()
wpi.wiringPiSPISetup(0, 500000)
"""
while True:
    wpi.wiringPiSPIDataRW(0, chr(180) + chr(0))
    time.sleep(0.03)

"""
while True:
    for gain in range(92):
        gain_offset = gain + 100 + random.randint(0,20)
        print gain_offset
        wpi.wiringPiSPIDataRW(0, chr(gain_offset) + chr(0))
        time.sleep(0.02)
    for ungain in range(92):
        gain_offset = 192-ungain + random.randint(0,20)
        print gain_offset
        wpi.wiringPiSPIDataRW(0, chr(gain_offset) + chr(0))
        time.sleep(0.02)
