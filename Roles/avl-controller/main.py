
import os
import Queue
import RPi.GPIO as GPIO
import settings
import time
import threading
import traceback
import sys


BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
THIRTYBIRDS_PATH = "%s/thirtybirds_2_0" % (UPPER_PATH )

#sys.path.append(BASE_PATH)
#sys.path.append(UPPER_PATH)

from thirtybirds_2_0.Network.manager import init as network_init

class Network(object):
    def __init__(self, hostname, network_message_handler, network_status_handler):
        self.hostname = hostname
        self.thirtybirds = network_init(
            hostname=self.hostname,
            role="server",
            discovery_multicastGroup=settings.discovery_multicastGroup,
            discovery_multicastPort=settings.discovery_multicastPort,
            discovery_responsePort=settings.discovery_responsePort,
            pubsub_pubPort=settings.pubsub_pubPort,
            message_callback=network_message_handler,
            status_callback=network_status_handler
        )

class Thirtybirds_Client_Monitor_Server(threading.Thread):
    def __init__(self, network, hostnames, update_period=30):
        threading.Thread.__init__(self)
        self.update_period = update_period
        self.current_clients = {}
        self.remembered_clients = {}
        self.network = network
        self.hostnames = hostnames
        self.queue = Queue.Queue()
        self.hosts = {}

    def empty_host_list(self):
        self.hosts = {}
        for hostname in self.hostnames:
            self.hosts[hostname] = {
                "present":False,
                "timestamp":False,
                "pickle_version":False,
                "temp":False,
                "git_pull_date":False,
                "cpu":False,
                "uptime":False,
                "disk":False
            }

    def add_to_queue(self, hostname, pickle_version, git_pull_date, temp, cpu, uptime, disk):
        self.queue.put((hostname, pickle_version, git_pull_date, temp, cpu, uptime, disk, time.time()))

    def print_current_clients(self):
        print ""
        print "CURRENT CLIENTS:"
        for hostname in self.hostnames:
            print "%s: %s : %s: %s: %s: %s: %s: %s: %s" % (
                hostname, 
                self.hosts[hostname]["present"], 
                self.hosts[hostname]["temp"], 
                self.hosts[hostname]["timestamp"], 
                self.hosts[hostname]["pickle_version"], 
                self.hosts[hostname]["git_pull_date"],
                self.hosts[hostname]["cpu"],
                self.hosts[hostname]["uptime"],
                self.hosts[hostname]["disk"]
            )

    def run(self):
        previous_hosts = {}
        while True:
            self.empty_host_list()
            self.network.thirtybirds.send("client_monitor_request", "")
            time.sleep(self.update_period)
            while not self.queue.empty():
                [hostname, pickle_version, git_pull_date, temp, cpu, uptime, disk, timestamp] = self.queue.get(True)
                self.hosts[hostname]["present"] = True
                self.hosts[hostname]["timestamp"] = timestamp
                self.hosts[hostname]["pickle_version"] = pickle_version
                self.hosts[hostname]["temp"] = temp
                self.hosts[hostname]["git_pull_date"] = git_pull_date
                self.hosts[hostname]["cpu"] = cpu
                self.hosts[hostname]["uptime"] = uptime
                self.hosts[hostname]["disk"] = disk
            #if not cmp(previous_hosts,self.hosts):
            #    self.print_current_clients()
            #previous_hosts = self.hosts
            self.print_current_clients()


