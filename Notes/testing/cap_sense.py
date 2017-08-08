import MPR121
import threading

# create four i2c devices at appropriate addresses
keybanks = [MPR121.MPR121() for i in xrange(4)]
for i, addr in enumerate([0x5A, 0x5B, 0x5C, 0x5D]):
  print keybanks[i].begin(addr)

last_state = [keybank.touched() for keybank in keybanks]


def check_cap_sensors(last_state):

  # get current state (have any keys been touched/released?)
  curr_state = [keybank.touched() for keybank in keybanks]
  print curr_state

  for j in xrange(4):

    for i in xrange(12):

      pin_bit = 1 << i

      # First check if transitioned from not touched to touched.
      if curr_state[j] & pin_bit and not last_state[j] & pin_bit:
        print 'touched: keybank ' + str(j) + ', key ' + str(i)
      
      if not curr_state[j] & pin_bit and last_state[j] & pin_bit:
        print 'released: keybank ' + str(j) + ', key ' + str(i)

  threading.Timer(0.01, check_cap_sensors, [curr_state]).start()


last_state = [keybank.touched() for keybank in keybanks]
check_cap_sensors(last_state)