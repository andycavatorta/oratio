import os
import Queue
import settings
import time
import threading


#BASE_PATH = os.path.dirname(os.path.realpath(__file__))
#UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
#DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
#THIRTYBIRDS_PATH = "%s/thirtybirds_2_0" % (UPPER_PATH )

#sys.path.append(BASE_PATH)
#sys.path.append(UPPER_PATH)

from thirtybirds_2_0.Network.manager import init as network_init
from thirtybirds_2_0.Adaptors.Sensors import AMT203_expanded_spi


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

class Transport(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.encoder = AMT203_expanded_spi.AMT203(0, 0, 16) # initialize encoder
        self.encoder.set_zero()                # set zero position -- move transport to left!
        self.resolution = self.encoder.get_resolution() # should be 4096
        self.gap = 2000              # this is the largest jump we want to detect (I think?)
        self.lap = 0
        self.last_encoder_value = 0
        self.last_accumulated_transport_postion = 0
        self.queue = Queue.Queue(maxsize=1  )

    def track_transport_position(self):
        current_encoder_value = self.encoder.get_position()
        # direction is True if moving to the right, else False
        direction = True if (self.last_encoder_value < current_encoder_value and current_encoder_value - self.last_encoder_value < self.gap) or (self.last_encoder_value - current_encoder_value > self.gap) else False
        # if the encoder has made a complete revolution, increment lap
        if current_encoder_value < self.last_encoder_value and direction:
            self.lap += 1  
        # decrement lap if moving in the opposite direction
        elif self.last_encoder_value - current_encoder_value < 0 and not direction:
            self.lap -= 1
        self.last_encoder_value = current_encoder_value                      # store raw position
        current_accumulated_transport_postion = (self.lap * self.resolution) + current_encoder_value  # calculate relative position
        # only send update if encoder has changed position sincfe last reading
        if current_accumulated_transport_postion != self.last_accumulated_transport_postion:
            # update encoder position
            self.last_accumulated_transport_postion = current_accumulated_transport_postion
            # send normalized encoder info to voice pi
            self.queue.put(current_accumulated_transport_postion)
            #print "{'transport_pos':" + str(current_accumulated_transport_postion) + "}"
            # trigger next encoder reading in 10 msg

    def get_position(self):
        return self.queue.get(True)

    def run(self):
        while True:
            self.track_transport_position()
            time.sleep(0.01)


# Main handles network send/recv and can see all other classes directly
class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.transport = Transport()
        self.transport.daemon = True
        self.transport.start()
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
        while True:
            try:
                #topic, msg = self.queue.get(True)
                #print "main Main.run topic/queue", topic, msg
                transport_position = self.transport.get_position()
                time.sleep(0.1)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))


def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main

