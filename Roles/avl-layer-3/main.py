import commands
import os
import RPi.GPIO as GPIO
import sys
import Queue
import settings
import threading
import time
import traceback

from thirtybirds_2_0.Network.manager import init as network_init
from thirtybirds_2_0.Updates.manager import init as updates_init

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

########################
## UTILS
########################

class Utils(object):
    def __init__(self, hostname):
        self.hostname = hostname
    def reboot(self):
        os.system("sudo reboot now")

    def get_shelf_id(self):
        return self.hostname[11:][:1]

    def get_camera_id(self):
        return self.hostname[12:]

    def create_image_file_name(self, timestamp, light_level, process_type):
        return "{}_{}_{}_{}_{}.png".format(timestamp, self.get_shelf_id() ,  self.get_camera_id(), light_level, process_type) 

    def remote_update_git(self, oratio, thirtybirds, update, upgrade):
        if oratio:
            subprocess.call(['sudo', 'git', 'pull'], cwd='/home/pi/oratio')
        if thirtybirds:
            subprocess.call(['sudo', 'git', 'pull'], cwd='/home/pi/thirtybirds_2_0')
        return

    def remote_update_scripts(self):
        updates_init("/home/pi/oratio", False, True)
        return

    def get_update_script_version(self):
        (updates, ghStatus, bsStatus) = updates_init("/home/pi/oratio", False, False)
        return updates.read_version_pickle()

    def get_git_timestamp(self):
        return commands.getstatusoutput("cd /home/pi/oratio/; git log -1 --format=%cd")[1]

    def get_temp(self):
        return commands.getstatusoutput("/opt/vc/bin/vcgencmd measure_temp")[1]

    def get_cpu(self):
        bash_output = commands.getstatusoutput("uptime")[1]
        split_output = bash_output.split(" ")
        return split_output[12]

    def get_uptime(self):
        bash_output = commands.getstatusoutput("uptime")[1]
        split_output = bash_output.split(" ")
        return split_output[4]

    def get_disk(self):
        # stub for now
        return "0"

    def get_client_status(self):
        return (self.hostname, self.get_update_script_version(), self.get_git_timestamp(), self.get_temp(), self.get_cpu(), self.get_uptime(), self.get_disk())


class Layer(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.network.thirtybirds.subscribe_to_topic("layer_3_record")
        self.network.thirtybirds.subscribe_to_topic("layer_3_play")
        self.network.thirtybirds.subscribe_to_topic("layer_3_volume")
        self.network.thirtybirds.subscribe_to_topic("layer_speed")
        self.network.thirtybirds.subscribe_to_topic("clear_loop")
        self.network.thirtybirds.subscribe_to_topic("mandala_device_request")
        self.utils = Utils(hostname)
        self.blinkTimer = None
        self.status = {
            "avl-layer-1":"pass", # because this passes if it can respond.  maybe better tests in future
        }

    def lights_out(self):
        GPIO.output(26, GPIO.LOW)
        self.blinkTimer = None

    def loop_callback(self):
        # print "Sending layer trigger 1"
        self.network.thirtybirds.send("layer_3_trigger", "1")
        GPIO.output(26, GPIO.HIGH)
        if (self.blinkTimer is not None):
            self.blinkTimer.cancel()
        self.blinkTimer = threading.Timer(0.3, self.lights_out)
        self.blinkTimer.start()

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
        # this method runs in the thread of the caller, not the thread of Layer
        topic, msg =  topic_msg # separating just to eval msg.  best to do it early.  it should be done in TB.
        #print "Main network_message_handler", topic, msg
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
        self.looper.setLoopCallback(self.loop_callback)
        self.looperController = LooperController(self.looper)
        self.looper.start()
        while True:
            try:
                topic, msg = self.queue.get(True)

                if topic == "mandala_device_request":
                    self.get_device_status()
                    continue
                #if topic == "client_monitor_request":
                #    self.network.thirtybirds.send("client_monitor_response", self.utils.get_client_status())

                elif topic == "layer_3_record":
                    if msg:
                        self.looperController.handleRecordPedalDown()
                    else:
                        self.looperController.handleRecordPedalUp()
                    continue
                elif topic == "layer_3_play":
                    if msg:
                        self.looperController.handlePlayPedalDown()
                    else:
                        self.looperController.handlePlayPedalUp()
                    continue
                elif topic == "layer_3_volume":
                    self.looperController.setVolume(msg)
                    continue
                elif topic == "layer_speed":
                    self.looperController.setLoopLength(msg)
                    continue
                elif topic == "clear_loop":
                    self.looperController.clear()
                    continue
                elif topic == "__heartbeat__":
                    #print "heartbeat received", msg
                    continue
                elif topic == "__print__":
                    print "Layer.network_status_handler", msg
                    continue
                else:
                    print ("Unhandled message type %s" % topic)

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))

def init(hostname):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(26, GPIO.OUT)
    layer = Layer(hostname)
    layer.daemon = True
    layer.start()
    return layer
