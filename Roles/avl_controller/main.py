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
            print "0 >>>>>>>>>>>>>>>>>>>>>>"
            assert self.transport_pos_relative != None
            print "1 >>>>>>>>>>>>>>>>>>>>>>"
            assert self.layer_speed != None
            print "2 >>>>>>>>>>>>>>>>>>>>>>"
            assert self.layer_1_volume != None
            print "3 >>>>>>>>>>>>>>>>>>>>>>"
            assert self.layer_2_volume != None
            print "4 >>>>>>>>>>>>>>>>>>>>>>"
            assert self.layer_3_volume != None
            print "5 >>>>>>>>>>>>>>>>>>>>>>"
            assert self.layer_4_volume != None
            print "6 >>>>>>>>>>>>>>>>>>>>>>"
            assert self.layer_5_volume != None
            print "7 >>>>>>>>>>>>>>>>>>>>>>"
            assert self.pitch_key_event != None
            print "8 >>>>>>>>>>>>>>>>>>>>>>"
            for v in self.voices:
                print "9 >>>>>>>>>>>>>>>>>>>>>>"
                assert v["voice_key_position"] != None
                print "10 >>>>>>>>>>>>>>>>>>>>>>"
                assert v["db_harmonic"] != None
                print "11 >>>>>>>>>>>>>>>>>>>>>>"
                assert v["db_fine"] != None
                print "12 >>>>>>>>>>>>>>>>>>>>>>"
                assert v["db_h1_harmonic"] != None
                print "13 >>>>>>>>>>>>>>>>>>>>>>"
                assert v["db_h1_fine"] != None
                print "14 >>>>>>>>>>>>>>>>>>>>>>"
                assert v["db_h1_vol"] != None
                print "15 >>>>>>>>>>>>>>>>>>>>>>"
                assert v["db_h2_harmonic"] != None
                print "16 >>>>>>>>>>>>>>>>>>>>>>"
                assert v["db_h2_fine"] != None
                print "17 >>>>>>>>>>>>>>>>>>>>>>"
                assert v["db_h2_vol"] != None
                print "18 >>>>>>>>>>>>>>>>>>>>>>"
                assert v["db_filter_a"] != None
                print "19 >>>>>>>>>>>>>>>>>>>>>>"
                assert v["db_filter_b"] != None
                print "20 >>>>>>>>>>>>>>>>>>>>>>"
            self.all_topics_initialized = True
        except:
            self.all_topics_initialized = False

    def normalize_transport(self):
        pass

    def calculate_base_pitch(self, db_harmonic, db_fine):
        self.pitch_key_event
        self.transport_pos_relative
        return 300


    def calculate_harmonic_pitch(self, base_pitch, harmonic, fine):
        return 500


    def calculate_harmonic_volume(self, base_volume, harm_voluime):
        return 50


    def calculate_voice_data(self,voice_num):
        voice = self.voices[voice_num]
        base_pitch = self.calculate_base_pitch(voice.db_harmonic, voice.db_fine)
        harmonic_1_pitch = self.calculate_harmonic_pitch(base_pitch, voice.db_h1_harmonic, voice.db_h1_fine)
        harmonic_2_pitch = self.calculate_harmonic_pitch(base_pitch, voice.db_h2_harmonic, voice.db_h2_fine)
        base_volume = voice["voice_key_position"]
        harmonic_1_volume = self.calculate_harmonic_volume(base_volume, voice.db_h1_vol)
        harmonic_2_volume = self.calculate_harmonic_volume(base_volume, voice.db_h2_vol)
        return [base_pitch, base_volume, harmonic_1_pitch, harmonic_1_volume, harmonic_2_pitch,harmonic_2_volume]

    def updateValue(self, name, val):
        print "updateValue", name, val
        lookup = {
            "voice_key_1_position" : self.voices[0]["voice_key_position"],
            "voice_key_2_position" : self.voices[1]["voice_key_position"],
            "voice_key_3_position" : self.voices[2]["voice_key_position"],
            "pitch_key_event":self.pitch_key_event,
            "transport_pos_relative":self.transport_pos_relative,
            "layer_speed":self.layer_speed,
            "layer_1_volume":self.layer_1_volume,
            "layer_2_volume":self.layer_2_volume,
            "layer_3_volume":self.layer_3_volume,
            "layer_4_volume":self.layer_4_volume,
            "layer_5_volume":self.layer_5_volume,
            "voice_1_db_harmonic" : self.voices[0]["db_harmonic"],
            "voice_1_db_fine" : self.voices[0]["db_fine"],
            "voice_1_db_h1_harmonic" : self.voices[0]["db_h1_harmonic"],
            "voice_1_db_h1_fine" : self.voices[0]["db_h1_fine"],
            "voice_1_db_h1_vol" : self.voices[0]["db_h1_vol"],
            "voice_1_db_h2_harmonic" : self.voices[0]["db_h2_harmonic"],
            "voice_1_db_h2_fine" : self.voices[0]["db_h2_fine"],
            "voice_1_db_h2_vol" : self.voices[0]["db_h2_vol"],
            "voice_1_db_filter_a" : self.voices[0]["db_filter_a"],
            "voice_1_db_filter_b" : self.voices[0]["db_filter_b"],
            "voice_2_db_harmonic" : self.voices[1]["db_harmonic"],
            "voice_2_db_fine" : self.voices[1]["db_fine"],
            "voice_2_db_h1_harmonic" : self.voices[1]["db_h1_harmonic"],
            "voice_2_db_h1_fine" : self.voices[1]["db_h1_fine"],
            "voice_2_db_h1_vol" : self.voices[1]["db_h1_vol"],
            "voice_2_db_h2_harmonic" : self.voices[1]["db_h2_harmonic"],
            "voice_2_db_h2_fine" : self.voices[1]["db_h2_fine"],
            "voice_2_db_h2_vol" : self.voices[1]["db_h2_vol"],
            "voice_2_db_filter_a" : self.voices[1]["db_filter_a"],
            "voice_2_db_filter_b" : self.voices[1]["db_filter_b"],
            "voice_2_db_harmonic" : self.voices[1]["db_harmonic"],
            "voice_2_db_fine" : self.voices[1]["db_fine"],
            "voice_2_db_h1_harmonic" : self.voices[2]["db_h1_harmonic"],
            "voice_2_db_h1_fine" : self.voices[2]["db_h1_fine"],
            "voice_2_db_h1_vol" : self.voices[2]["db_h1_vol"],
            "voice_2_db_h2_harmonic" : self.voices[2]["db_h2_harmonic"],
            "voice_2_db_h2_fine" : self.voices[2]["db_h2_fine"],
            "voice_2_db_h2_vol" : self.voices[2]["db_h2_vol"],
            "voice_2_db_filter_a" : self.voices[2]["db_filter_a"],
            "voice_2_db_filter_b" : self.voices[2]["db_filter_b"]
        }
        lookup[name] = val

    def run(self):
        while self.all_topics_initialized == False:
            self.check_if_all_values_initialized()
            time.sleep(1)
        while True:
            transport_pos = self.normalize_transport(self.pitch_key_event, self.transport_pos_relative)

            print calculate_voice_data(0)

            #network.send("voice_1", calculate_voice_data(0))
            #network.send("voice_2", calculate_voice_data(1))
            #network.send("voice_3", calculate_voice_data(2))
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
            "voice_3_db_fine",
            "voice_3_db_h1_harmonic",
            "voice_3_db_h1_fine",
            "voice_3_db_h1_vol",
            "voice_3_db_h2_harmonic",
            "voice_3_db_h2_fine",
            "voice_3_db_h2_vol",
            "voice_3_db_filter_a",
            "voice_3_db_filter_b"
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

    network.subscribe_to_topic("voice_3_db_harmonic")
    network.subscribe_to_topic("voice_3_db_fine")
    network.subscribe_to_topic("voice_3_db_h1_harmonic")
    network.subscribe_to_topic("voice_3_db_h1_fine")
    network.subscribe_to_topic("voice_3_db_h1_vol")
    network.subscribe_to_topic("voice_3_db_h2_harmonic")
    network.subscribe_to_topic("voice_3_db_h2_fine")
    network.subscribe_to_topic("voice_3_db_h2_vol")
    network.subscribe_to_topic("voice_3_db_filter_a")
    network.subscribe_to_topic("voice_3_db_filter_b")

    dispatcher = Dispatcher(network)
    dispatcher.start()
