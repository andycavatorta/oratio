import Adafruit_GPIO.I2C as I2C


class DS1803(object):

    CMD_WRITE_POT0 = 0xA9
    CMD_WRITE_POT1 = 0xAA
    CMD_WRITE_BOTH_POTS = 0xAF

    VARIANT_10K = 10000
    VARIANT_50K = 50000
    VARIANT_100K = 100000
    VARIANTS = [VARIANT_10K, VARIANT_50K, VARIANT_100K]

    def __init__(self, i2c=None, i2c_busnum=None, i2c_address=0x28,
                 variant=VARIANT_10K, **kwargs):
        if i2c_address not in range(0x28, 0x30):
            raise ValueError("DS1803 I2C address must be in the range [0x28..0x2F]")
        if variant not in DS1803.VARIANTS:
            raise ValueError("DS1803 variant is invalid")
        # Create I2C device.
        self.__name__ = "DS1803"
        self._i2c = i2c or I2C
        self._i2c_busnum = i2c_busnum or self._i2c.get_default_bus()
        self._i2c_address = i2c_address
        self._device = self._i2c.get_i2c_device(self._i2c_address, self._i2c_busnum, **kwargs)
        self._variant = variant

    def send_command(self, command, value):
        self._device.write8(command, value)

    def resistance_to_value(self, resistance):
        if resistance > self._variant:
            raise ValueError("Resistance {0} is invalid".format(resistance))
        value = int((resistance * 256.0) / self._variant)
        if value >= 256:
            value = 255
        return value

    def set_pot0_resistance(self, resistance):
        self.send_command(DS1803.CMD_WRITE_POT0, self.resistance_to_value(resistance))

    def set_pot1_resistance(self, resistance):
        self.send_command(DS1803.CMD_WRITE_POT1, self.resistance_to_value(resistance))

    def set_both_pots_resistance(self, resistance):
        self.send_command(DS1803.CMD_WRITE_BOTH_POTS, self.resistance_to_value(resistance))




"""
import time
ds1 = DS1803(i2c_address = 0x29)
ds2 = DS1803(i2c_address = 0x2f)

def sweep_all_levels():
    max = 255
    ds1.set_pot0_resistance(0)
    ds1.set_pot1_resistance(0)
    ds2.set_pot0_resistance(0)
    ds2.set_pot1_resistance(0)
    for level in range(max,0,-1):
        ds1.set_pot0_resistance(level)
        ds1.set_pot1_resistance(level)
        ds2.set_pot0_resistance(level)
        ds2.set_pot1_resistance(level)
        print level
        time.sleep(0.01)
    for level in range(max):
        ds1.set_pot0_resistance(level)
        ds1.set_pot1_resistance(level)
        ds2.set_pot0_resistance(level)
        ds2.set_pot1_resistance(level)
        print level
        time.sleep(0.01)

sweep_all_levels()


def sweep_all_levels():
    max = 100
    ds1.set_pot0_resistance(0)
    ds1.set_pot1_resistance(0)
    ds2.set_pot0_resistance(0)
    ds2.set_pot1_resistance(0)
    for level in range(max,0,-1):
        ds1.set_pot0_resistance(level/100)
        ds1.set_pot1_resistance(level/100)
        ds2.set_pot0_resistance(level/100)
        ds2.set_pot1_resistance(level/100)
        print level
        time.sleep(0.01)
    for level in range(0,max,1):
        ds1.set_pot0_resistance(level/100)
        ds1.set_pot1_resistance(level/100)
        ds2.set_pot0_resistance(level/100)
        ds2.set_pot1_resistance(level/100)
        print level
        time.sleep(0.01)

sweep_all_levels()


a = DS1803(i2c=0, i2c_address =0x29 , variant=10000)
print "a is a Dallas Semiconductor DS1803 digital Potentionmeter"
print "a.r_tot:", a.r_tot

for i in range(0, 255, 25):
    a.set_wiper(0, i)
    a.set_wiper(0, 255 - i)
    print "Wiper 0 is set to", a.get_wiper(0), "^=", a.get_r(0), "Ohm"
    print "Wiper 1 is set to", a.get_wiper(1), "^=", a.get_r(1), "Ohm"
    time.sleep(0.01)

for i in range(0, a.r_tot, 500):
    a.set_r(0, i)
    a.set_r(1, a.r_tot - i)
    print "Wiper 0 is set to", a.get_wiper(0), "^=", a.get_r(0), "Ohm"
    print "Wiper 1 is set to", a.get_wiper(1), "^=", a.get_r(1), "Ohm"
    time.sleep(0.01)

"""
