import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
    print "1w", GPIO.input(6)
    print "1b", GPIO.input(13)
    print "2w", GPIO.input(19)
    print "2b", GPIO.input(26)
    print "3w", GPIO.input(16)
    print "3b", GPIO.input(20)
    time.sleep(0.1)
