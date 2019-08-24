import socket
import threading
import AMT203

encoder = AMT203.AMT203(0, 0, 16) # initialize encoder
encoder.set_zero()                # set zero position -- move transport to left!

resolution = encoder.get_resolution() # should be 4096
gap = 2000              # this is the largest jump we want to detect (I think?)

def check_transport(last_abs_pos=0, last_pos=0, lap=0):

  # get raw encoder value
  pos = encoder.get_position()

  # direction is True if moving to the right, else False
  direction = True if (last_pos < pos and pos-last_pos < gap) or \
    (last_pos-pos > gap) else False

  # if the encoder has made a complete revolution, increment lap
  if pos < last_pos and direction:
    lap += 1  
  # decrement lap if moving in the opposite direction
  elif last_pos - pos < 0 and not direction:
    lap -= 1

  last_pos = pos                      # store raw position
  abs_pos = (lap * resolution) + pos  # calculate relative position

  # only send update if encoder has changed position sincfe last reading
  if abs_pos != last_abs_pos:

    # update encoder position
    last_abs_pos = abs_pos
    
    # send normalized encoder info to voice pi
    msg = "{'transport_pos':" + str(abs_pos) + "}"
    print msg
  
  # trigger next encoder reading in 10 msg
  threading.Timer(0.01, check_transport, [last_abs_pos, last_pos, lap]).start()

check_transport()