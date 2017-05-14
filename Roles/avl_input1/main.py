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
            if global_position > 1:
                time.sleep(0.01)
                main.add_to_queue("pitch_key_event", global_position)

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
        self.encoder_min = 0.0
        self.encoder_max = 140.0
        self.last_pos = 0.0

    def run(self):
        print "class Key thread started"
        while True:
            pos = self.encoder.get_position()
            if self.last_pos != pos:
                mapped_pos = self.map_key(self.name, pos)
                main.add_to_queue(self.name, mapped_pos)
                self.last_pos = pos
            time.sleep(0.01)

    def map_key(self, name, value):
        value = value if value <= 1000 else 0
        value = value if value <= self.encoder_max else self.encoder_max
        value = value if value >= self.encoder_min else self.encoder_min 
        mapped_value = (((value - self.encoder_min))/(self.encoder_max - self.encoder_min))
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
    #mpr121array = MPR121Array([0x5a, 0x5b, 0x5c, 0x5d])
    #mpr121array.start()
    key_0 = Key("voice_key_3_position",0,0)
    key_1 = Key("voice_key_2_position",0,1)
    #key_2 = Key("voice_key_3_position",1,1)
    key_0.start()
    time.sleep(5)
    key_1.start()
    time.sleep(5)
    #key_2.start()

