import os
import sys
import settings
import traceback
import threading
import Queue
import crystal_helpers as crystal

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
THIRTYBIRDS_PATH = "%s/thirtybirds_2_0" % (UPPER_PATH )

sys.path.append(BASE_PATH)
sys.path.append(UPPER_PATH)

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
        self.queue = Queue.Queue()

        # default intermediate frequency
        self.xtal_freq = 96131.8

        # get voice messages
        self.network.thirtybirds.subscribe_to_topic("voice_3")

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
                if topic == "voice_3":

                    params = []

                    # mute if volume is below threshold
                    thresh = [0.01, 0.1, 0.1]
                    for i in xrange(6):
                        param = 0 if msg[1] < thresh[0] else msg[i]                   # master
                        param = 0 if msg[3] < thresh[1] and i in (2,3) else param     # subvoice 1
                        param = 0 if msg[5] < thresh[2] and i in (4,5) else param     # subvoice 2
                        params.append(param)

                    
                    freq_root, vol, freq_sub1, vol_sub1, freq_sub2, vol_sub2 = params

                    # update intermediate frequency if new data is available
                    self.xtal_freq = crystal.measure_xtal_freq() or self.xtal_freq

                    print params, self.xtal_freq

                    # subvoice 1 (fundamental) frequency and voice volume
                    crystal.set_freq(0, self.xtal_freq - (freq_root + self.f_offset))
                    crystal.set_volume(0, map_master_volume(vol))

                    # subvoice 2 frequency and volume
                    crystal.set_freq(1, self.xtal_freq - (freq_sub1 + self.f_offset))
                    crystal.set_volume(1, map_subvoice_volume(vol_sub1))

                    # subvoice 3 frequency and volume
                    crystal.set_freq(2, self.xtal_freq - (freq_sub2 + self.f_offset))
                    crystal.set_volume(2, map_subvoice_volume(vol_sub2))

                    
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))


def init(hostname):
    crystal.init()

    main = Main(hostname)
    main.daemon = True
    main.start()
    return main

def map_subvoice_volume(level):
    return map_volume(level, 154, 100)

def map_master_volume(level,):
    return map_volume(level, 100, 900)

def map_volume(level, min, scale):
    return 0 if level == 0 else min + level * scale