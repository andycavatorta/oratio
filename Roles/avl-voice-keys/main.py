from __future__ import division

import test_that_works
import AMT203
import os
import Queue
import settings
import time
import threading
import traceback
import sys

from thirtybirds_2_0.Network.manager import init as network_init
#from thirtybirds_2_0.Adaptors.Sensors import AMT203_expanded_spi

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
        self.resolution = 4096
        print "Voice_Key.__init__ 0", spi_chip_select_pin
        self.encoder = AMT203.AMT203(0, 0, spi_chip_select_pin)
        print "Voice_Key.__init__ 1", self.encoder
        time.sleep(1)
        self.encoder.set_zero()
        print "Voice_Key.__init__ 2"
        self.last_encoder_postion = self.encoder.get_position()
        print "Voice_Key initialized with spi_chip_select_pin", spi_chip_select_pin
    def normalize(self, encoder_value):
        if encoder_value < 2000:
            encoder_value = self.resolution
        inverse_value = self.resolution - encoder_value
        #print "normalize 0", encoder_value, inverse_value
        if inverse_value <= self.min_encoder_position:
            inverse_value = self.min_encoder_position
            #print "normalize 1", inverse_value
        if inverse_value > self.max_encoder_position:
            inverse_value = self.max_encoder_position
            #print "normalize 2", inverse_value
        ranged_value = inverse_value / (self.max_encoder_position - self.min_encoder_position)
        #print "normalize 3", ranged_value
        return ranged_value
    def get_value(self):
        current_encoder_position = self.encoder.get_position()
        if current_encoder_position != self.last_encoder_postion:
            self.last_encoder_postion = current_encoder_position
            return self.normalize(current_encoder_position)
        else:
            return None

class Voice_Keys():
    def __init__(self):
        spi_chip_select_pins = [16, 20 ,21 ]
        min_encoder_positions = [0, 0, 0]
        max_encoder_positions = [100.0, 100.0, 100.0]
        self.voice_keys = [ Voice_Key(spi_chip_select_pins[key_number], min_encoder_positions[key_number], max_encoder_positions[key_number]) for key_number in range(3) ]
    def get_positions(self):
        voice_key_new_positions = []
        for key_number, voice_key in enumerate(self.voice_keys):
            voice_key_new_position = voice_key.get_value()
            if voice_key_new_position is not None:
                voice_key_new_positions.append((key_number, voice_key_new_position))
        return voice_key_new_positions

class Button(object):
    def __init__(self, name, pin):
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
    def __init__(self, defs):
        self.buttons = [ Button(defs[i][0], defs[i][1]) for i in range(len(defs)) ]
    def get_states(self):
        button_states = []
        for button in self.buttons:
            name, state = button.get_state()
            if state is not None:
                button_states.append((name, state))
        return button_states

# Main handles network send/recv and can see all other classes directly
class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.voice_keys = Voice_Keys()
        defs = [
            ("hold", 26),
            ("staccato_3", 19),
            ("staccato_2", 06),
            ("staccato_1", 13),
        ]
        self.buttons = Buttons(defs)
        self.hold = False
        self.staccato_1 = False
        self.staccato_2 = False
        self.staccato_3 = False
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
                button_states = self.buttons.get_states()
                for button_state in button_states:
                    name, state = button_state
                    if name == "hold":
                        self.hold = True if state == 0 else False
                    if name == "staccato_1":
                        self.staccato_1 = True if state == 0 else False
                    if name == "staccato_2":
                        self.staccato_2 = True if state == 0 else False
                    if name == "staccato_3":
                        self.staccato_3 = True if state == 0 else False

                if not self.hold:
                    voice_key_positions = self.voice_keys.get_positions()
                    for voice_key_position in voice_key_positions:
                        key_number, voice_key_new_position = voice_key_position
                        if key_number == 0 and self.staccato_1:
                            voice_key_new_position = 1.0 if voice_key_new_position >= 0.05 else 0.0
                        if key_number == 1 and self.staccato_2:
                            voice_key_new_position = 1.0 if voice_key_new_position >= 0.05 else 0.0
                        if key_number == 2 and self.staccato_3:
                            voice_key_new_position = 1.0 if voice_key_new_position >= 0.05 else 0.0
                        print key_number, voice_key_new_position
                        #print "button:", name, state
                        #print "button_states:", button_states
                        self.network.thirtybirds.send(topic_names[key_number], voice_key_new_position)

                time.sleep(0.01)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))

def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main
