from __future__ import division

import socket
import threading
import AMT203

# initialize encoders using CS pins 16, 20, 21 (wpi 27, 28, 29)
encoders = [AMT203.AMT203(0, 0, i) for i in [20, 21, 16]]

# set zero position -- make sure voice key is up!
[encoder.set_zero() for encoder in encoders]

# set encoder boundaries - these are all relative to the zero position
encoder_min = 0         # this should always be zero
encoder_max = 140       # max position
encoder_overflow = 500  # anything above this is garbage and is set to min

addrs = ["192.168.1.95", "192.168.1.95", "192.168.1.95"]

def map_key(value):
  # cap encoder at min and max values defined earlier
  if value > encoder_overflow: value_adj = encoder_min
  elif value > encoder_max: value_adj = encoder_max
  else: value_adj = value

  # normalize to a value between 0 and 1.0
  return (value_adj - encoder_min) / (encoder_max - encoder_min)

def check_voice_keys(last_pos=None):

  # get current position for each voice key
  pos = [encoder.get_position() for encoder in encoders]

  # only send update if encoder has changed position since last reading
  if pos != last_pos:

    mapped_pos = [map_key(p) for p in pos]  # normalize to 0.0-1.0
    last_pos = pos                          # update encoder position

    # send normalized encoder info to corresponding voice pi
    for i, sock in enumerate(addrs):
      msg = "{'voice_key':" + str(mapped_pos[i]) + "}"
      #sock.sendto(msg, ("192.168.1.95", 3000))
      #print i, pos[i], mapped_pos[i]

    print pos

  # trigger next encoder reading in 10 ms
  timer = threading.Timer(0.01, check_voice_keys, [last_pos]).start()


# create UDP client socket for sending encoder data to voice pi
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
check_voice_keys()