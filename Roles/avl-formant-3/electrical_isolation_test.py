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
    for gain in range(9):
        gain_offset = (gain*10) + 100 
        print gain_offset
        wpi.wiringPiSPIDataRW(0, chr(gain_offset) + chr(0))
        time.sleep(0.05)
    for ungain in range(9):
        gain_offset = 192-(ungain*10) 
        print gain_offset
        wpi.wiringPiSPIDataRW(0, chr(gain_offset) + chr(0))
        time.sleep(0.05)
