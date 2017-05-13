"""
inputs:
    3 SPI ADCs reading drawbars
    1 SPI ADC reading analog knobs
    
output topics:

    voice_1_db_harmonic
    voice_1_db_fine
    voice_1_db_h1_harmonic
    voice_1_db_h1_fine
    voice_1_db_h1_vol
    voice_1_db_h2_harmonic
    voice_1_db_h2_fine
    voice_1_db_h2_vol
    voice_1_db_filter_a
    voice_1_db_filter_b

    voice_2_db_harmonic
    voice_2_db_fine
    voice_2_db_h1_harmonic
    voice_2_db_h1_fine
    voice_2_db_h1_vol
    voice_2_db_h2_harmonic
    voice_2_db_h2_fine
    voice_2_db_h2_vol
    voice_2_db_filter_a
    voice_2_db_filter_b

    voice_3_db_harmonic
    voice_3_db_fine
    voice_3_db_h1_harmonic
    voice_3_db_h1_fine
    voice_3_db_h1_vol
    voice_3_db_h2_harmonic
    voice_3_db_h2_fine
    voice_3_db_h2_vol
    voice_3_db_filter_a
    voice_3_db_filter_b

    layer_speed
    layer_1_volume
    layer_2_volume
    layer_3_volume
    layer_4_volume
    layer_5_volume

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
from thirtybirds_2_0.Adaptors.ADC import TLC1543IN

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

class Drawbar(threading.Thread):
    def __init__(
        self, 
        spi_chip_select, 
        spi_master_slave,
        channels
        ):
        threading.Thread.__init__(self, chip_select_pin, channels)
        self.channels = channels
        # channels format: {"name":"", "detent_adc_values": [ 234,345,... closest values]} OR {"name":"", "min": (int), "max": (int), }
        for channel in channels:
            channel.update( {"last_value":0})
        self.spi_chip_select = spi_chip_select
        self.spi_master_slave = spi_master_slave
        self.channels = channels
        self.adc = TLC1543IN.TLC1543IN()

    def detent_from_adc_value(self, channel_num, val):
        return min(self.channels[channel_num]["detent_adc_values"], key=lambda x:abs(x-val))

    def normalize_adc_value_to_min_max(self, channel_num, val):
        channel_range = self.channels[channel_num]["max"] - self.channels[channel_num]["min"]
        val_with_min_offset = val - self.channels[channel_num]["min"]
        value_normalized = float(val_with_min_offset) / float(channel_range)
        return value_normalized

    def run(self):
        while True:
            for channel_num, channel in enumerate(self.channels):
                adc_value = self.adc(channel_num)
                if "detent_adc_values" in channel:
                    detent = self.detent_from_adc_value(channel_num, adc_value)
                    if detent != channel["last_value"]:
                        channel["last_value"] = detent
                        network.send(channel["name"], detent)
                else:
                    value_normalised = self.normalize_adc_value_to_min_max(channel_num, adc_value)
                    if value_normalised != channel["last_value"]:
                        channel["last_value"] = value_normalised
                        network.send(channel["name"], value_normalised)


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
    #network.subscribe_to_topic("sensor_data")  
    main = Main(HOSTNAME)
    main.start()


    voice_1_drawbar = Drawbar(0, 
            [
                {
                    "name":"voice_1_db_harmonic", 
                    "detent_adc_values": [50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800]
                },
                {
                    "name":"voice_1_db_fine", 
                    "min":100, 
                    "max":800
                },
                {
                    "name":"voice_1_db_h1_harmonic", 
                    "detent_adc_values":[50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800]
                },
                {
                    "name":"voice_1_db_h1_fine", 
                    "min":100, 
                    "max":800
                },
                {
                    "name":"voice_1_db_h1_vol", 
                    "min":100, 
                    "max":800
                },
                {
                    "name":"voice_1_db_h2_harmonic", 
                    "detent_adc_values":[50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800]
                },
                {
                    "name":"voice_1_db_h2_fine", 
                    "min":100, 
                    "max":800
                },
                {
                    "name":"voice_1_db_h2_vol", 
                    "min":100, 
                    "max":800
                },
                {
                    "name":"voice_1_db_filter_a", 
                    "min":100, 
                    "max":800
                },
                {
                    "name":"voice_1_db_filter_a", 
                    "min":100, 
                    "max":800
                },
            ]
        )
    voice_1_drawbar.start()
    # key_0 = Key("voice_key_1_position",0,0)
    # key_1 = Key("voice_key_2_position",0,1)
    # key_2 = Key("voice_key_3_position",1,1)
    # key_0.start()
    # time.sleep(5)
    # key_1.start()
    # time.sleep(5)
    # key_2.start()

############################################
###### PREVIOUS CODE FOR TRANSPORT #########
############################################

# """
# inputs:
#     4 ADC chips on I2C
#     1 rotary encoder on SPI
    
# output topics:
#     transport_pos_relative - integer from -8000 to 8000
#     layer_speed - seconds in float from 0.5 to 10.0 
#     layer_1_volume - float from 0.0 to 1.0
#     layer_2_volume - float from 0.0 to 1.0
#     layer_3_volume - float from 0.0 to 1.0
#     layer_4_volume - float from 0.0 to 1.0
#     layer_5_volume - float from 0.0 to 1.0

