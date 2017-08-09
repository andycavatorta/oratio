import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Forget pins 20 and 21. They seem to be a bit funny with the AudioInjector hat on
# Also forget pin 19. This too is a pin of Great Evil

while True:
    print "1w", GPIO.input(5)
    print "1b", GPIO.input(6)
    print "2w", GPIO.input(13)
    print "2b", GPIO.input(26)
    print "3w", GPIO.input(12)
    print "3b", GPIO.input(16)
    time.sleep(0.1)
