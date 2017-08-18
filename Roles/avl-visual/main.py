import os
import Queue
import settings
import time
import threading
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

# Main handles network send/recv and can see all other classes directly
class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)

        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.port = "5556"
        self.queue = Queue.Queue()
        self.context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        self.socket.bind("tcp://*:%s" % self.port)
        #self.network.thirtybirds.subscribe_to_topic("door_closed")
        self.network.thirtybirds.subscribe_to_topic("voice_1")
        self.network.thirtybirds.subscribe_to_topic("voice_2")
        self.network.thirtybirds.subscribe_to_topic("voice_3")
        self.network.thirtybirds.subscribe_to_topic("layer_speed")
        self.network.thirtybirds.subscribe_to_topic("layer_1_volume")
        self.network.thirtybirds.subscribe_to_topic("layer_2_volume")
        self.network.thirtybirds.subscribe_to_topic("layer_3_volume")
        self.network.thirtybirds.subscribe_to_topic("layer_1_play")
        self.network.thirtybirds.subscribe_to_topic("layer_2_play")
        self.network.thirtybirds.subscribe_to_topic("layer_3_play")
        self.network.thirtybirds.subscribe_to_topic("layer_1_record")
        self.network.thirtybirds.subscribe_to_topic("layer_2_record")
        self.network.thirtybirds.subscribe_to_topic("layer_3_record")


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
                self.socket.send("%d %d" % (topic, msg))
                print "main Main.run topic/queue", topic, msg
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))

def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main
