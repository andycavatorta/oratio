"""
attar is the global logging and reporting system.
When it's more complete, it can be moved to thritybirds

It is used as a global repository for internal messages: debug, trace, exceptions, events

It writes these messages to the terminal ( std.out ) and a log file, and publishes them on ZMQ.
So messages are available in many modes and easier to view, review, and collect.

multiple instances can run simultaneously.

"""

import time

class main():
    def __init__(self, hostname, publisher):
        self.hostname = hostname
        # if /Logs/attar.log does not exist, create it



    def log(self, topic, filename, classname, method, message, traceback=""):
        # get timestamp
        message_d = {
            "timestamp":time.strftime("%Y-%m-%d %H:%M:%S:"),
            "topic":topic,
            "hostname":hostname,
            "filename":filename,
            "classname":classname,
            "method":method,
            "message":message,
            "traceback":traceback
        }
        print topic, filename, classname, method, message, traceback
        message_j = json.dumps(message_d)
        #log message_d

        #publish message_d to topic
        publisher.send(topic, message_j)





