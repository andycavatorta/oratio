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


import time
import threading
import settings
import yaml
import json

from thirtybirds_2_0.Logs.main import Exception_Collector
from thirtybirds_2_0.Network.manager import init as network_init


def network_status_handler(msg):
    print "network_status_handler", msg


def network_message_handler(msg):
    try:
        print "network_message_handler", msg
        topic = msg[0]
        #print "topic", topic 
        if topic == "__heartbeat__":
            print "heartbeat received", msg
    except Exception as e:
        print "exception in network_message_handler", e

network = None

def init(HOSTNAME):
    global network
    network = network_init(
        hostname=HOSTNAME,
        role="server",
        discovery_multicastGroup=settings.discovery_multicastGroup,
        discovery_multicastPort=settings.discovery_multicastPort,
        discovery_responsePort=settings.discovery_responsePort,
        pubsub_pubPort=settings.pubsub_pubPort,
        message_callback=network_message_handler,
        status_callback=network_status_handler
    )
    network.subscribe_to_topic("system")  # subscribe to all system messages
    network.subscribe_to_topic("voice_key_1_position")  
    network.subscribe_to_topic("voice_key_2_position")
    network.subscribe_to_topic("voice_key_3_position")
    network.subscribe_to_topic("pitch_key_event")

    network.subscribe_to_topic("transport_pos_relative")
    network.subscribe_to_topic("layer_speed")
    network.subscribe_to_topic("layer_1_volume")
    network.subscribe_to_topic("layer_2_volume")
    network.subscribe_to_topic("layer_3_volume")
    network.subscribe_to_topic("layer_4_volume")
    network.subscribe_to_topic("layer_5_volume")
    
    network.subscribe_to_topic("voice_1_db_harmonic")
    network.subscribe_to_topic("voice_1_db_fine")
    network.subscribe_to_topic("voice_1_db_h1_harmonic")
    network.subscribe_to_topic("voice_1_db_h1_fine")
    network.subscribe_to_topic("voice_1_db_h1_vol")
    network.subscribe_to_topic("voice_1_db_h2_harmonic")
    network.subscribe_to_topic("voice_1_db_h2_fine")
    network.subscribe_to_topic("voice_1_db_h2_vol")
    network.subscribe_to_topic("voice_1_db_filter_a")
    network.subscribe_to_topic("voice_1_db_filter_b")

    network.subscribe_to_topic("voice_2_db_harmonic")
    network.subscribe_to_topic("voice_2_db_fine")
    network.subscribe_to_topic("voice_2_db_h1_harmonic")
    network.subscribe_to_topic("voice_2_db_h1_fine")
    network.subscribe_to_topic("voice_2_db_h1_vol")
    network.subscribe_to_topic("voice_2_db_h2_harmonic")
    network.subscribe_to_topic("voice_2_db_h2_fine")
    network.subscribe_to_topic("voice_2_db_h2_vol")
    network.subscribe_to_topic("voice_2_db_filter_a")
    network.subscribe_to_topic("voice_2_db_filter_b")

    network.subscribe_to_topic("voice_2_db_harmonic")
    network.subscribe_to_topic("voice_2_db_fine")
    network.subscribe_to_topic("voice_2_db_h1_harmonic")
    network.subscribe_to_topic("voice_2_db_h1_fine")
    network.subscribe_to_topic("voice_2_db_h1_vol")
    network.subscribe_to_topic("voice_2_db_h2_harmonic")
    network.subscribe_to_topic("voice_2_db_h2_fine")
    network.subscribe_to_topic("voice_2_db_h2_vol")
    network.subscribe_to_topic("voice_2_db_filter_a")
    network.subscribe_to_topic("voice_2_db_filter_b")
