import os
import sys
import Queue
import settings
import threading
import traceback

from thirtybirds_2_0.Network.manager import init as network_init

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.normpath(os.path.join(BASE_PATH, '..'))
DEVICES_PATH = os.path.normpath(os.path.join(BASE_PATH, 'Hosts'))
THIRTYBIRDS_PATH = os.path.normpath(os.path.join(UPPER_PATH, 'thirtybirds_2_0'))

sys.path.append(BASE_PATH)
sys.path.append(UPPER_PATH)

from layer.live_looper import LiveLooper
from layer.looper_controller import LooperController

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

class Layer(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.network.thirtybirds.subscribe_to_topic("layer_1_record")
        self.network.thirtybirds.subscribe_to_topic("layer_1_play")
        self.network.thirtybirds.subscribe_to_topic("layer_1_volume")
        self.network.thirtybirds.subscribe_to_topic("layer_speed")
        self.network.thirtybirds.subscribe_to_topic("clear_loop")

    def network_message_handler(self, topic_msg):
        # this method runs in the thread of the caller, not the thread of Layer
        topic, msg =  topic_msg # separating just to eval msg.  best to do it early.  it should be done in TB.
        if len(msg) > 0:
            msg = eval(msg)
        self.add_to_queue(topic, msg)

    def network_status_handler(self, topic_msg):
        # this method runs in the thread of the caller, not the thread of Layer
        self.add_to_queue("__print__", topic_msg)
        # print "Layer.network_status_handler", topic_msg

    def add_to_queue(self, topic, msg):
        self.queue.put((topic, msg))

    def run(self):
        self.looper = LiveLooper()
        self.looperController = LooperController(self.looper)
        self.looper.start()
        while True:
            try:
                topic, msg = self.queue.get(True)
                if topic == "layer_1_record":
                    if msg:
                        self.looperController.handleShortPedalDown()
                    else:
                        self.looperController.handleShortPedalUp()
                elif topic == "layer_1_play":
                    if msg:
                        self.looperController.handleLongPedalDown()
                    else:
                        self.looperController.handleLongPedalUp()
                elif topic == "layer_1_volume":
                    self.looperController.setVolume(msg)
                elif topic == "layer_speed":
                    self.looperController.setLoopLength(msg)
                elif topic == "clear_loop":
                    self.looperController.clear()
                elif topic == "__heartbeat__":
                    print "heartbeat received", msg
                elif topic == "__print__":
                    print "Layer.network_status_handler", msg
                else:
                    print ("Unhandled message type %s" % topic)

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))

def init(hostname):
    layer = Layer(hostname)
    layer.daemon = True
    layer.start()
    return layer
