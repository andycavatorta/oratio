import commands
import os
import Queue
import settings
import time
import threading
import serial
import sys
import traceback


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
        print os. system("stty -F /dev/ttyACM0 -hupcl")

        print 10000
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        print 10001
        self.queue = Queue.Queue()
        self.arduino_connection = open("/dev/ttyACM0",'w')
        print 10002
        self.utils = Utils(hostname)
        self.network.thirtybirds.subscribe_to_topic("mandala_device_status")
        self.UNSET = 0
        self.FAIL = 2000
        self.PASS = 4000
        self.mandala_device_status = None
        self.mandala_tlc_ids = {
            "avl-controller":39,
            "avl-formant-1":15,
            "avl-formant-1-amplifier":4,
            "avl-formant-2":16,
            "avl-formant-2-amplifier":5,
            "avl-formant-3":17,
            "avl-formant-3-amplifier":6,
            "avl-layer-1":40,
            "avl-layer-2":11,
            "avl-layer-3":12,
            "avl-medulla":35,
            "avl-pitch-keys":18,
            "avl-pitch-keys-sensor-1":7,
            "avl-pitch-keys-sensor-2":8,
            "avl-pitch-keys-sensor-3":9,
            "avl-pitch-keys-sensor-4":10,
            "avl-settings":34,
            "avl-settings-adcs":24,
            "avl-transport":13,
            "avl-transport-encoder":0,
            "avl-voice-1":36,
            "avl-voice-1-crystal-frequency-counter":25,
            "avl-voice-1-harmonic-generators":26,
            "avl-voice-1-harmonic-volume":27,
            "avl-voice-2":37,
            "avl-voice-2-crystal-frequency-counter":28,
            "avl-voice-2-harmonic-generators":29,
            "avl-voice-2-harmonic-volume":30,
            "avl-voice-3":38,
            "avl-voice-3-crystal-frequency-counter":31,
            "avl-voice-3-harmonic-generators":32,
            "avl-voice-3-harmonic-volume":33,
            "avl-voice-keys":14,
            "avl-voice-keys-encoder-1":1,
            "avl-voice-keys-encoder-2":2,
            "avl-voice-keys-encoder-3":3
        }
        self.arduino_delay_time = 0.1
        print 10003

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

        print 10003.1
        devicenames = self.mandala_tlc_ids.keys()
        devicenames.sort()
        print 10003.2
        for devicename in devicenames:
            tlc_id_int = self.mandala_tlc_ids[devicename] + 5000
            tlc_id_str = "{}\n".format(tlc_id_int)
            tlc_level_str = "0/n"

            print 10003.3, tlc_id_str, tlc_level_str
            #time.sleep(self.arduino_delay_time)
            print 10003.4
            self.arduino_connection.write(tlc_id_str)
            print 10003.5
            #time.sleep(self.arduino_delay_time)
            print 10003.6
            self.arduino_connection.write(tlc_level_str)
            print 10003.7
        print 10004
        while True:
            print 10005
            if self.mandala_device_status == None:
                print 10006
                self.network.thirtybirds.send("mandala_device_request", True)
                print 10007

            print 10008
            try:
                print 10009
                topic, msg = self.queue.get(True)
                print topic, msg
                if topic == "mandala_device_status":
                    self.mandala_device_status = eval(msg)
                    print 10010, repr(self.mandala_device_status)
                    devicenames = self.mandala_device_status.keys()
                    print 10011
                    devicenames.sort()
                    for devicename in devicenames:
                        print 10012, devicename
                        tlc_id_int = self.mandala_tlc_ids[devicename] + 5000
                        print 10013
                        tlc_id_str = "{}\n".format(tlc_id_int)
                        print 10014
                        if self.mandala_device_status[devicename] == "unset":
                            tlc_level_int = 0
                        if self.mandala_device_status[devicename] == "fail":
                            tlc_level_int = 100
                        if self.mandala_device_status[devicename] == "pass":
                            tlc_level_int = 4000
                        tlc_level_str = "{}\n".format(tlc_level_int)
                        print  10015, repr(tlc_id_str),  repr(tlc_level_str),  devicename

                        time.sleep(self.arduino_delay_time)
                        self.arduino_connection.write(tlc_id_str)
                        time.sleep(self.arduino_delay_time)
                        self.arduino_connection.write(tlc_level_str)

                time.sleep(0.01)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))

def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main

