import random
import time

arduino_connection = open("/dev/ttyACM0",'w')
for id in range(47):
    id_str = "{}\n".format(id)
    rand_value = random.randint(0,4000)
    print id_str, rand_value
    time.sleep(0.05)
    arduino_connection.write(id_str)
    time.sleep(0.05)
    arduino_connection.write(rand_value)

arduino_connection.close()
