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
import RPi.GPIO as GPIO
import settings 
import sys
import threading
import time
import wiringpi as wpi

from thirtybirds_2_0.Network.manager import init as network_init
from thirtybirds_2_0.Network.email_simple import init as email_init
#from thirtybirds_2_0.Adaptors.ADC import TLC1543IN

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
THIRTYBIRDS_PATH = "%s/thirtybirds" % (UPPER_PATH )

sys.path.append(BASE_PATH)
sys.path.append(UPPER_PATH)


class TLC1543():
    def __init__(self, spi_chip_select=0, spi_master_slave=0):
        self.spi_master_slave = spi_master_slave
        self.spi_chip_select = spi_chip_select

    def read(self, channel):
        return random.randrange(0,1000)

class Drawbar():
    def __init__(self, spi_chip_select, spi_master_slave,channels):
        self.channels = channels
        # channels format: {"name":"", "detent_adc_values": [ 234,345,... closest values]} OR {"name":"", "min": (int), "max": (int), }
        for channel in channels:
            channel.update( {"last_value":0})
        self.spi_chip_select = spi_chip_select
        self.spi_master_slave = spi_master_slave
        self.channels = channels
        #self.adc = TLC1543(self.spi_chip_select, self.spi_master_slave)

    def detent_from_adc_value(self, channel_num, val):
        return self.channels[channel_num]["detent_adc_values"].index(min(self.channels[channel_num]["detent_adc_values"], key=lambda x:abs(x-val)))

    def normalize_adc_value_to_min_max(self, channel_num, val):
        channel_range = self.channels[channel_num]["max"] - self.channels[channel_num]["min"]
        val_with_min_offset = val - self.channels[channel_num]["min"]
        value_normalized = float(val_with_min_offset) / float(channel_range)
        value_normalized = value_normalized if value_normalized > 0.0 else 0.0
        value_normalized = value_normalized if value_normalized < 1.0 else 1.0
        return 1.0 - value_normalized

    def spi_read_write(self,pin, msg):
        wpi.digitalWrite(pin, 0); wpi.delayMicroseconds(1)
        msg = wpi.wiringPiSPIDataRW(0, msg)
        wpi.delayMicroseconds(1)
        wpi.digitalWrite(pin, 1); wpi.delayMicroseconds(1)
        return msg

    def read_channel(self, cs, ch):
        self.spi_read_write(cs, chr(ch << 4) + chr(0x00))
        val = self.spi_read_write(cs, chr(0x00) + chr(0x00))
        return (ord(val[1][0]) << 2) | (ord(val[1][1]) >> 6)

    def read_avg(self, cs, ch, n=20):
        return sum([self.read_channel(cs, ch) for i in xrange(n)]) / n

    def scan(self):
        #print "running scan"
        for channel_num, channel in enumerate(self.channels):
            adc_value = self.read_avg(self.spi_chip_select, channel_num)
            if "detent_adc_values" in channel:
                detent = self.detent_from_adc_value(channel_num, adc_value)
                if detent != channel["last_value"]:
                    channel["last_value"] = detent
                    print channel["name"], detent
                    network.send(channel["name"], detent)
            else:
                value_normalised = self.normalize_adc_value_to_min_max(channel_num, adc_value)
                if abs(value_normalised - channel["last_value"])>0.07:
                #if value_normalised != channel["last_value"]:
                    channel["last_value"] = value_normalised
                    print channel["name"], value_normalised
                    network.send(channel["name"], value_normalised)
            time.sleep(0.01)

