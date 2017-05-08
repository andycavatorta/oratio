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
        network.send("transport_pos_relative", random.randrange(-8000,8000))
        network.send("layer_speed", random.randrange(0,10000) /1000.0)
        network.send("layer_1_volume", random.randrange(0,100)/100.0)
        network.send("layer_2_volume", random.randrange(0,100)/100.0)
        network.send("layer_3_volume", random.randrange(0,100)/100.0)
        network.send("layer_4_volume", random.randrange(0,100)/100.0)
        network.send("layer_5_volume", random.randrange(0,100)/100.0)
        network.send("voice_1_db_harmonic", random.randrange(0,16))
        network.send("voice_1_db_fine", random.randrange(-50,50))
        network.send("voice_1_db_h1_harmonic", random.randrange(0,16))
        network.send("voice_1_db_h1_fine", random.randrange(-50,50))
        network.send("voice_1_db_h1_vol", random.randrange(0,100)/100.0)
        network.send("voice_1_db_h2_harmonic", random.randrange(0,16))
        network.send("voice_1_db_h2_fine", random.randrange(-50,50))
        network.send("voice_1_db_h2_vol", random.randrange(0,100)/100.0)
        network.send("voice_1_db_filter_a", random.randrange(0,100)/100.0)
        network.send("voice_1_db_filter_b", random.randrange(0,100)/100.0)

        network.send("voice_2_db_harmonic", random.randrange(0,16))
        network.send("voice_2_db_fine", random.randrange(-50,50))
        network.send("voice_2_db_h1_harmonic", random.randrange(0,16))
        network.send("voice_2_db_h1_fine", random.randrange(-50,50))
        network.send("voice_2_db_h1_vol", random.randrange(0,100)/100.0)
        network.send("voice_2_db_h2_harmonic", random.randrange(0,16))
        network.send("voice_2_db_h2_fine", random.randrange(-50,50))
        network.send("voice_2_db_h2_vol", random.randrange(0,100)/100.0)
        network.send("voice_2_db_filter_a", random.randrange(0,100)/100.0)
        network.send("voice_2_db_filter_b", random.randrange(0,100)/100.0)

        network.send("voice_3_db_harmonic", random.randrange(0,16))
        network.send("voice_3_db_fine", random.randrange(-50,50))
        network.send("voice_3_db_h1_harmonic", random.randrange(0,16))
        network.send("voice_3_db_h1_fine", random.randrange(-50,50))
        network.send("voice_3_db_h1_vol", random.randrange(0,100)/100.0)
        network.send("voice_3_db_h2_harmonic", random.randrange(0,16))
        network.send("voice_3_db_h2_fine", random.randrange(-50,50))
        network.send("voice_3_db_h2_vol", random.randrange(0,100)/100.0)
        network.send("voice_3_db_filter_a", random.randrange(0,100)/100.0)
        network.send("voice_3_db_filter_b", random.randrange(0,100)/100.0)
        while True:
            network.send("transport_pos_relative", random.randrange(-8000,8000))
            time.sleep(random.randrange(0,3))
            network.send("layer_speed", random.randrange(0,10000) /1000.0)
            time.sleep(random.randrange(0,3))
            network.send("layer_1_volume", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("layer_2_volume", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("layer_3_volume", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("layer_4_volume", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("layer_5_volume", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_1_db_harmonic", random.randrange(0,16))
            time.sleep(random.randrange(0,3))
            network.send("voice_1_db_fine", random.randrange(-50,50))
            time.sleep(random.randrange(0,3))
            network.send("voice_1_db_h1_harmonic", random.randrange(0,16))
            time.sleep(random.randrange(0,3))
            network.send("voice_1_db_h1_fine", random.randrange(-50,50))
            time.sleep(random.randrange(0,3))
            network.send("voice_1_db_h1_vol", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_1_db_h2_harmonic", random.randrange(0,16))
            time.sleep(random.randrange(0,3))
            network.send("voice_1_db_h2_fine", random.randrange(-50,50))
            time.sleep(random.randrange(0,3))
            network.send("voice_1_db_h2_vol", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_1_db_filter_a", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_1_db_filter_b", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))

            network.send("voice_2_db_harmonic", random.randrange(0,16))
            time.sleep(random.randrange(0,3))
            network.send("voice_2_db_fine", random.randrange(-50,50))
            time.sleep(random.randrange(0,3))
            network.send("voice_2_db_h1_harmonic", random.randrange(0,16))
            time.sleep(random.randrange(0,3))
            network.send("voice_2_db_h1_fine", random.randrange(-50,50))
            time.sleep(random.randrange(0,3))
            network.send("voice_2_db_h1_vol", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_2_db_h2_harmonic", random.randrange(0,16))
            time.sleep(random.randrange(0,3))
            network.send("voice_2_db_h2_fine", random.randrange(-50,50))
            time.sleep(random.randrange(0,3))
            network.send("voice_2_db_h2_vol", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_2_db_filter_a", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_2_db_filter_b", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))

            network.send("voice_3_db_harmonic", random.randrange(0,16))
            time.sleep(random.randrange(0,3))
            network.send("voice_3_db_fine", random.randrange(-50,50))
            time.sleep(random.randrange(0,3))
            network.send("voice_3_db_h1_harmonic", random.randrange(0,16))
            time.sleep(random.randrange(0,3))
            network.send("voice_3_db_h1_fine", random.randrange(-50,50))
            time.sleep(random.randrange(0,3))
            network.send("voice_3_db_h1_vol", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_3_db_h2_harmonic", random.randrange(0,16))
            time.sleep(random.randrange(0,3))
            network.send("voice_3_db_h2_fine", random.randrange(-50,50))
            time.sleep(random.randrange(0,3))
            network.send("voice_3_db_h2_vol", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_3_db_filter_a", random.randrange(0,100)/100.0)
            time.sleep(random.randrange(0,3))
            network.send("voice_3_db_filter_b", random.randrange(0,100)/100.0)
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

