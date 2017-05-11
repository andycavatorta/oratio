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
import Adafruit_MPR121.MPR121 as MPR121
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

class MPR121Array(threading.Thread):
    def __init__(self, i2c_address):
        threading.Thread.__init__(self)
        position_raw = 0
        self.i2c_address = i2c_address
        self.capsensors = []
        self.last_touched = [0,0,0,0]
        self.last_global_position  = -1
        
        for sensor_id in range(4):
            self.capsensors.append(MPR121.MPR121())
            if not self.capsensors[sensor_id].begin(self.i2c_address[sensor_id]):
                print('Error initializing MPR121 @{}'.format(self.i2c_address[sensor_id]))
            print repr(self.capsensors[sensor_id])
        print "class CapSensorArray instantiated with values", self.i2c_address

    def run(self):
        print "class CapSensorArray thread started"
        for sensor_id in range(4):
            self.last_touched[sensor_id] = self.capsensors[sensor_id].touched()
            global_position = 1
        while True:
            for sensor_id in range(4):
                current_touched = self.capsensors[sensor_id].touched()
                for i in range(12):
                    pin_bit = 1 << i
                    if current_touched & pin_bit and not self.last_touched[sensor_id] & pin_bit:
                        print('{0} touched!'.format(i))
                        global_position = i + (12 * sensor_id)
                    if not current_touched & pin_bit and self.last_touched[sensor_id] & pin_bit:
                        print('{0} released!'.format(i))
                self.last_touched[sensor_id] = current_touched
            if global_position > 1 and self.last_global_position != global_position:
                main.add_to_queue("pitch_key_event", global_position)
                self.last_global_position = global_position
                time.sleep(0.01)

class Key(threading.Thread):
    def __init__(self, name, bus, deviceId):
        threading.Thread.__init__(self)
        self.name = name
        self.bus = bus
        self.deviceId = deviceId
        print "creating amt203 object"
        self.encoder = AMT203.AMT203(bus, deviceId)
        print "setting zero ", self.bus, self.deviceId
        self.encoder.set_zero()
        print "after zero ", self.bus, self.deviceId 
        print "class Key instantiated with values", name, bus, deviceId
        self.encoder_min = 0
        self.encoder_max = 100

    def run(self):
        print "class Key thread started"
        while True:
            pos = self.encoder.get_position()
            mapped_pos = self.map_key(self.name, pos)
            main.add_to_queue(self.name, mapped_pos)
            time.sleep(0.01)

    def map_key(self, name, value):
        value = encoder_max if value > encoder_max else value
        value = encoder_min if value < encoder_min else value
        mapped_value = (((value - encoder_min))/(encoder_max - encoder_min))
        return mapped_value

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
    mpr121array = MPR121Array([0x5a, 0x5b, 0x5c, 0x5d])
    mpr121array.start()
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
