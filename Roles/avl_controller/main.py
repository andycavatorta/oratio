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

network = None # for global
dispatcher = None # for global

class Dispatcher(threading.Thread):
    def __init__(self, network):
        threading.Thread.__init__(self)
        self.network = network
        self.all_topics_initialized = False

        self.pitch_key_event = None
        self.transport_pos_relative = None
        self.voices = [
            {
                "voice_key_position":None,
                "db_harmonic":None,
                "db_fine":None,
                "db_h1_harmonic":None,
                "db_h1_fine":None,
                "db_h1_vol":None,
                "db_h2_harmonic":None,
                "db_h2_fine":None,
                "db_h2_vol":None,
                "db_filter_a":None,
                "db_filter_b":None
            }
        ] *3
        self.layer_speed = None
        self.layer_1_volume = None
        self.layer_2_volume = None
        self.layer_3_volume = None
        self.layer_4_volume = None
        self.layer_5_volume = None

    def check_if_all_values_initialized(self):
        try:
            assert self.transport_pos_relative != None
            assert self.layer_speed != None
            assert self.layer_1_volume != None
            assert self.layer_2_volume != None
            assert self.layer_3_volume != None
            assert self.layer_4_volume != None
            assert self.layer_5_volume != None
            assert self.pitch_key_event != None
            for v in self.voices:
                assert v["voice_key_position"] != None
                assert v["db_harmonic"] != None
                assert v["db_fine"] != None
                assert v["db_h1_harmonic"] != None
                assert v["db_h1_fine"] != None
                assert v["db_h1_vol"] != None
                assert v["db_h2_harmonic"] != None
                assert v["db_h2_fine"] != None
                assert v["db_h2_vol"] != None
                assert v["db_filter_a"] != None
                assert v["db_filter_b"] != None
            self.all_topics_initialized = True
        except:
            self.all_topics_initialized = False

    def normalize_transport(self):
        pass

    def calculate_base_pitch(self, pitch_key, transport_pos):
        return


    def calculate_harmonic_pitch(self, base_pitch, db_h2_harmonic, db_h2_fine):
        return


    def calculate_harmonic_volume(self, base_volume, harm_voluime):
        return


    def calculate_voice_data(self,voice_num):
        voice_1_base_pitch = self.calculate_base_pitch(self.pitch_key_event, self.transport_pos, self.voice_1_db_harmonic, self.voice_1_db_fine)
        voice_1_harmonic_1_pitch = self.calculate_harmonic_pitch(voice_1_base_pitch, self.voice_1_db_h1_harmonic, self.voice_1_db_h1_fine)
        voice_1_harmonic_2_pitch = self.calculate_harmonic_pitch(voice_1_base_pitch, self.voice_1_db_h2_harmonic, self.voice_1_db_h2_fine)
        voice_1_base_volume = self.self.voice_key_1_position
        voice_1_harmonic_1_volume = self.calculate_harmonic_volume(voice_1_base_volume, self.voice_1_db_h1_vol)
        voice_1_harmonic_2_volume = self.calculate_harmonic_volume(voice_1_base_volume, self.voice_1_db_h2_vol)
        return [voice_1_base_pitch, voice_1_base_volume, voice_1_harmonic_1_pitch, voice_1_harmonic_1_volume, voice_1_harmonic_2_pitch,voice_1_harmonic_2_volume]

    def updateValue(self, name, val):
        print "updateValue", name, val

    def run(self):
        while self.all_topics_initialized == False:
            self.check_if_all_values_initialized()
            sleep(1)
        while True:

            transport_pos = self.normalize_transport(self.pitch_key_event, self.transport_pos_relative)

            network.send("voice_1", calculate_voice_data(0))
            network.send("voice_2", calculate_voice_data(1))
            network.send("voice_3", calculate_voice_data(2))
            #network.send("filter_1", [self.voices[0]["db_filter_a"],self.voices[0]["db_filter_b"]])
            #network.send("filter_2", [self.voices[1]["db_filter_a"],self.voices[1]["db_filter_b"]])
            #network.send("filter_3", [self.voices[2]["db_filter_a"],self.voices[2]["db_filter_b"]])

def network_status_handler(msg):
    print "network_status_handler", msg


def network_message_handler(msg):
    try:
        print "network_message_handler", msg
        topic = msg[0]
        if topic == "__heartbeat__":
            print "heartbeat received", msg
        if topic in [
            "system",
            "voice_key_1_position",
            "voice_key_2_position",
            "voice_key_3_position",
            "pitch_key_event",
            "transport_pos_relative",
            "layer_speed",
            "layer_1_volume",
            "layer_2_volume",
            "layer_3_volume",
            "layer_4_volume",
            "layer_5_volume",
            "voice_1_db_harmonic",
            "voice_1_db_fine",
            "voice_1_db_h1_harmonic",
            "voice_1_db_h1_fine",
            "voice_1_db_h1_vol",
            "voice_1_db_h2_harmonic",
            "voice_1_db_h2_fine",
            "voice_1_db_h2_vol",
            "voice_1_db_filter_a",
            "voice_1_db_filter_b",
            "voice_2_db_harmonic",
            "voice_2_db_fine",
            "voice_2_db_h1_harmonic",
            "voice_2_db_h1_fine",
            "voice_2_db_h1_vol",
            "voice_2_db_h2_harmonic",
            "voice_2_db_h2_fine",
            "voice_2_db_h2_vol",
            "voice_2_db_filter_a",
            "voice_2_db_filter_b",
            "voice_2_db_harmonic",
            "voice_2_db_fine",
            "voice_2_db_h1_harmonic",
            "voice_2_db_h1_fine",
            "voice_2_db_h1_vol",
            "voice_2_db_h2_harmonic",
            "voice_2_db_h2_fine",
            "voice_2_db_h2_vol",
            "voice_2_db_filter_a",
            "voice_2_db_filter_b"
        ]:
            global dispatcher
            dispatcher.updateValue(topic, msg[0])
        #print "topic", topic 
    except Exception as e:
        print "exception in network_message_handler", e


def init(HOSTNAME):
    global network
    global dispatcher
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

    dispatcher = Dispatcher(network)
    dispatcher.start()
