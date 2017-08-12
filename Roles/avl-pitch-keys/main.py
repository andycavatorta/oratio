"""
encountered an error that required manually loading the module

sudo modprobe i2c_bcm2708

"""

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

#sys.path.append(BASE_PATH)
#sys.path.append(UPPER_PATH)

from thirtybirds_2_0.Network.manager import init as network_init
from thirtybirds_2_0.Adaptors.Sensors import MPR121

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

class Capacitive_Sensors(threading.Thread):
    def __init__(self, network_send_callback):
        threading.Thread.__init__(self)
        self.network_send_callback = network_send_callback
        self.keybanks = [MPR121.MPR121() for i in xrange(4)]
        for i, addr in enumerate([0x5A, 0x5B, 0x5C, 0x5D]):
            print self.keybanks[i].begin(addr)

    def run(self):
        last_state_of_all_keys = [keybank.touched() for keybank in self.keybanks]
        while True:
            current_state_of_all_keys = [keybank.touched() for keybank in self.keybanks]
            for j in xrange(4):
                for i in xrange(12):
                    pin_bit = 1 << i
                    if current_state_of_all_keys[j] & pin_bit and not last_state_of_all_keys[j] & pin_bit:
                        global_key_number = 37 + (j * 12) + (11-i)
                        print global_key_number
                        #print 'touched: keybank ' + str(j) + ', key ' + str(i)
                        self.network_send_callback("pitch_key_touched", global_key_number)
                    #if not current_state_of_all_keys[j] & pin_bit and last_state_of_all_keys[j] & pin_bit:
                    #    print 'released: keybank ' + str(j) + ', key ' + str(i)
            last_state_of_all_keys = current_state_of_all_keys
            time.sleep(0.01)


# Main handles network send/recv and can see all other classes directly
class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.capcitive_sensors = Capacitive_Sensors(self.network.thirtybirds.send)
        self.capcitive_sensors.daemon = True
        self.capcitive_sensors.start()

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





