import wiringpi as wpi

chip_select_pins = [21,22,23,24,25,26,27,28,29]
wpi.wiringPiSetup()
wpi.wiringPiSPISetupMode(0, 500000, 0)

for pin in chip_select_pins:
    wpi.pinMode(pin, wpi.OUTPUT)

def spi_read_write(pin, msg):
    wpi.digitalWrite(pin, 0)
    wpi.delayMicroseconds(100)
    msg = wpi.wiringPiSPIDataRW(0, msg)
    wpi.delayMicroseconds(100)
    wpi.digitalWrite(pin, 1)
    wpi.delayMicroseconds(100)
    return msg

def read_channel(cs, ch):
    spi_read_write(cs, chr(ch << 4) + chr(0x00))
    val = spi_read_write(cs, chr(0x00) + chr(0x00))
    print "--->", cs, ch, val
    return (ord(val[1][0]) << 2) | (ord(val[1][1]) >> 6)

for chip_select_pin in chip_select_pins:
    for chip_channel in range(7):
        print read_channel(chip_select_pin, chip_channel)




