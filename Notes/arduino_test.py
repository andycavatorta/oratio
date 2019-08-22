import random
import time

arduino_connection = open("/dev/ttyACM0",'w')
for id in range(47):
    id_str = "{}\n".format(5000+id)
    rand_int = random.randint(0,1000)
    rand_str = "{}\n".format(rand_int)
    print repr(id_str), repr(rand_str)
    time.sleep(0.5)
    arduino_connection.write(id_str)
    time.sleep(0.5)
    arduino_connection.write(rand_str)

arduino_connection.close()
