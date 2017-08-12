import Adafruit_GPIO as GPIO
import adafruit_spi_modified as SPI
import os
import Queue
import settings
import time
import threading
import traceback
import sys


BASE_PATH = os.path.dirname(os.path.realpath(__file__))
UPPER_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
DEVICES_PATH = "%s/Hosts/" % (BASE_PATH )
THIRTYBIRDS_PATH = "%s/thirtybirds_2_0" % (UPPER_PATH )

sys.path.append(BASE_PATH)
sys.path.append(UPPER_PATH)

from thirtybirds_2_0.Network.manager import init as network_init

class MCP3008s(object):
    def __init__(self, spi_clock_pin, miso_pin, mosi_pin, chip_select_pins):
        self.gpio = GPIO.get_platform_gpio()
        self.chip_select_pins = chip_select_pins
        self._spi = SPI.BitBang(self.gpio, spi_clock_pin, mosi_pin, miso_pin)
        self._spi.set_clock_hz(1000000)
        self._spi.set_mode(0)
        self._spi.set_bit_order(SPI.MSBFIRST)
        for chip_select_pin in chip_select_pins:
            self.gpio.setup(chip_select_pin, GPIO.OUT)
            self.gpio.set_high(chip_select_pin)

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
        adcs = []
        for chip_select_pin in self.chip_select_pins:
            channels = []
            for adc_number in range(8):
                channels.append(self.read(chip_select_pin, adc_number))
            adcs.append(channels)
        return adcs

class Potentiometers(threading.Thread):
    def __init__(self, network_send_ref):
        threading.Thread.__init__(self)
        self.network_send_ref = network_send_ref
        self.noise_threshold = 10
        self.spi_clock_pin = 11
        self.miso_pin = 9
        self.mosi_pin = 10
        self.chip_select_pins = [8,7,12,16,20,21]
        self.potentiometers_layout  = [
            [
                "",
                "voice_1_overtone_2_harmonic",
                "voice_1_overtone_2_volume",
                "voice_1_overtone_1_fine",
                "voice_1_overtone_1_harmonic",
                "voice_1_overtone_1_volume",
                "voice_1_root_fine",
                "voice_1_root_harmonic",
            ],
            [
                "",
                "",
                "voice_1_formant_front_back",
                "voice_1_formant_open_close",
                "voice_1_formant_pitch",                
                "voice_1_formant_volume",
                "voice_1_overtone_2_fine", 
                ""
            ],
            [
                "voice_2_root_harmonic",
                "voice_2_root_fine",
                "voice_2_overtone_1_volume",
                "voice_2_overtone_1_harmonic",
                "voice_2_overtone_1_fine",
                "voice_2_overtone_2_volume",
                "voice_2_overtone_2_harmonic",
                ""
            ],
            [
                "",
                "",
                "voice_2_formant_front_back",
                "voice_2_formant_open_close",
                "voice_2_formant_pitch",                
                "voice_2_formant_volume",
                "voice_2_overtone_2_fine", 
                ""
            ],
            [
                "voice_3_root_harmonic",
                "voice_3_root_fine",
                "voice_3_overtone_1_volume",
                "voice_3_overtone_1_harmonic",
                "voice_3_overtone_1_fine",
                "voice_3_overtone_2_volume",
                "voice_3_overtone_2_harmonic",
                ""
            ],
            [
                "layer_speed",
                "",
                "voice_3_formant_front_back",
                "voice_3_formant_open_close",
                "voice_3_formant_pitch",                
                "voice_3_formant_volume",
                "voice_3_overtone_2_fine", 
                ""
            ]
        ]
        self.potentiometer_last_value  = [
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0]
        ]
        self.mcp3008s = MCP3008s(self.spi_clock_pin, self.miso_pin, self.mosi_pin, self.chip_select_pins)
    
    def run(self):
        while True:
            all_adc_values =  self.mcp3008s.scan_all()
            #print all_adc_values
            for adc in range(len(all_adc_values)):
                for channel in range(8):
                    adc_value = 1023 - all_adc_values[adc][channel]
                    if abs(adc_value - self.potentiometer_last_value[adc][channel] ) > self.noise_threshold:
                        self.network_send_ref(self.potentiometers_layout[adc][channel], adc_value/1023.0)
                        print adc, channel, self.potentiometers_layout[adc][channel], adc_value
                    self.potentiometer_last_value[adc][channel] = adc_value
            time.sleep(0.1)

class Network(object):
    def __init__(self, hostname, network_message_handler, network_status_handler):
        self.hostname = hostname
        self.thirtybirds = network_init(
            hostname=hostname,
            role="client",
            discovery_multicastGroup=settings.discovery_multicastGroup,
            discovery_multicastPort=settings.discovery_multicastPort,
            discovery_responsePort=settings.discovery_responsePort,
            pubsub_pubPort=settings.pubsub_pubPort,
            message_callback=network_message_handler,
            status_callback=network_status_handler
        )

# Main handles network send/recv and can see all other classes directly
class Main(threading.Thread):
    def __init__(self, hostname):
        threading.Thread.__init__(self)
        self.network = Network(hostname, self.network_message_handler, self.network_status_handler)
        self.queue = Queue.Queue()
        self.network.thirtybirds.subscribe_to_topic("door_closed")
        self.potentiometers = Potentiometers(self.network.thirtybirds.send) # self.network.thirtybirds.send
        self.potentiometers.daemon = True
        self.potentiometers.start()
    def network_message_handler(self, topic_msg):
        # this method runs in the thread of the caller, not the tread of Main
        topic, msg =  topic_msg # separating just to eval msg.  best to do it early.  it should be done in TB.
        if len(msg) > 0: 
            msg = eval(msg)
        self.add_to_queue(topic, msg)

    def network_status_handler(self, topic_msg):
        # this method runs in the thread of the caller, not the tread of Main
        print "Main.network_status_handler", topic_msg

    def add_to_queue(self, topic, msg):
        self.queue.put((topic, msg))

    def run(self):
        while True:
            try:
                topic, msg = self.queue.get(True)
                if topic == "door_closed":
                    door.add_to_queue(msg)
                    self.network.thirtybirds.send("door_status", True)
                    
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print e, repr(traceback.format_exception(exc_type, exc_value,exc_traceback))

def init(hostname):
    main = Main(hostname)
    main.daemon = True
    main.start()
    return main


