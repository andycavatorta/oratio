"""
inputs:
    4 ADC chips on I2C
    1 rotary encoder on SPI
    
output topics:
    transport_pos_relative - integer from -8000 to 8000
    layer_speed - seconds in float from 0.5 to 10.0 
    layer_1_volume - float from 0.0 to 1.0
    layer_2_volume - float from 0.0 to 1.0
    layer_3_volume - float from 0.0 to 1.0
    layer_4_volume - float from 0.0 to 1.0
    layer_5_volume - float from 0.0 to 1.0

    voice_1_db_harmonic - integer from 0 to 16 (?)
    voice_1_db_fine - cents in integer from  -50 to +50
    voice_1_db_h1_harmonic - integer from 0 to 16 (?)
    voice_1_db_h1_fine - cents in integer from  -50 to +50
    voice_1_db_h1_vol - float from 0.0 to 1.0
    voice_1_db_h2_harmonic - integer from 0 to 16 (?)
    voice_1_db_h2_fine - cents in integer from  -50 to +50
    voice_1_db_h2_vol - float from 0.0 to 1.0
    voice_1_db_filter_a - float from 0.0 to 1.0
    voice_1_db_filter_b - float from 0.0 to 1.0

    voice_2_db_harmonic - integer from 0 to 16 (?)
    voice_2_db_fine - cents in integer from  -50 to +50
    voice_2_db_h1_harmonic - integer from 0 to 16 (?)
    voice_2_db_h1_fine - cents in integer from  -50 to +50
    voice_2_db_h1_vol - float from 0.0 to 1.0
    voice_2_db_h2_harmonic - integer from 0 to 16 (?)
    voice_2_db_h2_fine - cents in integer from  -50 to +50
    voice_2_db_h2_vol - float from 0.0 to 1.0
    voice_2_db_filter_a - float from 0.0 to 1.0
    voice_2_db_filter_b - float from 0.0 to 1.0

    voice_3_db_harmonic - integer from 0 to 16 (?)
    voice_3_db_fine - cents in integer from  -50 to +50
    voice_3_db_h1_harmonic - integer from 0 to 16 (?)
    voice_3_db_h1_fine - cents in integer from  -50 to +50
    voice_3_db_h1_vol - float from 0.0 to 1.0
    voice_3_db_h2_harmonic - integer from 0 to 16 (?)
    voice_3_db_h2_fine - cents in integer from  -50 to +50
    voice_3_db_h2_vol - float from 0.0 to 1.0
    voice_3_db_filter_a - float from 0.0 to 1.0
    voice_3_db_filter_b - float from 0.0 to 1.0

"""

import importlib
import json
import os
import Queue
import random
import settings 
import sys
import threading
import time

from thirtybirds_2_0.Network.manager import init as network_init
from thirtybirds_2_0.Network.email_simple import init as email_init
from thirtybirds_2_0.Adaptors.Sensors import AMT203

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
THIRTYBIRDS_PATH = "%s/thirtybirds" % (UPPER_PATH )

sys.path.append(BASE_PATH)
sys.path.append(UPPER_PATH)


class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.hostname = hostname
        self.queue = Queue.Queue()

    def add_to_queue(self, topic, msg):
        self.queue.put([topic, msg])

    def run(self):
        while True:
            topic_msg = self.queue.get(True)
            network.send(topic_msg[0], topic_msg[1])

class Transport(threading.Thread):
    def __init__(self, bus, deviceId):
        threading.Thread.__init__(self)
        self.bus = bus
        self.deviceId = deviceId
        print "creating amt203 object"
        self.encoder = AMT203.AMT203(bus, deviceId)
        print "setting zero ", self.bus, self.deviceId
        self.encoder.set_zero()
        print "after zero ", self.bus, self.deviceId 
        print "class Transport instantiated with values", bus, deviceId

    def run(self):
        print "class Transport thread started"
        while True:
            main.add_to_queue("transport_pos_raw", self.encoder.get_position())
            time.sleep(0.01)


def network_status_handler(msg):
    print "network_status_handler", msg

def network_message_handler(msg):
    print "network_message_handler", msg
    topic = msg[0]
    #host, sensor, data = yaml.safe_load(msg[1])
    if topic == "__heartbeat__":
        print "heartbeat received", msg

network = None # makin' it global

def init(HOSTNAME):
    global network
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
    #network.subscribe_to_topic("sensor_data")  
    main = Main(HOSTNAME)
    main.start()
    transport = Transport(0,0)
    transport.start()
