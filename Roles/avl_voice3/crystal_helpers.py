import wiringpi as wpi

spi_channel_lookup = {
  # spi channel   |   pi pin
  0:                  27,
  1:                  28,
  2:                  29
  }

# 8-bit parallel port, use for quick testing
pport_8bit = {
  # bit		  |  [fd
  7:                  0,
  6:                  2,
  5:                  3,
  4:                  21,
  3:                  22,
  2:                  23,
  1:                  24,
  0:                  25
}
pport_en1 = 26
pport_en2 = 1

# file descriptor for digital potentiometer (i2c)
digipot1 = 0
digipot2 = 0

# store current frequencies
freq_a = 0
freq_b = 0
freq_c = 0

# for convenience, save characters
delay_us = wpi.delayMicroseconds

# convert (base-10) frequency to a pair of 16-bit SPI commands for AD9833
def freq_word (freq, prnt=False) :

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
def spiRW (channel, message) :
  wpi.digitalWrite(spi_channel_lookup[channel], 0); delay_us(1)  # pull low

  msg = wpi.wiringPiSPIDataRW(0, message)
  delay_us(1)

  wpi.digitalWrite(spi_channel_lookup[channel], 1); delay_us(1)  # pull high

  return msg


def init () :
  print 'Initialize WiringPi'
  print wpi.wiringPiSetup()

  # in SPI mode 2, clock idle HIGH, data clocked on falling edge
  print 'Initialize SPI Devices'
  print wpi.wiringPiSPISetupMode(0, 500000, 2)
  #print wpi.wiringPiSPISetupMode(1, 500000, 2)
  #print wpi.wiringPiSPISetupMode(2, 500000, 2)

  # setup pins for additional spi channels
  for v in spi_channel_lookup.itervalues():
    print v
    print wpi.pinMode(v, 1)         # configure pin as output
    print wpi.digitalWrite(v, 1)    # default HIGH

  # reset AD9833, and set up to use consecutive writes for full 28-bt rees
  print 'Reset AD9833 on channel 0'
  print spiRW(0, chr(0x21) + chr(0x00)) # enter reset mode
  wpi.delay(500)
  print spiRW(0, chr(0x00) + chr(0x00))
  print spiRW(0, chr(0x00) + chr(0x00))
  print spiRW(0, chr(0x20) + chr(0x00)) # exit reset mode

  print 'Reset AD9833 on channel 1'
  print spiRW(1, chr(0x21) + chr(0x00)) # enter reset mode
  wpi.delay(500)
  print spiRW(1, chr(0x00) + chr(0x00))
  print spiRW(1, chr(0x00) + chr(0x00))
  print spiRW(1, chr(0x20) + chr(0x00)) # exit reset mode

  print 'Reset AD9833 on channel 2'
  print spiRW(2, chr(0x21) + chr(0x00)) # enter reset mode
  wpi.delay(500)
  print spiRW(2, chr(0x00) + chr(0x00))
  print spiRW(2, chr(0x00) + chr(0x00))
  print spiRW(2, chr(0x20) + chr(0x00)) # exit reset mode

  # setup i2c interfrace
  print 'Initialize I2C Devices'
  global digipot1
  digipot1 = wpi.wiringPiI2CSetup(0x29)    # DS18030-50+ digital potentiometer
  print digipot1

  global digipot2
  digipot2 = wpi.wiringPiI2CSetup(0x2f)    # master gain
  print digipot2


  # setup parallel port
  print 'Initialize parallel port'
  for v in pport_8bit.itervalues():
    print v
    print wpi.pinMode(v, wpi.OUTPUT)
    print wpi.digitalWrite(v, 0)

  print pport_en1, pport_en2

  wpi.pinMode(pport_en1, wpi.OUTPUT)
  wpi.digitalWrite(pport_en1, 0)

  wpi.pinMode(pport_en2, wpi.OUTPUT)
  wpi.digitalWrite(pport_en2, 0)

def send_freq (ch, freq, prnt=True, sine=True) :

  word = freq_word(freq, prnt)

  if (prnt):
    if (sine):
      print spiRW(ch, chr(0b00100000) + chr(0b0))
    else:
      print spiRW(ch, chr(0b00100000) + chr(0b10))
    print spiRW(ch, word[1])
    print spiRW(ch, word[0])

  else:
    spiRW(ch, chr(0b00100000) + chr(0b0))
    spiRW(ch, word[1])
    spiRW(ch, word[0])

  global freq_a, freq_b, freq_c

  if (ch == 0):
    freq_a = freq
  elif (ch == 1):
    freq_b = freq
  else:
    freq_c = freq

  #return word


def freq_sweep (ch, start, end, step, t_delay=100, prnt=True, sine=True):

  freq = start

  while (freq < end):
    send_freq(ch, freq, prnt, sine)
    wpi.delay(t_delay)
    freq += step

  while (freq > start):
    send_freq(ch, freq, prnt, sine)
    wpi.delay(t_delay)
    freq -= step



def set_levels (ch, level):

  if (ch > 0):
    command = 0b10101001 if ch == 1 else 0b10101010
    print bin(command)
    return wpi.wiringPiI2CWriteReg8 (digipot1, command, level & 255)

  return wpi.wiringPiI2CWriteReg8(digipot2, 0b10101001, level & 255)

def quick_start():
  init()

  print 'set osc 0 to 167450-220'
  send_freq(0, 167450-220)

  print 'set osc 1 to 0'
  send_freq(1, 0)

  print 'set osc 2 to 0'
  send_freq(2, 0)

  print 'set pot 1 to 0'
  set_levels(1, 0)

  print 'set pot 2 to 0'
  set_levels(2, 0)


def sweep (target=2000, dt=100, df=100):

  global freq_a
  global freq_b
  global freq_c

  ctr = 0

  while (ctr < target):
    send_freq(0, freq_a-df)
    send_freq(1, freq_b-df)
    send_freq(2, freq_c-df)
    wpi.delay(dt)
    ctr += df

  while (ctr > 0):
    send_freq(0, freq_a+df)
    send_freq(1, freq_b+df)
    send_freq(2, freq_c+df)
    wpi.delay(dt)
    ctr -= df


def pport_write (en, word):
  word = bin(word & 255)[2:].zfill(8)
  print word

  pport_en = pport_en1 if en == 1 else pport_en2

  wpi.digitalWrite(pport_en, 0)
  for i in xrange(8):
    print i, wpi.digitalWrite(pport_8bit[i], int(word[7-i]))
  
  wpi.digitalWrite(pport_en, 1)
  delay_us(4)
  wpi.digitalWrite(pport_en, 0)
