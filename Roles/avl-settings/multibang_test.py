
import Adafruit_GPIO as GPIO
import adafruit_spi_modified as SPI

class MCP3008s(object):
    def __init__(self, spi_clock_pin, miso_pin, mosi_pin, chip_select_pins):
        self.gpio = GPIO.get_platform_gpio()
        self.chip_select_pins = chip_select_pins
        self._spi = SPI.BitBang(gpio, spi_clock_pin, mosi_pin, miso_pin)
        self._spi.set_clock_hz(1000000)
        self._spi.set_mode(0)
        self._spi.set_bit_order(SPI.MSBFIRST)

    def read(self, chip_select_pin, adc_number):
        assert 0 <= adc_number <= 7, 'ADC number must be a value of 0-7!'
        # Build a single channel read command.
        # For example channel zero = 0b11000000
        command = 0b11 << 6                  # Start bit, single channel read
        command |= (adc_number & 0x07) << 3  # Channel number (in 3 bits)
        # Note the bottom 3 bits of command are 0, this is to account for the
        # extra clock to do the conversion, and the low null bit returned at
        # the start of the response.
        resp = self._spi.transfer(chip_select_pin,[command, 0x0, 0x0])
        # Parse out the 10 bits of response data and return it.
        result = (resp[0] & 0x01) << 9
        result |= (resp[1] & 0xFF) << 1
        result |= (resp[2] & 0x80) >> 7
        return result & 0x3FF

    def scan_all(self):
        for chip_select_pin in self.chip_select_pins:
            for adc_number in range(8):
                print self.read(chip_select_pin, adc_number)


spi_clock_pin  = 11
miso_pin = 9
mosi_pin = 10
chip_select_pins = [8,7]

mcp3008s = MCP3008s(spi_clock_pin, miso_pin, mosi_pin, chip_select_pins)

mcp3008s.scan_all()
