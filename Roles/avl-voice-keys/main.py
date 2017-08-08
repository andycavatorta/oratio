from __future__ import division

import os
import Queue
import settings
import time
import threading

from thirtybirds_2_0.Network.manager import init as network_init
from thirtybirds_2_0.Adaptors.Sensors import AMT203_expanded_spi

import RPi.GPIO as GPIO  
GPIO.setmode(GPIO.BCM)  

class Network(object):
    def __init__(self, hostname, network_message_handler, network_status_handler):
        self.hostname = hostname
        self.thirtybirds = network_init(
            hostname=hostname,
            role="client",
            discovery_multicastGroup=settings.discovery_multicastGroup,
            discovery_multicastPort=settings.discovery_multicastPort,
            discovery_responsePort=settings.discovery_responsePort,
            pubsub_pubPort=settings.pubsub_pubPort,
            message_callback=network_message_handler,
            status_callback=network_status_handler
        )

class Voice_Key(object):
    def __init__(self, spi_chip_select_pin, min_encoder_position, max_encoder_position):
        self.min_encoder_position = min_encoder_position
        self.max_encoder_position = max_encoder_position
        print "Voice_Key.__init__ 0", spi_chip_select_pin
        self.encoder = AMT203_expanded_spi.AMT203(0, 0, spi_chip_select_pin)
        print "Voice_Key.__init__ 1", self.encoder
        time.sleep(1)
        self.encoder.set_zero()
        print "Voice_Key.__init__ 2"
        self.last_encoder_postion = self.encoder.get_position()
        print "Voice_Key initialized with spi_chip_select_pin", spi_chip_select_pin
    def get_value(self):
        #print "Voice_Key.get_value started"
        current_encoder_position = self.encoder.get_position()
        #print "Voice_Key.get_value value"
        if current_encoder_position != self.last_encoder_postion:
            self.last_encoder_postion = current_encoder_position
            # next, calculate adjusted position
            return current_encoder_position
        else:
            return None

class Voice_Keys():
    def __init__(self):
        spi_chip_select_pins = [20,21,16]
        min_encoder_positions = [0, 0, 0]
        max_encoder_positions = [100, 100, 100]
        self.voice_keys = [ Voice_Key(spi_chip_select_pins[key_number], min_encoder_positions[key_number], max_encoder_positions[key_number]) for key_number in range(3) ]
    def get_positions(self):
        #print "Voice_Keys.get_positions"
        voice_key_new_positions = []
        for key_number, voice_key in enumerate(self.voice_keys):
            voice_key_new_position = voice_key.get_value()
            if voice_key_new_position is not None:
                voice_key_new_positions.append((key_number, voice_key_new_position))
        return voice_key_new_positions

class Button(object):
    def __init__(self, name, pin):
        print "----------->",name, pin
        self.name = name
        self.pin = pin
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
        self.last_state = None # so this always returns something on first query
    def get_state(self):
        current_state = GPIO.input(self.pin)
        if current_state == self.last_state:
            return (self.name, None)
        else:
            self.last_state = current_state
            return (self.name, GPIO.input(self.pin))

class Buttons(object):
    def __init__(self):
        defs = (
            ("hold", 26)
        )
        self.buttons = [ Button(defs[i][0], defs[i][1]) for i in range(len(defs)) ]
    def get_states(self):
        for button in self.buttons:
            name, state = button.get_state()
            print name, state


# Main handles network send/recv and can see all other classes directly
class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.voice_keys = Voice_Keys()
        self.buttons = Buttons()
        #self.network.thirtybirds.subscribe_to_topic("door_closed")

    def network_message_handler(self, topic_msg):
        # this method runs in the thread of the caller, not the tread of Main
        topic, msg =  topic_msg # separating just to eval msg.  best to do it early.  it should be done in TB.
        if len(msg) > 0: 
            msg = eval(msg)
        self.add_to_queue(topic, msg)

    def network_status_handler(self, topic_msg):
        # this method runs in the thread of the caller, not the tread of Main
        print "Main.network_status_handler", topic_msg

    def add_to_queue(self, topic, msg):
        self.queue.put((topic, msg))

    def run(self):
        topic_names = ["voice_key_1_position", "voice_key_2_position", "voice_key_3_position"]
        while True:
            try:
                voice_key_positions = self.voice_keys.get_positions()
                for voice_key_position in voice_key_positions:
                    key_number, voice_key_new_position = voice_key_position
                    print key_number, voice_key_new_position
                    #self.network.thirtybirds.send(topic_names[key_number], voice_key_position)
                self.buttons.get_states()

                time.sleep(0.1)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))

def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main

