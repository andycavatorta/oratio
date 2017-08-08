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

import crystal_helpers as c

from thirtybirds_2_0.Network.manager import init as network_init
from thirtybirds_2_0.Network.email_simple import init as email_init

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
THIRTYBIRDS_PATH = "%s/thirtybirds" % (UPPER_PATH )

sys.path.append(BASE_PATH)
sys.path.append(UPPER_PATH)

global last_f1
global last_f2
global last_f3

offset = 95839.5
# offset = 95711
#offset = 95945.1

"""
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
"""

class FPGA():
    def __init__(
        self, 
        spi_chipeselect, 
        spi_masterslave
    ):
        self.spi_chipeselect = spi_chipeselect
        self.spi_masterslave = spi_masterslave
        self.spi_connection = None # to do
        # create SPI connection
    def send(self, filter_a, filter_b):
        #self.spi_connection.send
        print "FPGA: ", filter_a, filter_b

class TONE():
    def __init__(
        self, 
        spi_chipeselect_for_dac, 
        spi_masterslave_for_dac
    ):
        self.spi_chipeselect_for_dac = spi_chipeselect_for_dac
        self.spi_masterslave_for_dac = spi_masterslave_for_dac
        self.spi_connection = None # to do

    def send(self, freq, vol):
        #self.spi_connection.send
        print "TONE: ", freq, vol

# class TONES():
#     def __init__(
#         self, 
#         spi_chipeselect_for_dac_1, 
#         spi_masterslave_for_dac_1,
#         spi_chipeselect_for_dac_2, 
#         spi_masterslave_for_dac_2,
#         spi_chipeselect_for_dac_3, 
#         spi_masterslave_for_dac_3,
#         spi_chipeselect_for_fpga, 
#         spi_masterslave_for_fpga
#     ):
#         self.tone_1 = TONE(spi_chipeselect_for_dac_1, spi_masterslave_for_dac_1)
#         self.tone_2 = TONE(spi_chipeselect_for_dac_2 , spi_masterslave_for_dac_2)
#         self.tone_3 = TONE(spi_chipeselect_for_dac_3, spi_masterslave_for_dac_3)
#         self.fpga = FPGA(spi_chipeselect_for_fpga,spi_masterslave_for_fpga)

#     def send(self, multi_msg):
#         self.tone_1.send(multi_msg[0],multi_msg[1])
#         self.tone_2.send(multi_msg[2],multi_msg[3])
#         self.tone_3.send(multi_msg[4],multi_msg[5])
#         self.fpga.send(multi_msg[6],multi_msg[7])

# tones = TONES(
#         , #spi_chipeselect_for_dac_1, 
#         0, #spi_masterslave_for_dac_1,
#         , #spi_chipeselect_for_dac_2, 
#         0, #spi_masterslave_for_dac_2,
#         , #spi_chipeselect_for_dac_3, 
#         0, #spi_masterslave_for_dac_3,
#         , #spi_chipeselect_for_fpga, 
#          #spi_masterslave_for_fpga
# )

def network_status_handler(msg):
    print "network_status_handler", msg

def network_message_handler(msg):
    global offset 
    print "network_message_handler", msg
    topic = msg[0]
    #host, sensor, data = yaml.safe_load(msg[1])
    if topic == "__heartbeat__":
        print "heartbeat received", msg
    
    if topic == "voice_2":
        # tones.send(eval(msg[1]))
        global offset
        # quick hack -- will make this better later!
        payload = eval(msg[1])
        freq_1, gain, freq_2, vol_2, freq_3, vol_3, cutoff_raw, pband = payload
        #offset = 95925.1
        #print offset-int(payload[0])


        c.send_freq(0, offset-int(freq_1))
        c.send_freq(1, offset-int(freq_2))
        c.send_freq(2, offset-int(freq_3))
        #c.set_levels(0, 255 if payload[1] < 0.5 else int(180.0 * payload[1]))
        c.set_levels(0, 0 if payload[1] < 0.1 else int(240.0 * payload[1]))
        c.set_levels(1, 0 if vol_2 < 0.1 else int(255.0 * vol_2))
        c.set_levels(2, 0 if vol_3 < 0.1 else int(255.0 * vol_3))

        cutoff_freq = (cutoff_raw - 0.5) * freq_1 + freq_1
        adj_period = 1e6 / (cutoff_freq * 100)
        c.pport_write(1, adj_period)
        c.pband_size(pband/255)

        """
        if (payload[1] > 0.2):
            c.send_freq(0, offset-int(freq_1))
            c.send_freq(1, offset-int(freq_2))
            c.send_freq(2, offset-int(freq_3))
            #c.set_levels(0, 255 if payload[1] < 0.5 else int(180.0 * payload[1]))
            c.set_levels(0, 0 if payload[1] < 0.1 else int(180.0 * payload[1]))
            c.set_levels(1, 0 if vol_2 < 0.1 else int(255.0 * vol_2))
            c.set_levels(2, 0 if vol_3 < 0.1 else int(255.0 * vol_3))
        else:
            c.send_freq(0, 0)
            c.send_freq(1, 0)
            c.send_freq(2, 0)
        """
network = None # makin' it global

def init(HOSTNAME):
    c.init()

    c.send_freq(0, 0)
    c.send_freq(1, 0)
    c.send_freq(2, 0)

    c.set_levels(0, 0)
    c.set_levels(1, 0)
    c.set_levels(2, 0)

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
    network.subscribe_to_topic("voice_2")
    #main = Main(HOSTNAME)
    #main.start()
