import os
import Queue
import serial
import settings
import sys
import time
import threading
import traceback
import zmq


#BASE_PATH = os.path.dirname(os.path.realpath(__file__))
#UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
#DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
#THIRTYBIRDS_PATH = "%s/thirtybirds_2_0" % (UPPER_PATH )

#sys.path.append(BASE_PATH)
#sys.path.append(UPPER_PATH)

from thirtybirds_2_0.Network.manager import init as network_init

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

class Mandala(threading.Thread):
    def __init__(self, serial_device_path='/dev/ttyUSB0'):
        threading.Thread.__init__(self)
        self.ser = serial.Serial(serial_device_path, 115200, timeout=10) # Establish the connection on a specific port
        self.delay = 0.015
        self.level_range = 4096
        self.queue = Queue.Queue()
        #print self.ser
        self.topics_d = {
            "controller":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":26,
                "dependencies":[
                    "controller_pedals_connected"
                ]
            },
            "controller_pedals_connected":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":9,
                "dependencies":[]
            },
            "layer_1":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":29,
                "dependencies":[]
            },
            "layer_2":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":30,
                "dependencies":[]
            },
            "layer_3":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":31,
                "dependencies":[]
            },
            "medulla":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":24,
                "dependencies":[]
            },
            "pitch_keys":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":28,
                "dependencies":[
                    "pitch_keys_sensor_1_present",
                    "pitch_keys_sensor_2_present",
                    "pitch_keys_sensor_3_present",
                    "pitch_keys_sensor_4_present",
                ]
            },
            "pitch_keys_sensor_1_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":11,
                "dependencies":[]
            },
            "pitch_keys_sensor_2_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":12,
                "dependencies":[]
            },
            "pitch_keys_sensor_3_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":13,
                "dependencies":[]
            },
            "pitch_keys_sensor_4_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":14,
                "dependencies":[]
            },
            "preamp_1":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":33,
                "dependencies":[]
            },
            "preamp_2":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":34,
                "dependencies":[]
            },
            "preamp_3":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":35,
                "dependencies":[]
            },
            "settings":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":32,
                "dependencies":[
                    "settings_adc_1_present",
                    "settings_adc_2_present",
                    "settings_adc_3_present",
                    "settings_adc_4_present",
                    "settings_adc_5_present",
                    "settings_adc_6_present",
                ]
            },
            "settings_adc_1_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":15,
                "dependencies":[]
            },
            "settings_adc_2_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":16,
                "dependencies":[]
            },
            "settings_adc_3_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":17,
                "dependencies":[]
            },
            "settings_adc_4_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":18,
                "dependencies":[]
            },
            "settings_adc_5_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":19,
                "dependencies":[]
            },
            "settings_adc_6_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":20,
                "dependencies":[]
            },
            "transport":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":27,
                "dependencies":[
                    "transport_encoder_present"
                ]
            },
            "transport_encoder_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":10,
                "dependencies":[]
            },
            "voice_1":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":21,
                "dependencies":[
                    "voice_1_oscillator_present",
                    "voice_1_tuning_complete",
                ]
            },
            "voice_1_oscillator_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":0,
                "dependencies":[]
            },
            "voice_1_tuning_complete":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":1,
                "dependencies":[]
            },
            "voice_2":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":22,
                "dependencies":[
                    "voice_2_oscillator_present",
                    "voice_2_tuning_complete",
                ]
            },
            "voice_2_oscillator_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":2,
                "dependencies":[]
            },
            "voice_2_tuning_complete":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":3,
                "dependencies":[]
            },
            "voice_3":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":23,
                "dependencies":[
                    "voice_3_oscillator_present",
                    "voice_3_tuning_complete",
                ]
            },
            "voice_3_oscillator_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":4,
                "dependencies":[]
            },
            "voice_3_tuning_complete":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":5,
                "dependencies":[]
            },
            "voice_keys":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":25,
                "dependencies":[
                    "voice_keys_encoder_1_present",
                    "voice_keys_encoder_2_present",
                    "voice_keys_encoder_3_present",
                ]
            },
            "voice_keys_encoder_1_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":6,
                "dependencies":[]
            },
            "voice_keys_encoder_2_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":7,
                "dependencies":[]
            },
            "voice_keys_encoder_3_present":{
                "reported_status":False,
                "computed_status":False,
                "led_status":"off",
                "address":8,
                "dependencies":[]
            },

            "ready":{
                "computed_status":False,
                "led_status":"off",
                "address":36,
                "dependencies":[
                    "controller",
                    "layer_1",
                    "layer_2",
                    "layer_3",
                    "medulla",
                    "pitch_keys",
                    "preamp_1",
                    "preamp_2",
                    "preamp_3",
                    "settings",
                    "transport",
                    "voice_1",
                    "voice_2",
                    "voice_3",
                    "voice_keys",
                ]
            }
        }
        self.computer_topics = [key for key, val in self.topics_d.items() if len(val["dependencies"]) > 0 and key != "ready"]
        self.peripheral_topics = [key for key, val in self.topics_d.items() if len(val["dependencies"]) == 0]
        self.led_level_d = {
            "off":0.0,
            "low":0.02,
            "high":0.9
        }


    def get_ready_state(self):
        return self.topics_d["ready"]["computed_status"]

    def get_dependent_topic(self, dependency_topic):
        for computer_topic in self.computer_topics:
            if dependency_topic in self.topics_d[topic]["dependencies"]:
                return computer_topic
        return False

    def get_if_dependencies_are_all_true(self, topic):
        for dependency_topic in self.topics_d[topic]["dependencies"]:
            if self.topics_d[dependency_topic]["computed_status"] == False:
                return False
        return True

    def update_computed_status(self, topic):
        if self.get_ready_state(): #if already ready

            if topic in self.peripheral_topics:

                if self.topics_d[topic]["reported_status"]: # this status should already be True if ready is True
                    print topic, "reports True but should already be True"
                    self.topics_d[topic]["computed_status"] = True
                else: 
                    self.topics_d[topic]["computed_status"] = False
                    dependent_topic = self.get_dependent_topic(topic)
                    self.topics_d[dependent_topic]["computed_status"] = False

            if topic in self.computer_topics:
                if self.topics_d[topic]["reported_status"]: # this status should already be True if ready is True
                    print topic, "reports True but should already be True"
                    self.topics_d[topic]["computed_status"] = True
                else: # computer is offline. set dependent peripherals offline, too
                    self.topics_d[topic]["computed_status"] = False
                    for dependency_topic in self.topics_d[topic]["dependencies"]:
                        self.topics_d[dependency_topic]["reported_status"] = False
                        self.topics_d[dependency_topic]["computed_status"] = False

        else: # if not ready

            if topic in self.peripheral_topics:

                if self.topics_d[topic]["reported_status"]: # peripheral coming online
                    self.topics_d[topic]["computed_status"] = True
                    dependent_topic = self.get_dependent_topic(topic)
                    if self.get_if_dependencies_are_all_true(dependent_topic):
                        self.topics_d[dependent_topic]["computed_status"] = True
                    else:
                        self.topics_d[dependent_topic]["computed_status"] = False
                else: # peripheral coming offline
                    self.topics_d[topic]["computed_status"] = False
                    dependent_topic = self.get_dependent_topic(topic)
                    self.topics_d[dependent_topic]["computed_status"] = False

            if topic in self.computer_topics:
                if self.topics_d[topic]["reported_status"]: # computer coming online
                    self.topics_d[topic]["computed_status"] = True
                else: # computer coming offline
                    self.topics_d[topic]["computed_status"] = False
                    for dependency_topic in self.topics_d[topic]["dependencies"]:
                        self.topics_d[dependency_topic]["computed_status"] = False
                        self.topics_d[dependency_topic]["reported_status"] = False


        ready_state_test = True
        for dependency_topic in self.topics_d['ready']["dependencies"]:
            if self.topics_d[dependency_topic]["computed_status"] == False:
                ready_state_test = False
                break

        self.topics_d['ready']["computed_status"] = ready_state_test

    def update_led_states(self):
        if self.topics_d['ready']["computed_status"]:
            self.topics_d['ready']["led_status"] = "high"
            for topic in self.computer_topics:
                self.topics_d[topic]["led_status"] = "low"
            for topic in self.peripheral_topics:
                self.topics_d[topic]["led_status"] = "low"
        else:
            self.topics_d['ready']["led_status"] = "off"
            for topic in self.peripheral_topics:
                if self.topics_d[topic]["computed_status"]:
                    self.topics_d[topic]["led_status"] = "high"
                else:
                    self.topics_d[topic]["led_status"] = "off"
            for topic in self.computer_topics:
                if self.topics_d[topic]["reported_status"] == False:
                    self.topics_d[topic]["led_status"] = "off"
                else:
                    if self.topics_d[topic]["computed_status"]:
                        self.topics_d[topic]["led_status"] = "high"
                    else:
                        self.topics_d[topic]["led_status"] = "low"

        for topic in self.topics_d.keys():
            led_position = self.topics_d[topic]["address"]
            led_level = self.led_level_d[self.topics_d[topic]["led_status"]]
            self.add_to_queue(led_position, led_level)

    def update(self, topic, status): # status_str = True|False
        try:
            self.topics_d[topic]["reported_status"] = status
            self.update_computed_status(topic)
            self.update_led_states()

        except Exception as e:
            print "exception in Mandala.update", e

    def add_to_queue(self, position, level):
        self.queue.put((position, level))

    def run(self):
        while True:
            time.sleep(self.delay)
            position, level = self.queue.get(True)
            print position, level
            if position < 38 and level <= 1.0:
                led_pos_str = str(position+5000)
                led_level_str = str(int(level*4096))
                print led_pos_str, led_level_str
                self.ser.write('<' + led_pos_str + '>') 
                time.sleep(self.delay)
                self.ser.write('<' + led_level_str + '>') 

#mandala = Mandala('/dev/ttyACM0')
#mandala.daemon = True
#mandala.start()

# Main handles network send/recv and can see all other classes directly
class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.mandala = Mandala('/dev/ttyACM0')
        self.mandala.daemon = True
        self.mandala.start()
        self.mandala_topics = self.mandala.topics_d.keys()
        for topic in self.mandala_topics:
            self.network.thirtybirds.subscribe_to_topic(topic)

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
            #try:
                topic, msg = self.queue.get(True)
                if topic in self.mandala_topics:
                    self.mandala.update(topic, msg)
                #self.socket.send("{} {}".format(topic, msg))
                print "main Main.run topic/queue", topic, msg
            #except Exception as e:
            #    exc_type, exc_value, exc_traceback = sys.exc_info()
            #    print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))

def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main
