"""
TASKS:
    init:
        maintain SSH tunnel to conductor
        listen to Web API
        open DB connection
    runtime:
        maintain DB of inventory histories?
        generate HTML reports
        serve reports on request

API for conductor:
    receive_inventory_and_map

Dashboard:
    web interface
    websocket push
    status of all camera_units
        connected
        current status ( color coded )
        inventory
        exceptions

"""




import importlib
import json
import os
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
        ### NETWORK ###

        ### SET UP SUBSCRIPTIONS AND LISTENERS ###

        ### SET UP ATTAR ### so any exceptions can be reported

    def run(self):
        while True:
            time.sleep(60)

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
    network.subscribe_to_topic("voice_3")  
    #network.subscribe_to_topic("sensor_data")  
    main = Main(HOSTNAME)
    main.start()

