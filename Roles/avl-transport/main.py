"""
pin info:
  the AMT203 encoder is connected through SPI
  pin 19: SPI 0 MOSI
  pin 21: SPI 0 MISO
  pin 23: SPI 0 CLOCK
  pin 24: SPI 0 CHIP_SELECT_MASTER
  pin 36: SPI * CHIP_SELECT_* ( can be overwritten with passed variable 'cs' )

"""

import os
import Queue
import settings
import time
import threading
import sys

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
        current_encoder_value = 4096 - self.encoder.get_position()
        #current_encoder_value = self.encoder.get_position()
        # direction is True if moving to the right, else False
        direction = True if (self.last_encoder_value < current_encoder_value and current_encoder_value - self.last_encoder_value < self.gap) or (self.last_encoder_value - current_encoder_value > self.gap) else False
        # if the encoder has made a complete revolution, increment lap
        if current_encoder_value < self.last_encoder_value and direction:
            self.lap += 1  
        # decrement lap if moving in the opposite direction
        elif self.last_encoder_value - current_encoder_value < 0 and not direction:
            self.lap -= 1
        self.last_encoder_value = current_encoder_value # store raw position
        current_accumulated_transport_postion = (self.lap * self.resolution) + current_encoder_value  # calculate relative position
        # only send update if encoder has changed position sincfe last reading
        if current_accumulated_transport_postion != self.last_accumulated_transport_postion:
            # send normalized encoder info to voice pi
            if abs(current_accumulated_transport_postion - self.last_accumulated_transport_postion) >= 25:
                self.queue.put(current_accumulated_transport_postion)
                # update encoder position
                self.last_accumulated_transport_postion = current_accumulated_transport_postion
            #print "{'transport_pos':" + str(current_accumulated_transport_postion) + "}"
            # trigger next encoder reading in 10 msg

    def get_position(self):
        return self.queue.get(True)

    def run(self):
        while True:
            self.track_transport_position()
            time.sleep(0.02)


# Main handles network send/recv and can see all other classes directly
class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.transport = Transport()
        self.transport.daemon = True
        self.transport.start()
        self.network.thirtybirds.subscribe_to_topic("mandala_device_request")
        self.status = {
            "avl-transport":"pass", # because this passes if it can respond.  maybe better tests in future
            "avl-transport-encoder":"unset"
        }

    def update_device_status(self, devicename, status):
        if self.status[devicename] != status:
            self.status[devicename] = status
            msg = [devicename, status]
            self.network.thirtybirds.send("mandala_device_status", msg)

    def get_device_status(self):
        for devicename in self.status:
            msg = [devicename, self.status[devicename]]
            self.network.thirtybirds.send("mandala_device_status", msg)

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
        try:
            transport_position = self.transport.get_position()
            self.update_device_status("avl-transport-encoder", "pass")
        except Exception as e:
            self.update_device_status("avl-transport-encoder", "fail")

        while True:
            try:
                try:
                    topic, msg = self.queue.get(False)
                    if topic == "mandala_device_request":
                        self.get_device_status()
                except Queue.Empty:
                    pass
                #print "main Main.run topic/queue", topic, msg
                transport_position = self.transport.get_position()
                self.network.thirtybirds.send("transport_position", transport_position)
                time.sleep(0.01)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))


def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main