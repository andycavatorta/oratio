import wiringpi as wpi

# run this first, initializes wiringpi library and sets SPI speed
def init (speed=500000, cs1=27, cs2=28, mode=0):
  wpi.wiringPiSetup()
  wpi.wiringPiSPISetupMode(0, speed, mode)
  wpi.pinMode(cs1, wpi.OUTPUT)
  wpi.pinMode(cs2, wpi.OUTPUT)

# hacky way of using more than two spi lines
def spiRW (pin, msg):
  wpi.digitalWrite(pin, 0); wpi.delayMicroseconds(1)
  msg = wpi.wiringPiSPIDataRW(0, msg)
  wpi.delayMicroseconds(1)
  wpi.digitalWrite(pin, 1); wpi.delayMicroseconds(1)
  return msg

# get pot reading (0-1024) given chip select (cs) and channel (ch)
def read_channel (cs, ch):
  spiRW(cs, chr(ch << 4) + chr(0x00))
  val = spiRW(cs, chr(0x00) + chr(0x00))
  print val
  print ord(val[1][0])
  print ord(val[1][1])
  return (ord(val[1][0]) << 2) | (ord(val[1][1]) >> 6)

# quick way to get rid of outliers, make better later
def read_avg (cs, ch, n=20):
  return sum([read_channel(cs, ch) for i in xrange(n)]) / n