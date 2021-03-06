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
from thirtybirds_2_0.Adaptors.Sensors import AMT203_expanded_spi
from thirtybirds_2_0.Updates.manager import init as updates_init

wpi.wiringPiSetup()
wpi.wiringPiSPISetup(0, 500000)

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
        self.last_master_volume_level = 0
        self.utils = Utils(hostname)
        self.network.thirtybirds.subscribe_to_topic("voice_3")
        self.network.thirtybirds.subscribe_to_topic("client_monitor_request")
        self.network.thirtybirds.subscribe_to_topic("mandala_device_request")
        self.status = {
            "avl-formant-3":"pass", # because this passes if it can respond.  maybe better tests in future
            "avl-formant-3-amplifier":"unset"
        }

    def update_device_status(self, devicename, status):
        print "update_device_status 1",devicename, status
        if self.status[devicename] != status:
            self.status[devicename] = status
            msg = [devicename, status]
            print "update_device_status 2",devicename, status
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
        master_volume = 0
        try:
            wpi.wiringPiSPIDataRW(0, chr(0) + chr(0)) # set volume to zero as test of comms
            self.update_device_status("avl-formant-3-amplifier", "pass")
        except Exception as e:
            self.update_device_status("avl-formant-3-amplifier", "fail")

        while True:
            try:
                try:
                    topic, msg = self.queue.get(False)
                    if topic == "mandala_device_request":
                        self.get_device_status()
                    if topic == "voice_3":
                        master_volume = msg[1] * 100
                        master_volume = 0 if master_volume < 10 else master_volume - 10
                except Queue.Empty:
                    pass
                #if master_volume != self.last_master_volume_level :
                if master_volume > self.last_master_volume_level :
                    #print "upside A master_volume=", master_volume, "self.last_master_volume_level", self.last_master_volume_level
                    self.last_master_volume_level = self.last_master_volume_level + 1
                    gain = int(102 + (self.last_master_volume_level)) if self.last_master_volume_level > 1 else 0
                    print "upside B master_volume=", master_volume, "self.last_master_volume_level", self.last_master_volume_level, gain
                    wpi.wiringPiSPIDataRW(0, chr(gain) + chr(0))
                    time.sleep(0.001)
                    continue
                if master_volume < self.last_master_volume_level :
                    #print "downside A master_volume=", master_volume, "self.last_master_volume_level", self.last_master_volume_level
                    self.last_master_volume_level = self.last_master_volume_level - 1
                    if self.last_master_volume_level < 0:
                        self.last_master_volume_level = 0
                    gain = int(102 + (self.last_master_volume_level)) if self.last_master_volume_level > 1 else 0
                    print "downside B master_volume=", master_volume,  "self.last_master_volume_level", self.last_master_volume_level, gain
                    wpi.wiringPiSPIDataRW(0, chr(gain) + chr(0))
                    time.sleep(0.001)
                    continue
                time.sleep(0.01)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))


def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main

