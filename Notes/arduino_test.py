import random
import time

arduino_connection = open("/dev/ttyACM0",'w')
for id in range(47):
    id_str = "{}\n".format(id)
    time.sleep(0.05)
    arduino_connection.write(id_str)
    time.sleep(0.05)
    arduino_connection.write(random.randint(0,4000))

arduino_connection.close()
