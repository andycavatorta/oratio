"""
inputs:
    4 cap sensors on I2C
    3 rotary encoders on SPI
    
output topics:
    pitch_key_event - integer from 0 to 47
    voice_key_1_position - float from 0.0 to 1.0
    voice_key_2_position - float from 0.0 to 1.0
    voice_key_3_position - float from 0.0 to 1.0

"""

import importlib
import json
import os
import random
import settings 
import sys
import threading
import time

from thirtybirds_2_0.Network.manager import init as network_init
from thirtybirds_2_0.Network.email_simple import init as email_init

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

    def run(self):
        while True:
            network.send("pitch_key_event", random.randrange(0,47))
            time.sleep(random.randrange(0,3))
            network.send("voice_key_1_position", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_key_2_position", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_key_3_position", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("pitch_key_event", random.randrange(0,47))
            time.sleep(random.randrange(0,3))
            network.send("voice_key_1_position", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_key_2_position", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_key_3_position", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))

        ###  ###


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

