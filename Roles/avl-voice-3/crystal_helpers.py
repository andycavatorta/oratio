import serial
import serial.tools.list_ports
import wiringpi as wpi

spi_channel_lookup = {
  # spi channel   |   pi pin
  0:                  21,
  1:                  22,
  2:                  23
  }

digipot = 0  # file descriptor for digital potentiometer (i2c)
ser = None   # interface to USB serial

# bit-bang SPI
bb_mosi = 4
bb_sck = 5

# for convenience, save characters
delay_us = wpi.delayMicroseconds

# convert (base-10) frequency to a pair of 16-bit SPI commands for AD9833
def freq_word(freq, prnt=False):

  # 28-bit frequency to write is given by f_target / f_clock * 2^28 
  freq_adj = int(freq / 25e6 * 2**28)

  first_msb = 0x40 | ( (freq_adj & 0xfc00000) >> 22 )
  first_lsb = (freq_adj & 0x3fc000) >> 14

  second_msb = 0x40 | ( (freq_adj & 0x3f00) >> 8 )
  second_lsb = freq_adj & 0xff  

  def bin_fmt (word) :
    return bin(word)[2:].zfill(8)

  if (prnt) :
    print 'first word:  ' + bin_fmt(first_msb) + '  ' + bin_fmt(first_lsb)
    print 'second word: ' + bin_fmt(second_msb) + '  ' + bin_fmt(second_lsb)

  return chr(first_msb) + chr(first_lsb), chr(second_msb) + chr(second_lsb)


# wrapper for wiringpi SPI R/W, but with support for more than two lines
def spiRW(channel, message):
  wpi.digitalWrite(spi_channel_lookup[channel], 0); delay_us(1)  # pull low

  msg = wpi.wiringPiSPIDataRW(0, message)
  delay_us(1)

  wpi.digitalWrite(spi_channel_lookup[channel], 1); delay_us(1)  # pull high

  return msg


def init():
  global digipot, ser

  print 'Initialize WiringPi'
  wpi.wiringPiSetup()

  # in SPI mode 2, clock idle HIGH, data clocked on falling edge
  print 'Initialize SPI devices'
  wpi.wiringPiSPISetupMode(0, 500000, 2)

  # setup pins for additional spi channels
  for v in spi_channel_lookup.itervalues():
    wpi.pinMode(v, 1)         # configure pin as output
    wpi.digitalWrite(v, 1)    # default HIGH

  print "Reset AD9833 for all channels"
  for i in xrange(3):

    # reset AD9833, and set up to use consecutive writes for full 28-bt res
    spiRW(i, chr(0x21) + chr(0x00)) # enter reset mode
    wpi.delay(500)
    spiRW(i, chr(0x00) + chr(0x00))
    spiRW(i, chr(0x00) + chr(0x00))
    spiRW(i, chr(0x20) + chr(0x00)) # exit reset mode

    set_freq(i, 0)      # freq set to zero
    set_volume(i, 0)    # volume set to zero

  # setup i2c interfrace
  print 'Initialize I2C devices'
  digipot = wpi.wiringPiI2CSetup(0x29)    # DS18030-50+ digital potentiometer

  # serial interface for talking to frequency counter
  print 'Open Serial Port'
  port = None
  for i in serial.tools.list_ports.comports():
    if len(i[2]) > 2 and i[2][0:3] == 'USB':
      port = i[0]
      print 'found', port
      break

  if port != None:
    ser = serial.Serial(port, 57600)
  else:
    ser = None
    print "problem finding serial port"

  # bit-bang spi
  print 'Configure bit-bang SPI pins'
  for pin in [bb_mosi, bb_sck]:
    wpi.pinMode(pin, 1)        # configure pin as output
    wpi.digitalWrite(pin, 0)   # default HIGH

  print 'Done'


def set_freq(ch, freq, prnt=False):
  # convert frequency to pair of 16-bit words
  word = freq_word(freq, prnt)

  spiRW(ch, chr(0x20) + chr(0b0))   # control bytes
  spiRW(ch, word[1])                # first freq word
  spiRW(ch, word[0])                # second freq word


def set_volume (ch, level):
  # for channels 1 and 2 (the overtones) set volume via i2c digital pot
  if (ch > 0):
    command = 0b10101001 if ch == 1 else 0b10101010
    return wpi.wiringPiI2CWriteReg8 (digipot, command, level & 255)

  # master volume has a separate protocol (bit-bang spi)
  return set_volume_master(level)

def set_volume_master(level):
  # get binary representation of level
  level_bin = bin(int(level))[2:].zfill(8);

  for i in xrange(16):
    wpi.digitalWrite(bb_mosi, 0 if i > 7 else int(level_bin[i]))
    wpi.digitalWrite(bb_sck, 1)
    wpi.digitalWrite(bb_sck, 0)


# check serial port for intermediate frequency, return None if no data
def measure_xtal_freq():
  if not ser.inWaiting(): return None

  while ser.inWaiting():
    raw = ser.readline()

  return None if len(raw) < 7 else float(raw.strip()) / 10.0