class Drawbars(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.chip_select_pins = [27, 28]
        self.drawbars = []
        wpi.wiringPiSetup()
        wpi.wiringPiSPISetupMode(0, 500000, 0)
        for pin in self.chip_select_pins:
            wpi.pinMode(pin, wpi.OUTPUT)

        self.drawbars.append(
            Drawbar(self.chip_select_pins[0], 0, 
                [
                    {
                        "name":"voice_1_db_harmonic", 
                        "detent_adc_values": [1022, 1008, 950, 888, 833, 760, 705, 640, 579]
                    },
                    {
                        "name":"voice_1_db_fine", 
                        "min":60, 
                        "max":998
                    },
                    {
                        "name":"voice_1_db_h1_fine", 
                        "min":50, 
                        "max":950
                    },
                    {
                        "name":"voice_1_db_h1_harmonic", 
                        "detent_adc_values":[1022, 1012, 972, 956, 844, 793, 733, 674, 582]
                    },
                    {
                        "name":"voice_1_db_h1_vol", 
                        "min":50, 
                        "max":987
                    },
                    {
                        "name":"voice_1_db_h2_fine", 
                        "min":54, 
                        "max":1010
                    },
                    {
                        "name":"voice_1_db_h2_harmonic", 
                        "detent_adc_values":[1021, 1011, 980, 932, 843, 806, 708,669, 594]
                    },
                    {
                        "name":"voice_1_db_h2_vol", 
                        "min":39, 
                        "max":1008
                    },
                    {
                        "name":"voice_1_db_filter_a", 
                        "min":55, 
                        "max":1008
                    },
                    {
                        "name":"voice_1_db_filter_b", 
                        "min":76, 
                        "max":1009
                    },
                ]
            )
        )
        self.drawbars.append(
            Drawbar(self.chip_select_pins[1], 0, 
                [
                    {
                        "name":"voice_2_db_harmonic", 
                        "detent_adc_values": [997, 978, 915, 858, 803, 742,666, 624,545]
                    },
                    {
                        "name":"voice_2_db_fine", 
                        "min":28, 
                        "max":994
                    },
                    {
                        "name":"voice_2_db_h1_fine", 
                        "min":23, 
                        "max":985
                    },
                    {
                        "name":"voice_2_db_h1_harmonic", 
                        "detent_adc_values":[997, 968, 939, 894, 806, 731, 682,627, 550]
                    },
                    {
                        "name":"voice_2_db_h1_vol", 
                        "min":35, 
                        "max":1007
                    },
                    {
                        "name":"voice_2_db_h2_fine", 
                        "min":15, 
                        "max":969
                    },
                    {
                        "name":"voice_2_db_h2_harmonic", 
                        "detent_adc_values":[979, 950, 922 ,907, 824, 719, 690,628, 548]
                    },
                    {
                        "name":"voice_2_db_h2_vol", 
                        "min":68, 
                        "max":1002
                    },
                    {
                        "name":"voice_2_db_filter_a", 
                        "min":52, 
                        "max":1002
                    },
                    {
                        "name":"voice_2_db_filter_b", 
                        "min":47, 
                        "max":1004
                    },
                ]
            )
        )
        self.drawbars.append(
            Drawbar(self.chip_select_pins[2], 0, 
                [
                    {
                        "name":"voice_2_db_harmonic", 
                        "detent_adc_values": [50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800]
                    },
                    {
                        "name":"voice_2_db_fine", 
                        "min":100, 
                        "max":800
                    },
                    {
                        "name":"voice_2_db_h1_harmonic", 
                        "detent_adc_values":[50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800]
                    },
                    {
                        "name":"voice_2_db_h1_fine", 
                        "min":100, 
                        "max":800
                    },
                    {
                        "name":"voice_2_db_h1_vol", 
                        "min":100, 
                        "max":800
                    },
                    {
                        "name":"voice_2_db_h2_harmonic", 
                        "detent_adc_values":[50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800]
                    },
                    {
                        "name":"voice_2_db_h2_fine", 
                        "min":100, 
                        "max":800
                    },
                    {
                        "name":"voice_2_db_h2_vol", 
                        "min":100, 
                        "max":800
                    },
                    {
                        "name":"voice_2_db_filter_a", 
                        "min":100, 
                        "max":800
                    },
                    {
                        "name":"voice_2_db_filter_a", 
                        "min":100, 
                        "max":800
                    },
                ]
            )
        )

    def set_chip_select(self, selected_pin):
        for pin in self.chip_select_pins:
            GPIO.output(pin, GPIO.LOW)
        GPIO.output(selected_pin, GPIO.HIGH)

    def run(self):
        while True:
            for ordinal, pin in enumerate(self.chip_select_pins):
                #self.set_chip_select(pin)
                self.drawbars[ordinal].scan()
                time.sleep(0.1)

"""
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

"""

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
    drawbars = Drawbars()
    drawbars.daemon = True
    drawbars.start()

