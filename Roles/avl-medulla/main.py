import commands
import os
import Queue
import settings
import time
import threading
import wiringpi as wpi
import sys
import traceback

#BASE_PATH = os.path.dirname(os.path.realpath(__file__))
#UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
#DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
#THIRTYBIRDS_PATH = "%s/thirtybirds_2_0" % (UPPER_PATH )

#sys.path.append(BASE_PATH)
#sys.path.append(UPPER_PATH)

from thirtybirds_2_0.Network.manager import init as network_init
from thirtybirds_2_0.Updates.manager import init as updates_init

#wpi.wiringPiSetup()
#wpi.wiringPiSPISetup(0, 500000)

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
        self.last_master_volume_level = 0
        self.utils = Utils(hostname)
        self.network.thirtybirds.subscribe_to_topic("mandala_device_status")
        self.UNSET = 0
        self.FAIL = 2000
        self.PASS = 4000
        self.mandala_device_status = None
        self.mandala_devices = {
            "avl-layer-1":{"tlc_id":29,"status":self.UNSET},
            "avl-layer-2":{"tlc_id":30,"status":self.UNSET},
            "avl-layer-3":{"tlc_id":31,"status":self.UNSET},

            "avl-transport":{"tlc_id":27,"status":self.UNSET},
            "avl-transport-encoder":{"tlc_id":10,"status":self.UNSET},

            "avl-voice_keys":{"tlc_id":25,"status":self.UNSET},
            "avl-voice-keys-encoder-1":{"tlc_id":6,"status":self.UNSET},
            "avl-voice-keys-encoder-2":{"tlc_id":7,"status":self.UNSET},
            "avl-voice-keys-encoder-3":{"tlc_id":8,"status":self.UNSET},

            "avl-formant-1":{"tlc_id":33,"status":self.UNSET},
            "avl-formant-1-amplifier":{"tlc_id":33,"status":self.UNSET},
            "avl-formant-2":{"tlc_id":34,"status":self.UNSET},
            "avl-formant-2-amplifier":{"tlc_id":34,"status":self.UNSET},
            "avl-formant-3":{"tlc_id":35,"status":self.UNSET},
            "avl-formant-3-amplifier":{"tlc_id":35,"status":self.UNSET},

            "avl-pitch-keys":{"tlc_id":28,"status":self.UNSET},
            "avl-pitch-keys-sensor-1":{"tlc_id":11,"status":self.UNSET},
            "avl-pitch-keys-sensor-2":{"tlc_id":12,"status":self.UNSET},
            "avl-pitch-keys-sensor-3":{"tlc_id":13,"status":self.UNSET},
            "avl-pitch-keys-sensor-4":{"tlc_id":14,"status":self.UNSET},

            "avl-settings":{"tlc_id":32,"status":self.UNSET},

            "medulla":{"tlc_id":24,"status":self.UNSET},

            "avl-voice-1":{"tlc_id":21,"status":self.UNSET},
            "avl-voice-1-crystal-frequency-counter":{"tlc_id":0,"status":self.UNSET},
            "avl-voice-1-voice_board":{"tlc_id":1,"status":self.UNSET},

            "avl-voice-2":{"tlc_id":22,"status":self.UNSET},
            "avl-voice-2-crystal-frequency-counter":{"tlc_id":2,"status":self.UNSET},
            "avl-voice-2-voice_board":{"tlc_id":3,"status":self.UNSET},

            "avl-voice-3":{"tlc_id":23,"status":self.UNSET},
            "avl-voice-3-crystal-frequency-counter":{"tlc_id":4,"status":self.UNSET},
            "avl-voice-3-voice_board":{"tlc_id":5,"status":self.UNSET},

            "controller":{"tlc_id":26,"status":self.UNSET},
        }

    def network_message_handler(self, topic_msg):
        # this method runs in the thread of the caller, not the tread of Main
        topic, msg =  topic_msg # separating just to eval msg.  best to do it early.  it should be done in TB.
        #if len(msg) > 0: 
        #    msg = eval(msg)
        self.add_to_queue(topic, msg)

    def network_status_handler(self, topic_msg):
        # this method runs in the thread of the caller, not the tread of Main
        print "Main.network_status_handler", topic_msg

    def add_to_queue(self, topic, msg):
        self.queue.put((topic, msg))

    def run(self):
        
        while True:
            if self.mandala_device_status == None:
                time.sleep(1)
                self.network.thirtybirds.send("mandala_device_status_request", True)
            try:
                topic, msg = self.queue.get(True)
                if topic == "mandala_device_status":
                    print topic, msg
                time.sleep(0.01)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))


def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main

