######################
### LOAD LIBS AND GLOBALS ###
######################

import importlib
import json
import os
import settings
import sys
import pdb
#import threading
import time
#import yaml

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
THIRTYBIRDS_PATH = "%s/thirtybirds_2_0" % (UPPER_PATH )

sys.path.append(BASE_PATH)
sys.path.append(UPPER_PATH)

from thirtybirds_2_0.Network.info import init as network_info_init
network_info = network_info_init()
args = sys.argv # Could you actually get anything to happen without this?

def get_hostname():
    global args
    try:
        pos = args.index("-n") # pull hostname from command line argument, if there is one
        hostname = args[pos+1]
    except Exception as E:
        hostname = network_info.getHostName()
    return hostname

HOSTNAME = get_hostname()

####################
### PAUSE UNTIL ONLINE  ###
####################

PAUSE_UNTIL_ONLINE_MAX_SECONDS = 30

def pause_until_online(max_seconds):
    for x in range(max_seconds):
        if network_info.getOnlineStatus():
            print "got connection!"
            break
        else:
            print "waiting for connection..."
            time.sleep(1)

pause_until_online(PAUSE_UNTIL_ONLINE_MAX_SECONDS)

###############
### AUTO UPDATE ###
###############

try:
    skip_update = args.index("--skip-update")
except ValueError:
    skip_update = False

if skip_update is False:
    #args = sys.argv[1:]
    try:
        #pos = args.index("-u")
        #au = args[pos+1]
        #assert au in ["true","True"]
        from thirtybirds_2_0.Updates.manager import init as updates_init
        result = updates_init(THIRTYBIRDS_PATH, True, True)
        print result
        result = updates_init(BASE_PATH, True, True)
        print result
    except Exception as e:
        print "Exception in main.py", e

#########################
### LOAD DEVICE-SPECIFIC CODE ###
#########################

host = importlib.import_module("Roles.%s.main" % (HOSTNAME))
client = host.init(HOSTNAME)

#########################
### RUN OSC DEBUG SERVER ###
#########################

def handleSimulatedNetworkMessage(addr, tags, stuff, source):
    global client
    topic = stuff[0]
    msg = "" if len(stuff) <= 1 else stuff[1]
    client.network_message_handler((topic, msg))

try:
    run_osc_debug_server = args.index("--run-osc")
except ValueError:
    run_osc_debug_server = False

if run_osc_debug_server is not False:
    COMMON_PATH = "%s/Common/" % (BASE_PATH )
    sys.path.append(COMMON_PATH)
    from osc_server_wrapper import OSCServerWrapper
    osc_server_tester = OSCServerWrapper('0.0.0.0', 7000)
    osc_server_tester.addOSCHandler("/network_message", handleSimulatedNetworkMessage)
    osc_server_tester.startOSCSServer()
