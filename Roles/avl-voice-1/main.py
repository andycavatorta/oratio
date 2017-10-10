import commands
import crystal_helpers as crystal
import os
import Queue
import sys
import settings
import time
import traceback
import threading

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
THIRTYBIRDS_PATH = "%s/thirtybirds_2_0" % (UPPER_PATH )

sys.path.append(BASE_PATH)
sys.path.append(UPPER_PATH)

from thirtybirds_2_0.Network.manager import init as network_init
from thirtybirds_2_0.Updates.manager import init as updates_init


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



# Main handles network send/recv and can see all other classes directly
class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.utils = Utils(hostname)
        #self.gainRampThread = gainRampThread
        # default intermediate frequency
        #self.xtal_freq = 167233.6
        self.xtal_freq = 167218.6
        self.f_offset = 0           # adjust output freq

        # get voice messages
        self.network.thirtybirds.subscribe_to_topic("voice_1")
        self.network.thirtybirds.subscribe_to_topic("client_monitor_request")

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
                print topic, msg
                if topic == "voice_1":

                    params = []
                    # mute if volume is below threshold
                    thresh = [0.01, 0.01, 0.01]
                    for i in xrange(6):
                        param = 0 if msg[1] < thresh[0] else msg[i]                   # master
                        param = 0 if msg[3] < thresh[1] and i in (2,3) else param     # subvoice 1
                        param = 0 if msg[5] < thresh[2] and i in (4,5) else param     # subvoice 2
                        params.append(param)
                    freq_root, vol, freq_sub1, vol_sub1, freq_sub2, vol_sub2 = params
                    # update intermediate frequency if new data is available
                    #measure_xtal_freq = crystal.measure_xtal_freq()
                    self.xtal_freq = crystal.measure_xtal_freq() or self.xtal_freq
                    print "adjusted:", params, self.xtal_freq

                    # subvoice 1 (fundamental) frequency
                    crystal.set_freq(0, vol and (self.xtal_freq - (freq_root + self.f_offset)))

                    # subvoice 2 frequency and volume
                    crystal.set_freq(1, vol_sub1 and (self.xtal_freq - (freq_sub1 + self.f_offset)))
                    crystal.set_volume(1, map_subvoice_volume(vol_sub1))

                    # subvoice 3 frequency and volume
                    crystal.set_freq(2, vol_sub2 and (self.xtal_freq - (freq_sub2 + self.f_offset)))
                    crystal.set_volume(2, map_subvoice_volume(vol_sub2))

                if topic == "client_monitor_request":
                    self.network.thirtybirds.send("client_monitor_response", self.utils.get_client_status())
                    

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
    # return map_volume(level, 0, 100)
    # return map_volume(level, 50, 100)
    # print "level=", level
    return map_volume(level-0.1, 0, 200)

def map_volume(level, min, scale):
    print "map_volume=", 0 if level == 0 else int(min + level * scale)
    return 0 if level == 0 else int(min + level * scale)