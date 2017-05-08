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


import json
import Queue
import settings
import threading
import time
import yaml

from thirtybirds_2_0.Logs.main import Exception_Collector
from thirtybirds_2_0.Network.manager import init as network_init

network = None # for global
dispatcher = None # for global

class Dispatcher(threading.Thread):
    def __init__(self, network):
        threading.Thread.__init__(self)
        self.network = network
        self.queue = Queue.Queue()
        ### constants ###
        self.transport_encoder_pulses_per_pitch = 765.0

        ### from inputs ###
        self.pitch_key_event = 0
        self.transport_pos_relative = 0 # extrapolation of raw encoder values
        self.voice_key_1_position = 0 # float from 0.0 to 1.0
        self.voice_key_2_position = 0 # float from 0.0 to 1.0
        self.voice_key_3_position = 0 # float from 0.0 to 1.0
        self.voices = [
            {
                "voice_key_position":0, # integet fom 0 to 47
                "db_harmonic":0, # integer starting at 0
                "db_fine":0,  # cents -50 t0 50
                "db_h1_harmonic":0, # integer starting at 0
                "db_h1_fine":0, # cents -50 t0 50
                "db_h1_vol":0, # float 0.0 to 2.0, so harmonic can be 200% volume of fundamental
                "db_h2_harmonic":0, # integer starting at 0
                "db_h2_fine":0, # cents -50 t0 50
                "db_h2_vol":0, # float 0.0 to 2.0, so harmonic can be 200% volume of fundamental
                "db_filter_a":0, # float 0.0 to 1.0
                "db_filter_b":0 # float 0.0 to 1.0
            }
        ] *3
        self.layer_speed = 0
        self.layer_1_volume = 0
        self.layer_2_volume = 0
        self.layer_3_volume = 0
        self.layer_4_volume = 0
        self.layer_5_volume = 0

        ### calculated locally  ###
        self.transport_pos_offset = 0 # extrapolation of raw encoder values
        self.transport_pos_adjusted = 0 # extrapolation of raw encoder values


    def calculate_base_pitch(self, voice_num, priority):
        voice = self.voices[voice_num]
        if priority == "pitch_key":

            self.transport_pos_offset = self.transport_encoder_pulses_per_pitch + self.pitch_key_event
            
            pitch_key_freq = pow( 2, (  self.pitch_key_event / 12 ) ) * 27.5
        if priority == "transport":
            self.transport_pos_adjusted = self.transport_pos_relative + self.transport_pos_offset
            pitch_positon = self.transport_pos_adjusted / self.transport_encoder_pulses_per_pitch
            pitch_key_freq = pow( 2, (  pitch_positon / 12 ) ) * 27.5

        harmonic_freq = (int(voice["db_harmonic"]) + 1) * pitch_key_freq
        final_freq = harmonic_freq * pow(2, (voice["db_fine"]/1200))
        return final_freq


    def calculate_harmonic_pitch(self, voice_num, base_pitch, db_harmonic_num):
        voice = self.voices[voice_num]
        if db_harmonic_num == 0:
            harmonic_freq = (int(voice["db_h1_harmonic"]) + 1) * base_pitch
            final_freq = harmonic_freq * pow(2, (voice["db_h1_fine"]/1200))
            return final_freq
        if db_harmonic_num == 1:
            harmonic_freq = (int(voice["db_h2_harmonic"]) + 1) * base_pitch
            final_freq = harmonic_freq * pow(2, (voice["db_h2_fine"]/1200))
            return final_freq
            
    def calculate_harmonic_volume(self, base_volume, harm_voluime):
        return 50


    def calculate_voice_data(self,voice_num, priority):
        voice = self.voices[voice_num]
        base_pitch = self.calculate_base_pitch(voice_num, priority)
        harmonic_1_pitch = self.calculate_harmonic_pitch(voice_num, base_pitch, 0)
        harmonic_2_pitch = self.calculate_harmonic_pitch(voice_num, base_pitch, 1)
        base_volume = voice["voice_key_position"]
        harmonic_1_volume = base_volume *  voice["db_h1_vol"]
        harmonic_2_volume = base_volume *  voice["db_h2_vol"] 
        return [base_pitch, base_volume, harmonic_1_pitch, harmonic_1_volume, harmonic_2_pitch,harmonic_2_volume]

    def updateValue(self, name, val):
        #print "updateValue", name, val
        if name == "pitch_key_event":
            self.pitch_key_event = val
            self.queue.put("all_pitch_key")
            return
        if name == "transport_pos_relative":
            self.transport_pos_relative = val
            self.queue.put("all_transport")
            return

        if name == "voice_key_1_position":
            self.voices[0]["voice_key_position"] = val
            self.queue.put("1")
            return
        if name == "voice_1_db_harmonic":
            self.voices[0]["db_harmonic"] = val
            self.queue.put("1")
            return
        if name == "voice_1_db_fine":
            self.voices[0]["db_fine"] = val
            self.queue.put("1")
            return
        if name == "voice_1_db_h1_harmonic":
            self.voices[0]["db_h1_harmonic"] = val
            self.queue.put("1")
            return
        if name == "voice_1_db_h1_fine":
            self.voices[0]["db_h1_fine"] = val
            self.queue.put("1")
            return
        if name == "voice_1_db_h1_vol":
            self.voices[0]["db_h1_vol"] = val
            self.queue.put("1")
            return
        if name == "voice_1_db_h2_harmonic":
            self.voices[0]["db_h2_harmonic"] = val
            self.queue.put("1")
            return
        if name == "voice_1_db_h2_fine":
            self.voices[0]["db_h2_fine"] = val
            self.queue.put("1")
            return
        if name == "voice_1_db_h2_vol":
            self.voices[0]["db_h2_vol"] = val
            self.queue.put("1")
            return
        if name == "voice_1_db_filter_a":
            self.voices[0]["db_filter_a"] = val
            self.queue.put("1")
            return
        if name == "voice_1_db_filter_b":
            self.voices[0]["db_filter_b"] = val
            self.queue.put("1")
            return

        if name == "voice_key_2_position":
            self.voices[1]["voice_key_position"] = val
            self.queue.put("2")
            return
        if name == "voice_2_db_harmonic":
            self.voices[1]["db_harmonic"] = val
            self.voices[1]["voice_key_position"] = val
            self.queue.put("2")
            return
        if name == "voice_2_db_fine":
            self.voices[1]["db_fine"] = val
            self.voices[1]["voice_key_position"] = val
            self.queue.put("2")
            return
        if name == "voice_2_db_h1_harmonic":
            self.voices[1]["db_h1_harmonic"] = val
            self.voices[1]["voice_key_position"] = val
            self.queue.put("2")
            return
        if name == "voice_2_db_h1_fine":
            self.voices[1]["db_h1_fine"] = val
            self.voices[1]["voice_key_position"] = val
            self.queue.put("2")
            return
        if name == "voice_2_db_h1_vol":
            self.voices[1]["db_h1_vol"] = val
            self.voices[1]["voice_key_position"] = val
            self.queue.put("2")
            return
        if name == "voice_2_db_h2_harmonic":
            self.voices[1]["db_h2_harmonic"] = val
            self.voices[1]["voice_key_position"] = val
            self.queue.put("2")
            return
        if name == "voice_2_db_h2_fine":
            self.voices[1]["db_h2_fine"] = val
            self.voices[1]["voice_key_position"] = val
            self.queue.put("2")
            return
        if name == "voice_2_db_h2_vol":
            self.voices[1]["db_h2_vol"] = val
            self.voices[1]["voice_key_position"] = val
            self.queue.put("2")
            return
        if name == "voice_2_db_filter_a":
            self.voices[1]["db_filter_a"] = val
            self.voices[1]["voice_key_position"] = val
            self.queue.put("2")
            return
        if name == "voice_2_db_filter_b":
            self.voices[1]["db_filter_b"] = val
            self.voices[1]["voice_key_position"] = val
            self.queue.put("2")
            return

        if name == "voice_key_3_position":
            self.voices[2]["voice_key_position"] = val
            self.queue.put("3")
            return
        if name == "voice_3_db_harmonic":
            self.voices[2]["db_harmonic"] = val
            self.queue.put("3")
            return
        if name == "voice_3_db_fine":
            self.voices[2]["db_fine"] = val
            self.queue.put("3")
            return
        if name == "voice_3_db_h1_harmonic":
            self.voices[2]["db_h1_harmonic"] = val
            self.queue.put("3")
            return
        if name == "voice_3_db_h1_fine":
            self.voices[2]["db_h1_fine"] = val
            self.queue.put("3")
            return
        if name == "voice_3_db_h1_vol":
            self.voices[2]["db_h1_vol"] = val
            self.queue.put("3")
            return
        if name == "voice_3_db_h2_harmonic":
            self.voices[2]["db_h2_harmonic"] = val
            self.queue.put("3")
            return
        if name == "voice_3_db_h2_fine":
            self.voices[2]["db_h2_fine"] = val
            self.queue.put("3")
            return
        if name == "voice_3_db_h2_vol":
            self.voices[2]["db_h2_vol"] = val
            self.queue.put("3")
            return
        if name == "voice_3_db_filter_a":
            self.voices[2]["db_filter_a"] = val
            self.queue.put("3")
            return
        if name == "voice_3_db_filter_b":
            self.voices[2]["db_filter_b"] = val
            self.queue.put("3")
            return
        
        if name == "layer_speed":
            self.layer_speed = val
        if name == "layer_1_volume":
            self.layer_1_volume = val
        if name == "layer_2_volume":
            self.layer_2_volume = val
        if name == "layer_3_volume":
            self.layer_3_volume = val
        if name == "layer_4_volume":
            self.layer_4_volume = val
        if name == "layer_5_volume":
            self.layer_5_volume= val


    def run(self):
        while True:
            scope_of_update = self.queue.get(True)
            if scope_of_update == "all_pitch_key":
                network.send("voice_1", self.calculate_voice_data(0, "pitch_key"))
                network.send("voice_2", self.calculate_voice_data(1, "pitch_key"))
                network.send("voice_3", self.calculate_voice_data(2, "pitch_key"))
            if scope_of_update == "all_transport":
                network.send("voice_1", self.calculate_voice_data(0, "transport"))
                network.send("voice_2", self.calculate_voice_data(1, "transport"))
                network.send("voice_3", self.calculate_voice_data(2, "transport"))
            if scope_of_update == "1":
                network.send("voice_1", self.calculate_voice_data(0, "transport"))
            if scope_of_update == "2":
                network.send("voice_2", self.calculate_voice_data(1, "transport"))
            if scope_of_update == "3":
                network.send("voice_3", self.calculate_voice_data(2, "transport"))

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
            dispatcher.updateValue(topic, msg[1])
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