class Pedal(object):
    def __init__(self, pin_number):
            self.pin_number = pin_number
            GPIO.setup(pin_number, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            self.last_value = 0
    def detect_change(self):
            current_value = GPIO.input(self.pin_number)
            if current_value == self.last_value:
                return None
            else:
                self.last_value = current_value
                return current_value

class Pedals(threading.Thread):
    def __init__(self, outgoing_msg_queue):
        threading.Thread.__init__(self)
        self.outgoing_msg_queue = outgoing_msg_queue
        self.pedals = []
        pins =  [16,20,21,13,19,26,]
        #pins =  [26, 19, 13, 21, 20, 16]
        GPIO.setmode(GPIO.BCM)
        for pin in pins:
            self.pedals.append(Pedal(pin))

    def run(self):
        while True:
            for i, pedal in enumerate(self.pedals):
                pedal_change = pedal.detect_change()
                if pedal_change is not None:
                    # print pedal, pedal_change
                    # Layer code expects 1 for down and 0 for up
                    pedal_change = 1 if pedal_change is 0 else 0
                    pedal_name = 'pedal_{}'.format(str(i+1))
                    print pedal_name, pedal_change
                    self.outgoing_msg_queue(pedal_name, pedal_change)
            time.sleep(0.01)

class Voice(object):
    def __init__(self, voice_number):
        self.voice_number = voice_number
        #inputs
        self.root_volume = 0.0
        self.root_harmonic = 0.0
        self.root_fine = 0.0
        self.overtone_1_volume = 0.0
        self.overtone_1_harmonic = 0.0
        self.overtone_1_fine = 0.0
        self.overtone_2_volume = 0.0
        self.overtone_2_harmonic = 0.0
        self.overtone_2_fine = 0.0
        self.formant_volume = 0.0
        self.formant_pitch = 0.0
        self.formant_open_close = 0.0
        self.formant_front_back = 0.0
        self.root_octave = 0
        self.root_half_steps = 0
        self.pitch_key = 0.0
        self.transport_position = 0.0
        self.transport_pos_at_last_pitch_key_touched = 0.0
        #outputs
        self._root_frequency = 0.0
        self._root_volume = 0.0
        self._overtone_1_frequency = 0.0
        self._overtone_1_volume = 0.0
        self._overtone_2_frequency = 0.0
        self._overtone_2_volume = 0.0
        self._formant_pattern = {}

        self.transport_encoder_pulses_per_pitch = 1564

    def update(self, name, value):
        if name == "root_volume":
            self.root_volume = value
            self.calculate_volumes()
        if name == "root_harmonic":
            self.root_harmonic = value
            self.calculate_frequencies()
        if name == "root_fine":
            self.root_fine = value
            self.calculate_frequencies()
        if name == "overtone_1_volume":
            self.overtone_1_volume = value
            self.calculate_volumes()
        if name == "overtone_1_harmonic":
            self.overtone_1_harmonic = value
            self.calculate_frequencies()
        if name == "overtone_1_fine":
            self.overtone_1_fine = value
            self.calculate_frequencies()
        if name == "overtone_2_volume":
            self.overtone_2_volume = value
            self.calculate_volumes()
        if name == "overtone_2_harmonic":
            self.overtone_2_harmonic = value
            self.calculate_frequencies()
        if name == "overtone_2_fine":
            self.overtone_2_fine = value
            self.calculate_frequencies()
        if name == "root_octave":
            self.root_octave = value
            self.calculate_frequencies()
        if name == "root_half_steps":
            self.root_half_steps = value
            self.calculate_frequencies()

        if name == "formant_volume":
            self.formant_volume = value
            self.calculate_formant_pattern()
        if name == "formant_pitch":
            self.formant_pitch = value
            self.calculate_formant_pattern()
        if name == "formant_open_close":
            self.formant_open_close = value
            self.calculate_formant_pattern()
        if name == "formant_front_back":
            self.formant_front_back = value
            self.calculate_formant_pattern()
        if name == "pitch_key":
            self.pitch_key = value
            self.transport_pos_at_last_pitch_key_touched = self.transport_position
            self.calculate_frequencies()
        if name == "transport_position":
            self.transport_position = value
            self.calculate_frequencies()
        voice_control_message = [
            self._root_frequency,
            self._root_volume,
            self._overtone_1_frequency,
            self._overtone_1_volume,
            self._overtone_2_frequency,
            self._overtone_2_volume,
            0,
            0
        ]
        #print "voice", self.voice_number, voice_control_message
        return voice_control_message

    def calculate_frequencies(self):
        #### root pitch ####
        # calculate base pitch
        #root_pitch = pow( 2, (  self.pitch_key / 12.0 ) ) * 27.5
        # add transport

        pitch_diff_from_transport = (self.transport_position - self.transport_pos_at_last_pitch_key_touched ) / float(self.transport_encoder_pulses_per_pitch)
        root_half_steps_increment = int(self.root_half_steps * 17)
        #print "root_half_steps_increment = ", root_half_steps_increment
        if root_half_steps_increment >= 16:
            #print 
            root_half_steps_value = 36
        elif root_half_steps_increment == 15:
            root_half_steps_value = 24
        else:
            root_half_steps_value = int(self.root_half_steps * 17)
        #print "root_half_steps_value = ", root_half_steps_value
        pitch_diff_from_transport_and_last_key = self.pitch_key + root_half_steps_value + pitch_diff_from_transport 
        #pitch_diff_from_transport_and_last_key = self.pitch_key + int(self.root_half_steps * 12) + int(self.root_octave * 5) * 12 + pitch_diff_from_transport 
        root_pitch = pow( 2, ( pitch_diff_from_transport_and_last_key  / 12.0 ) ) * 55.00
        #root_pitch = pow( 2, ( pitch_diff_from_transport_and_last_key  / 12.0 ) ) * 55.375
        #root_pitch = pow( 2, ( pitch_diff_from_transport_and_last_key  / 12.0 ) ) * 27.5
        # add harmonic
        root_harmonic_freq = (int(self.root_harmonic * 10) + 1) * root_pitch
        # add fine pitch adjust
        self._root_frequency = root_harmonic_freq * pow(2, (  ((self.root_fine*60)-30)  /1200.0))
        #### overtone 1 pitch ####
        # add harmonic
        overtone_1_harmonic_freq = (int(self.overtone_1_harmonic * 10) + 1) * self._root_frequency
        # add fine pitch adjust
        self._overtone_1_frequency = overtone_1_harmonic_freq * pow(2, (  ((self.overtone_1_fine*60)-30)  /1200.0))
        #### overtone 2 pitch ####
        # add harmonic
        overtone_2_harmonic_freq = (int(self.overtone_2_harmonic * 10) + 1) * self._root_frequency
        # add fine pitch adjust
        self._overtone_2_frequency = overtone_2_harmonic_freq * pow(2, (  ((self.overtone_2_fine*60)-30)  /1200.0))

    def calculate_volumes(self):
        self._root_volume = self.root_volume
        self._overtone_1_volume = self.overtone_1_volume * self.root_volume
        self._overtone_2_volume = self.overtone_2_volume * self.root_volume

    def calculate_formant_pattern(self):
        pass


# Main handles network send/recv and can see all other classes directly
class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.pedals = Pedals(self.add_to_queue)
        self.pedals.daemon = True
        self.pedals.start()

        self.hostnames = [
            "avl-formant-1",
            "avl-formant-2",
            "avl-formant-3",
            "avl-layer-1",
            "avl-layer-2",
            "avl-layer-3",
            "avl-medulla",
            "avl-pitch-keys",
            "avl-settings",
            "avl-transport",
            "avl-voice-1",
            "avl-voice-2",
            "avl-voice-3",
            "avl-voice-keys"
        ]
        self.client_monitor_server = Thirtybirds_Client_Monitor_Server(self.network, self.hostnames)
        self.client_monitor_server.daemon = True
        #self.client_monitor_server.start()
        #self.network.thirtybirds.subscribe_to_topic("system")  # subscribe to all system messages
        self.network.thirtybirds.subscribe_to_topic("mandala_device_request")
        self.network.thirtybirds.subscribe_to_topic("mandala_device_status")

        self.network.thirtybirds.subscribe_to_topic("pitch_key_touched")
        self.network.thirtybirds.subscribe_to_topic("transport_position")

        self.network.thirtybirds.subscribe_to_topic("layer_speed")
        self.network.thirtybirds.subscribe_to_topic("layer_1_volume")
        self.network.thirtybirds.subscribe_to_topic("layer_2_volume")
        self.network.thirtybirds.subscribe_to_topic("layer_3_volume")

        self.network.thirtybirds.subscribe_to_topic("voice_key_1_position")
        self.network.thirtybirds.subscribe_to_topic("voice_1_root_harmonic")
        self.network.thirtybirds.subscribe_to_topic("voice_1_root_fine")
        self.network.thirtybirds.subscribe_to_topic("voice_1_overtone_1_harmonic")
        self.network.thirtybirds.subscribe_to_topic("voice_1_overtone_1_fine")
        self.network.thirtybirds.subscribe_to_topic("voice_1_overtone_1_volume")
        self.network.thirtybirds.subscribe_to_topic("voice_1_overtone_2_harmonic")
        self.network.thirtybirds.subscribe_to_topic("voice_1_overtone_2_fine")
        self.network.thirtybirds.subscribe_to_topic("voice_1_overtone_2_volume")
        self.network.thirtybirds.subscribe_to_topic("voice_1_formant_volume")
        self.network.thirtybirds.subscribe_to_topic("voice_1_formant_pitch")
        self.network.thirtybirds.subscribe_to_topic("voice_1_formant_open_close")
        self.network.thirtybirds.subscribe_to_topic("voice_1_formant_front_back")
        self.network.thirtybirds.subscribe_to_topic("voice_1_root_half_steps")
        self.network.thirtybirds.subscribe_to_topic("voice_1_root_octave")
        self.network.thirtybirds.subscribe_to_topic("voice_1_emergence")

        self.network.thirtybirds.subscribe_to_topic("voice_key_2_position")
        self.network.thirtybirds.subscribe_to_topic("voice_2_root_harmonic")
        self.network.thirtybirds.subscribe_to_topic("voice_2_root_fine")
        self.network.thirtybirds.subscribe_to_topic("voice_2_overtone_1_harmonic")
        self.network.thirtybirds.subscribe_to_topic("voice_2_overtone_1_fine")
        self.network.thirtybirds.subscribe_to_topic("voice_2_overtone_1_volume")
        self.network.thirtybirds.subscribe_to_topic("voice_2_overtone_2_harmonic")
        self.network.thirtybirds.subscribe_to_topic("voice_2_overtone_2_fine")
        self.network.thirtybirds.subscribe_to_topic("voice_2_overtone_2_volume")
        self.network.thirtybirds.subscribe_to_topic("voice_2_formant_volume")
        self.network.thirtybirds.subscribe_to_topic("voice_2_formant_pitch")
        self.network.thirtybirds.subscribe_to_topic("voice_2_formant_open_close")
        self.network.thirtybirds.subscribe_to_topic("voice_2_formant_front_back")
        self.network.thirtybirds.subscribe_to_topic("voice_2_root_half_steps")
        self.network.thirtybirds.subscribe_to_topic("voice_2_root_octave")
        self.network.thirtybirds.subscribe_to_topic("voice_2_emergence")

        self.network.thirtybirds.subscribe_to_topic("voice_key_3_position")
        self.network.thirtybirds.subscribe_to_topic("voice_3_root_harmonic")
        self.network.thirtybirds.subscribe_to_topic("voice_3_root_fine")
        self.network.thirtybirds.subscribe_to_topic("voice_3_overtone_1_harmonic")
        self.network.thirtybirds.subscribe_to_topic("voice_3_overtone_1_fine")
        self.network.thirtybirds.subscribe_to_topic("voice_3_overtone_1_volume")
        self.network.thirtybirds.subscribe_to_topic("voice_3_overtone_2_harmonic")
        self.network.thirtybirds.subscribe_to_topic("voice_3_overtone_2_fine")
        self.network.thirtybirds.subscribe_to_topic("voice_3_overtone_2_volume")
        self.network.thirtybirds.subscribe_to_topic("voice_3_formant_volume")
        self.network.thirtybirds.subscribe_to_topic("voice_3_formant_pitch")
        self.network.thirtybirds.subscribe_to_topic("voice_3_formant_open_close")
        self.network.thirtybirds.subscribe_to_topic("voice_3_formant_front_back")
        self.network.thirtybirds.subscribe_to_topic("voice_3_root_half_steps")
        self.network.thirtybirds.subscribe_to_topic("voice_3_root_octave")
        self.network.thirtybirds.subscribe_to_topic("voice_3_emergence")

        self.voices = [ Voice(i) for i in range(3) ]

        self.mandala_devices = {
            "avl-controller":"pass", # because if this is sending data, it's online.
            "avl-formant-1":"unset",
            "avl-formant-1-amplifier":"unset",
            "avl-formant-2":"unset",
            "avl-formant-2-amplifier":"unset",
            "avl-formant-3":"unset",
            "avl-formant-3-amplifier":"unset",
            "avl-layer-1":"unset",
            "avl-layer-2":"unset",
            "avl-layer-3":"unset",
            "avl-medulla":"pass",# because if this is sending data, it's online.
            "avl-pitch-keys":"unset",
            "avl-pitch-keys-sensor-1":"unset",
            "avl-pitch-keys-sensor-2":"unset",
            "avl-pitch-keys-sensor-3":"unset",
            "avl-pitch-keys-sensor-4":"unset",
            "avl-settings":"unset",
            "avl-settings-adcs":"unset",
            "avl-transport":"unset",
            "avl-transport-encoder":"unset",
            "avl-voice-1":"unset",
            "avl-voice-1-crystal-frequency-counter":"unset",
            "avl-voice-1-harmonic-generators":"unset",
            "avl-voice-1-harmonic-volume":"unset",
            "avl-voice-2":"unset",
            "avl-voice-2-crystal-frequency-counter":"unset",
            "avl-voice-2-harmonic-generators":"unset",
            "avl-voice-2-harmonic-volume":"unset",
            "avl-voice-3":"unset",
            "avl-voice-3-crystal-frequency-counter":"unset",
            "avl-voice-3-harmonic-generators":"unset",
            "avl-voice-3-harmonic-volume":"unset",
            "avl-voice-keys":"unset",
            "avl-voice-keys-encoder-1":"unset",
            "avl-voice-keys-encoder-2":"unset",
            "avl-voice-keys-encoder-3":"unset"
        }

    def network_message_handler(self, topic_msg):
        # this method runs in the thread of the caller, not the tread of Main
        topic, msg =  topic_msg # separating just to eval msg.  best to do it early.  it should be done in TB.
        if len(msg) > 0:
            msg = eval(msg)
        self.add_to_queue(topic, msg)

    def network_status_handler(self, topic_msg):
        # this method runs in the thread of the caller, not the tread of Main
        print "Main.network_status_handler", topic_msg
        if topic_msg["status"]=="device_discovered":
            self.mandala_devices[topic_msg["hostname"]] = "pass"
            self.add_to_queue("mandala_device_status", (topic_msg["hostname"], "pass"))
            #self.network.thirtybirds.send("mandala_device_status", self.mandala_devices)
        if topic_msg["status"]=="device_removed":
            self.mandala_devices[topic_msg["hostname"]] = "fail"
            self.add_to_queue("mandala_device_status", (topic_msg["hostname"], "fail"))
            #self.network.thirtybirds.send("mandala_device_status", self.mandala_devices)

    def add_to_queue(self, topic, msg):
        self.queue.put((topic, msg))

    def run(self):
        while True:
            try:
                topic, msg = self.queue.get(True)
                print topic, msg

                if topic == "pitch_key_touched":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("pitch_key", msg))
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("pitch_key", msg))
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("pitch_key", msg))
                    self.network.thirtybirds.send("pitch_key_touched",msg)
                    continue
                if topic == "transport_position":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("transport_position", msg))
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("transport_position", msg))
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("transport_position", msg))
                    self.network.thirtybirds.send("transport_position",msg)
                    continue
                if topic == "voice_key_1_position":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("root_volume", msg))
                    self.network.thirtybirds.send("voice_key_1_position",msg)
                    continue
                if topic == "voice_key_2_position":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("root_volume", msg))
                    self.network.thirtybirds.send("voice_key_2_position",msg)
                    continue
                if topic == "voice_key_3_position":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("root_volume", msg))
                    self.network.thirtybirds.send("voice_key_3_position",msg)
                    continue

                if topic == "layer_speed":
                    self.network.thirtybirds.send("layer_speed", float(msg)*30.0)
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "layer_1_volume":
                    self.network.thirtybirds.send("layer_1_volume", msg)
                    self.network.thirtybirds.send("layer_1_volume",msg)
                    continue
                if topic == "layer_2_volume":
                    self.network.thirtybirds.send("layer_2_volume", msg)
                    self.network.thirtybirds.send("layer_2_volume",msg)
                    continue
                if topic == "layer_3_volume":
                    self.network.thirtybirds.send("layer_3_volume", msg)
                if topic == "layer_3_volume":
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "pedal_1":
                    self.network.thirtybirds.send("layer_1_play", msg)
                    self.network.thirtybirds.send("pedal_1",msg)
                    continue
                if topic == "pedal_2":
                    self.network.thirtybirds.send("layer_2_play", msg)
                    self.network.thirtybirds.send("pedal_2",msg)
                    continue
                if topic == "pedal_3":
                    self.network.thirtybirds.send("layer_3_play", msg)
                    self.network.thirtybirds.send("pedal_3",msg)
                    continue
                if topic == "pedal_4":
                    self.network.thirtybirds.send("layer_1_record", msg)
                    self.network.thirtybirds.send("pedal_4",msg)
                    continue
                if topic == "pedal_5":
                    self.network.thirtybirds.send("layer_2_record", msg)
                    self.network.thirtybirds.send("pedal_5",msg)
                    continue
                if topic == "pedal_6":
                    self.network.thirtybirds.send("layer_3_record", msg)
                    self.network.thirtybirds.send("pedal_6",msg)
                    continue

                if topic == "voice_1_root_harmonic":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("root_harmonic", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_root_fine":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("root_fine", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_overtone_1_harmonic":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("overtone_1_harmonic", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_overtone_1_fine":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("overtone_1_fine", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_overtone_1_volume":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("overtone_1_volume", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_overtone_2_harmonic":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("overtone_2_harmonic", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_overtone_2_fine":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("overtone_2_fine", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_overtone_2_volume":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("overtone_2_volume", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_formant_volume":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("formant_volume", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_formant_pitch":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("formant_pitch", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_formant_open_close":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("formant_open_close", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_formant_front_back":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("formant_front_back", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_root_half_steps":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("root_half_steps", msg))
                    self.network.thirtybirds.send("",msg)
                    continue
                if topic == "voice_1_root_octave":
                    self.network.thirtybirds.send("voice_1", self.voices[0].update("root_octave", msg))
                    self.network.thirtybirds.send("",msg)
                    continue

                if topic == "voice_2_root_harmonic":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("root_harmonic", msg))
                    self.network.thirtybirds.send("voice_2_root_harmonic",msg)
                    continue
                if topic == "voice_2_root_fine":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("root_fine", msg))
                    self.network.thirtybirds.send("voice_2_root_fine",msg)
                    continue
                if topic == "voice_2_overtone_1_harmonic":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("overtone_1_harmonic", msg))
                    self.network.thirtybirds.send("voice_2_overtone_1_harmonic",msg)
                    continue
                if topic == "voice_2_overtone_1_fine":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("overtone_1_fine", msg))
                    self.network.thirtybirds.send("voice_2_overtone_1_fine",msg)
                    continue
                if topic == "voice_2_overtone_1_volume":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("overtone_1_volume", msg))
                    self.network.thirtybirds.send("voice_2_overtone_1_volume",msg)
                    continue
                if topic == "voice_2_overtone_2_harmonic":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("overtone_2_harmonic", msg))
                    self.network.thirtybirds.send("voice_2_overtone_2_harmonic",msg)
                    continue
                if topic == "voice_2_overtone_2_fine":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("overtone_2_fine", msg))
                    self.network.thirtybirds.send("voice_2_overtone_2_fine",msg)
                    continue
                if topic == "voice_2_overtone_2_volume":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("overtone_2_volume", msg))
                    self.network.thirtybirds.send("voice_2_overtone_2_volume",msg)
                    continue
                if topic == "voice_2_formant_volume":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("formant_volume", msg))
                    self.network.thirtybirds.send("voice_2_formant_volume",msg)
                    continue
                if topic == "voice_2_formant_pitch":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("formant_pitch", msg))
                    self.network.thirtybirds.send("voice_2_formant_volume",msg)
                    continue
                if topic == "voice_2_formant_open_close":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("formant_open_close", msg))
                    self.network.thirtybirds.send("voice_2_formant_open_close",msg)
                    continue
                if topic == "voice_2_formant_front_back":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("formant_front_back", msg))
                    self.network.thirtybirds.send("voice_2_formant_front_back",msg)
                    continue
                if topic == "voice_2_root_half_steps":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("root_half_steps", msg))
                    self.network.thirtybirds.send("voice_2_root_half_steps",msg)
                    continue
                if topic == "voice_2_root_octave":
                    self.network.thirtybirds.send("voice_2", self.voices[1].update("root_octave", msg))
                    self.network.thirtybirds.send("voice_2_root_octave",msg)
                    continue

                if topic == "voice_3_root_harmonic":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("root_harmonic", msg))
                    self.network.thirtybirds.send("voice_3_root_harmonic",msg)
                    continue
                if topic == "voice_3_root_fine":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("root_fine", msg))
                    self.network.thirtybirds.send("voice_3_root_fine",msg)
                    continue
                if topic == "voice_3_overtone_1_harmonic":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("overtone_1_harmonic", msg))
                    self.network.thirtybirds.send("voice_3_overtone_1_harmonic",msg)
                    continue
                if topic == "voice_3_overtone_1_fine":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("overtone_1_fine", msg))
                    self.network.thirtybirds.send("voice_3_overtone_1_fine",msg)
                    continue
                if topic == "voice_3_overtone_1_volume":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("overtone_1_volume", msg))
                    self.network.thirtybirds.send("voice_3_overtone_1_volume",msg)
                    continue
                if topic == "voice_3_overtone_2_harmonic":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("overtone_2_harmonic", msg))
                    self.network.thirtybirds.send("voice_3_overtone_2_harmonic",msg)
                    continue
                if topic == "voice_3_overtone_2_fine":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("overtone_2_fine", msg))
                    self.network.thirtybirds.send("voice_3_overtone_2_fine",msg)
                    continue
                if topic == "voice_3_overtone_2_volume":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("overtone_2_volume", msg))
                    self.network.thirtybirds.send("voice_3_overtone_2_volume",msg)
                    continue
                if topic == "voice_3_formant_volume":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("formant_volume", msg))
                    self.network.thirtybirds.send("voice_3_formant_volume",msg)
                    continue
                if topic == "voice_3_formant_pitch":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("formant_pitch", msg))
                    self.network.thirtybirds.send("voice_3_formant_pitch",msg)
                    continue
                if topic == "voice_3_formant_open_close":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("formant_open_close", msg))
                    self.network.thirtybirds.send("voice_3_formant_open_close",msg)
                    continue
                if topic == "voice_3_formant_front_back":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("formant_front_back", msg))
                    self.network.thirtybirds.send("voice_3_formant_front_back",msg)
                    continue
                if topic == "voice_3_root_half_steps":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("root_half_steps", msg))
                    self.network.thirtybirds.send("voice_3_root_half_steps",msg)
                    continue
                if topic == "voice_3_root_octave":
                    self.network.thirtybirds.send("voice_3", self.voices[2].update("root_octave", msg))
                    self.network.thirtybirds.send("voice_3_root_octave",msg)
                    continue
                if topic == "client_monitor_response":
                    self.client_monitor_server.add_to_queue(msg[0],msg[1],msg[2],msg[3],msg[4],msg[5],msg[6])
                    continue

                if topic == "mandala_device_request": # received from medulla
                    self.network.thirtybirds.send("mandala_device_request", None) # send to all devices
                    #self.network.thirtybirds.send("mandala_device_status", self.mandala_devices) # send to medulla
                    continue

                if topic == "mandala_device_status": # response from all devices
                    self.network.thirtybirds.send("mandala_device_status", msg)
                    #devicename, status = msg
                    #print  "mandala_device_status", devicename, repr(status), repr(self.mandala_devices[devicename])
                    #if self.mandala_devices[devicename] != status:
                    #    self.mandala_devices[devicename] = status
                    #    self.network.thirtybirds.send("mandala_device_status", self.mandala_devices) # send to medulla
                    #continue

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))

def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main





