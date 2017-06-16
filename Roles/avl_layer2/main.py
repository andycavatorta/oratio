
import Adafruit_MCP3008
import importlib
import json
import os
import Queue
import random
import RPi.GPIO as GPIO
import settings 
import sys
import threading
import time
#import wiringpi as wpi

from thirtybirds_2_0.Network.manager import init as network_init
from thirtybirds_2_0.Network.email_simple import init as email_init

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
THIRTYBIRDS_PATH = "%s/thirtybirds" % (UPPER_PATH )

sys.path.append(BASE_PATH)
sys.path.append(UPPER_PATH)


class Drawbar():
    def __init__(self, 
        name, 
        adc,
        adc_channel,
        detent_adc_values = [],
        max = 1023,
        min = 0
        ):
        self.name = name
        self.adc = adc
        self.adc_channel = adc_channel
        self.detent_adc_values = detent_adc_values
        self.max = max
        self.min = min
        self.previous_value = -1
        self.change_threshold = 5

    def detent_from_adc_value(self, raw_value):
        return self.detent_adc_values.index(min(self.detent_adc_values, key=lambda x:abs(x-raw_value)))

    def normalize_adc_value_to_min_max(self, val):
        value_range = self.max - self.min
        val_with_min_offset = val - self.min
        value_normalized = float(val_with_min_offset) / float(value_range)
        value_normalized = value_normalized if value_normalized > 0.0 else 0.0
        value_normalized = value_normalized if value_normalized < 1.0 else 1.0
        return 1.0 - value_normalized

    def read(self):
        # get raw value
        raw_value = self.adc.read_adc(self.adc_channel)
        # if close to last values, return -1
        if abs(self.previous_value - raw_value) <= self.change_threshold:
            self.previous_value = raw_value
            return -1

        self.previous_value = raw_value
        # if detent values, get detents
        if len(self.detent_adc_values) > 0:
            return self.detent_from_adc_value(raw_value)
        else:
            return self.normalize_adc_value_to_min_max(raw_value)

class Drawbars(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        CLK  = 18
        MISO = 23
        MOSI = 24
        CS0   = 25
        CS1   = 8
        self.adc1 = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS0, miso=MISO, mosi=MOSI)
        self.adc2 = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS1, miso=MISO, mosi=MOSI)
        self.drawbars = [
            Drawbar(
                name="voice_2_db_harmonic" , 
                detent_adc_values = [1022, 1008, 950, 888, 833, 760, 705, 640, 579],
                adc=self.adc1,
                adc_channel=0
            ),
            Drawbar(
                name="voice_2_db_fine" , 
                min=50, 
                max=998,
                adc=self.adc1,
                adc_channel=1
            ),
            Drawbar(
                name="voice_2_db_h1_fine" , 
                min=60, 
                max=950,
                adc=self.adc1,
                adc_channel=2
            ),
            Drawbar(
                name="voice_2_db_h1_harmonic" , 
                detent_adc_values = [1022, 1012, 972, 956, 844, 793, 733, 674, 582],
                adc=self.adc1,
                adc_channel=3
            ),
            Drawbar(
                name="voice_2_db_h1_vol" , 
                min=50, 
                max=987,
                adc=self.adc1,
                adc_channel=4
            ),
            Drawbar(
                name="voice_2_db_h2_fine" , 
                min=54, 
                max=1010,
                adc=self.adc2,
                adc_channel=0
            ),
            Drawbar(
                name="voice_2_db_h2_harmonic" , 
                detent_adc_values = [1021, 1011, 980, 932, 843, 806, 708,669, 594],
                adc=self.adc2,
                adc_channel=1
            ),
            Drawbar(
                name="voice_2_db_h2_vol" , 
                min=39, 
                max=1008,
                adc=self.adc2,
                adc_channel=2
            ),
            Drawbar(
                name="voice_2_db_filter_a" , 
                min=55, 
                max=1008,
                adc=self.adc2,
                adc_channel=3
            ),
            Drawbar(
                name="voice_2_db_filter_b" , 
                min=76, 
                max=1009,
                adc=self.adc2,
                adc_channel=4
            )
        ]

    def run(self):
        while True:
            for drawbar in self.drawbars:
                val = drawbar.read()
                #print ">>>",drawbar.name, val
                if val > -1:
                    network.send(drawbar.name, val)
                time.sleep(0.005)

def network_status_handler(msg):
    print "network_status_handler", msg

def network_message_handler(msg):
    print "network_message_handler", msg
    topic = msg[0]
    #host, sensor, data = yaml.safe_load(msg[1])
    if topic == "__heartbeat__":
        print "heartbeat received", msg

network = None # makin' it global
main = None

def init(HOSTNAME):
    global network
    global main
    network = network_init(
        hostname=HOSTNAME,
        role="client",
        discovery_multicastGroup=settings.discovery_multicastGroup,
        discovery_multicastPort=settings.discovery_multicastPort,
        discovery_responsePort=settings.discovery_responsePort,
        pubsub_pubPort=settings.pubsub_pubPort,
        message_callback=network_message_handler,
        status_callback=network_status_handler
    )

    network.subscribe_to_topic("system")  # subscribe to all system messages
    drawbars = Drawbars()
    drawbars.daemon = True
    drawbars.start()
