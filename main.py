######################
### LOAD LIBS AND GLOBALS ###
######################

import importlib
import json
import os
import settings 
import sys
#import threading
#import time
#import yaml

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
THIRTYBIRDS_PATH = "%s/thirtybirds_2_0" % (UPPER_PATH )

sys.path.append(BASE_PATH)
sys.path.append(UPPER_PATH)

from thirtybirds_2_0.Network.info import init as network_info_init
network_info = network_info_init()

def get_hostname():
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

args = sys.argv[1:]
#try:
pos = args.index("-u")
au = args[pos+1]
assert au in ["true","True"]
from thirtybirds_2_0.Updates.manager import init as updates_init
result = updates_init(THIRTYBIRDS_PATH, True, True)
print result
result = updates_init(BASE_PATH, True, True)
print result
#except Exception as E:
#    pass

#########################
### LOAD DEVICE-SPECIFIC CODE ###
#########################
    
host = importlib.import_module("Roles.%s.main" % (HOSTNAME))
host.init(HOSTNAME)

