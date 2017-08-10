import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import os
import Queue
import settings
import time
import threading
import traceback
import sys

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
THIRTYBIRDS_PATH = "%s/thirtybirds_2_0" % (UPPER_PATH )

sys.path.append(BASE_PATH)
sys.path.append(UPPER_PATH)

from thirtybirds_2_0.Network.manager import init as network_init

class Potentiometer(object):
    def __init__(self, name, adc, channel_number):
        self.name = name
        self.adc = adc
        self.channel_number = channel_number
        self.last_value = -1
        self.threshold_of_change = 15
    def get_change(self):
        current_value = self.adc.read_adc(self.channel_number)
        change_in_value = abs(self.last_value - current_value)
        self.last_value = current_value
        return  current_value if abs(self.last_value - current_value) >= self.threshold_of_change else None
    def get_name(self):
        return self.name
    
class ADC(object): 
    def __init__(self, chip_select_pin, potentiometer_names):
        pin_values = [0] * 8
        self.chip_select_pin = chip_select_pin
        CLK  = 18
        MISO = 23
        MOSI = 24
        self.adc = Adafruit_MCP3008.MCP3008(clk=CLK, cs=chip_select_pin, miso=MISO, mosi=MOSI)
        self.potentiometers = [Potentiometer(potentiometer_names[i], self.adc, i) for i in range(len(potentiometer_names) ) ]

    def get_changes(self):
        changes_in_value = []
        for potentiometer in self.potentiometers:
            change_in_value = potentiometer.get_change()
            if change_in_value is not None:
                changes_in_value.append([potentiometer.get_name(), change_in_value])
        return changes_in_value

class ADCS(threading.Thread):
    def __init__(self, network_send_ref):
        threading.Thread.__init__(self)
        self.network_send_ref = network_send_ref
        chip_select_pins = [21,22,23,26]
        #chip_select_pins = [21,22,23,24,25,26]
        potentiometer_names = [
            [
                "voice_1_root_harmonic"
                "voice_1_root_fine"
                "voice_1_overtone_1_harmonic"
                "voice_1_overtone_1_fine"
                "voice_1_overtone_1_volume"
                "voice_1_overtone_2_harmonic"
             ],
             [   
                "voice_1_overtone_2_fine"
                "voice_1_overtone_2_volume"
                "voice_1_formant_volume"
                "voice_1_formant_pitch"
                "voice_1_formant_open_close"
                "voice_1_formant_front_back"
            ],
            [
                "voice_2_root_harmonic"
                "voice_2_root_fine"
                "voice_2_overtone_1_harmonic"
                "voice_2_overtone_1_fine"
                "voice_2_overtone_1_volume"
                "voice_2_overtone_2_harmonic"
             ],
             [   
                "voice_2_overtone_2_fine"
                "voice_2_overtone_2_volume"
                "voice_2_formant_volume"
                "voice_2_formant_pitch"
                "voice_2_formant_open_close"
                "voice_2_formant_front_back"
            ],
            [
                "voice_3_root_harmonic"
                "voice_3_root_fine"
                "voice_3_overtone_1_harmonic"
                "voice_3_overtone_1_fine"
                "voice_3_overtone_1_volume"
                "voice_3_overtone_2_harmonic"
             ],
             [   
                "voice_3_overtone_2_fine"
                "voice_3_overtone_2_volume"
                "voice_3_formant_volume"
                "voice_3_formant_pitch"
                "voice_3_formant_open_close"
                "voice_3_formant_front_back"
            ]
        ]
        self.adcs = [ADC(chip_select_pins[i], potentiometer_names[i]) for i in range(len(chip_select_pins))]

    def run(self):
        while True:
            for adc in self.adcs:
                changes = adc.get_changes()
                for change in changes:
                    topic, value = change
                    self.self.network_send_ref(topic, value)
                time.sleep(0.01)

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

# Main handles network send/recv and can see all other classes directly
class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.network.thirtybirds.subscribe_to_topic("door_closed")
        self.adcs = ADCS(self.network.thirtybirds.send)
        self.adcs.daemon = True
        self.adcs.start()
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
        while True:
            try:
                topic, msg = self.queue.get(True)
                if topic == "door_closed":
                    door.add_to_queue(msg)
                    self.network.thirtybirds.send("door_status", True)
                    
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))

def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main


