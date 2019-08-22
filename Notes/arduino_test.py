import random
import time

arduino_connection = open("/dev/ttyACM0",'w')
for id in range(47):
    id_str = "{}\n".format(id)
    rand_int = random.randint(0,4000)
    rand_str = "{}\n".format(rand_int)
    print id_str, rand_int
    time.sleep(0.05)
    arduino_connection.write(id_str)
    time.sleep(0.05)
    arduino_connection.write(rand_str)

arduino_connection.close()