#     voice_1_db_harmonic - integer from 0 to 16 (?)
#     voice_1_db_fine - cents in integer from  -50 to +50
#     voice_1_db_h1_harmonic - integer from 0 to 16 (?)
#     voice_1_db_h1_fine - cents in integer from  -50 to +50
#     voice_1_db_h1_vol - float from 0.0 to 1.0
#     voice_1_db_h2_harmonic - integer from 0 to 16 (?)
#     voice_1_db_h2_fine - cents in integer from  -50 to +50
#     voice_1_db_h2_vol - float from 0.0 to 1.0
#     voice_1_db_filter_a - float from 0.0 to 1.0
#     voice_1_db_filter_b - float from 0.0 to 1.0

#     voice_2_db_harmonic - integer from 0 to 16 (?)
#     voice_2_db_fine - cents in integer from  -50 to +50
#     voice_2_db_h1_harmonic - integer from 0 to 16 (?)
#     voice_2_db_h1_fine - cents in integer from  -50 to +50
#     voice_2_db_h1_vol - float from 0.0 to 1.0
#     voice_2_db_h2_harmonic - integer from 0 to 16 (?)
#     voice_2_db_h2_fine - cents in integer from  -50 to +50
#     voice_2_db_h2_vol - float from 0.0 to 1.0
#     voice_2_db_filter_a - float from 0.0 to 1.0
#     voice_2_db_filter_b - float from 0.0 to 1.0

#     voice_3_db_harmonic - integer from 0 to 16 (?)
#     voice_3_db_fine - cents in integer from  -50 to +50
#     voice_3_db_h1_harmonic - integer from 0 to 16 (?)
#     voice_3_db_h1_fine - cents in integer from  -50 to +50
#     voice_3_db_h1_vol - float from 0.0 to 1.0
#     voice_3_db_h2_harmonic - integer from 0 to 16 (?)
#     voice_3_db_h2_fine - cents in integer from  -50 to +50
#     voice_3_db_h2_vol - float from 0.0 to 1.0
#     voice_3_db_filter_a - float from 0.0 to 1.0
#     voice_3_db_filter_b - float from 0.0 to 1.0

# """

# import importlib
# import json
# import os
# import Queue
# import random
# import settings 
# import sys
# import threading
# import time

# from thirtybirds_2_0.Network.manager import init as network_init
# from thirtybirds_2_0.Network.email_simple import init as email_init
# from thirtybirds_2_0.Adaptors.Sensors import AMT203

# BASE_PATH = os.path.dirname(os.path.realpath(__file__))
# UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
# DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
# THIRTYBIRDS_PATH = "%s/thirtybirds" % (UPPER_PATH )

# sys.path.append(BASE_PATH)
# sys.path.append(UPPER_PATH)


# class Main(threading.Thread):
#     def __init__(self, hostname):
#         threading.Thread.__init__(self)
#         self.hostname = hostname
#         self.queue = Queue.Queue()

#     def add_to_queue(self, topic, msg):
#         self.queue.put([topic, msg])

#     def run(self):
#         while True:
#             topic_msg = self.queue.get(True)
#             network.send(topic_msg[0], topic_msg[1])

# class Transport(threading.Thread):
#     def __init__(self, bus, deviceId):
#         threading.Thread.__init__(self)
#         self.bus = bus
#         self.deviceId = deviceId
#         print "creating amt203 object"
#         self.encoder = AMT203.AMT203(bus, deviceId)
#         print "setting zero ", self.bus, self.deviceId
#         self.encoder.set_zero()
#         print "after zero ", self.bus, self.deviceId 
#         self.last_position = self.encoder.get_position()
#         self.last_relative_position = int(self.last_position)
#         self.resolution = self.encoder.get_resolution()
#         self.gap = 2000
#         self.lap = 0
#         self.direction = None
#         print "class Transport instantiated with values", bus, deviceId

#     def get_relative_position(self):
#         current_position = self.encoder.get_position()
#         self.direction = True if (self.last_position < current_position and  current_position - self.last_position < self.gap) or  (self.last_position - current_position > self.gap) else False
#         if current_position < self.last_position and self.direction:
#             self.lap +=  1
#         elif self.last_position - current_position < 0 and not self.direction:
#             self.lap -= 1
#         self.last_position = current_position
#         return (self.lap*self.resolution) + current_position

#     def run(self):
#         print "class Transport thread started"
#         while True:
#             current_relative_position = self.get_relative_position()
#             if current_relative_position != self.last_relative_position:
#                 self.last_relative_position = current_relative_position
#                 main.add_to_queue("transport_pos_raw", current_relative_position)
#             time.sleep(0.01)


# def network_status_handler(msg):
#     print "network_status_handler", msg

# def network_message_handler(msg):
#     print "network_message_handler", msg
#     topic = msg[0]
#     #host, sensor, data = yaml.safe_load(msg[1])
#     if topic == "__heartbeat__":
#         print "heartbeat received", msg

# network = None # makin' it global
# main = None # also makin' it global

# def init(HOSTNAME):
#     global network
#     global main
#     network = network_init(
#         hostname=HOSTNAME,
#         role="client",
#         discovery_multicastGroup=settings.discovery_multicastGroup,
#         discovery_multicastPort=settings.discovery_multicastPort,
#         discovery_responsePort=settings.discovery_responsePort,
#         pubsub_pubPort=settings.pubsub_pubPort,
#         message_callback=network_message_handler,
#         status_callback=network_status_handler
#     )

#     network.subscribe_to_topic("system")  # subscribe to all system messages
#     #network.subscribe_to_topic("sensor_data")  
#     main = Main(HOSTNAME)
#     main.start()
#     transport = Transport(0,0)
#     transport.start()
