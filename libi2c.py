# -*- coding: utf-8 -*-
from time import sleep
import RPi.GPIO as GPIO

class I2C:
    """
    Bit-banging, python-only, I²C interface with top-notch debugging. ;-)
    """

    def __init__(self, pin_sda=3, pin_scl=5, delay=0.0001):
        """
        Initialize I²C interface

        Args:
          sda, scl: Pins used for SDA/SCL
        """
        self._debug = []

        self.pin_sda = pin_sda
        self.pin_scl = pin_scl
        self.delay = delay

        assert pin_sda >= 1 and pin_sda <= 26
        assert pin_scl >= 1 and pin_scl <= 26

        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(True)

        self.scl_out()
        self.sda_out()
        self.sda_high()
        self.scl_high()
        sleep(self.delay * 5)

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        GPIO.cleanup()

    def show_error(self):
        "Display error with debugging info"
        print "ERROR", "".join(self._debug)

    ##
    # Low-level bit-banging
    ##
    def sda_in(self):
        "Change direction of SDA pin"
        self.sda_low()
        self._debug.append("[D_IN]")
        if self.pin_sda == 3:
            # Already has physical pull-up and additional breaks the protocol
            # in my case.
            GPIO.setup(self.pin_sda, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
        else:
            # NOTE: Disable if using own pull-ups.
            GPIO.setup(self.pin_sda, GPIO.IN, pull_up_down=GPIO.PUD_ON)

    def sda_out(self, initial=GPIO.HIGH):
        "Change direction of SDA pin"
        self._debug.append("[D_OUT]")
        GPIO.setup(self.pin_sda, GPIO.OUT, initial=initial)

    def scl_out(self):
        "Change direction of SCL pin"
        GPIO.setup(self.pin_scl, GPIO.OUT, initial=GPIO.HIGH)

    def sda_high(self):
        GPIO.output(self.pin_sda, GPIO.HIGH)
        sleep(self.delay)
        self._debug.append('D')

    def sda_low(self):
        GPIO.output(self.pin_sda, GPIO.LOW)
        sleep(self.delay)
        self._debug.append('d')

    def scl_high(self):
        GPIO.output(self.pin_scl, GPIO.HIGH)
        sleep(self.delay)
        self._debug.append('C')

    def scl_low(self):
        GPIO.output(self.pin_scl, GPIO.LOW)
        sleep(self.delay)
        self._debug.append('c')

    def read_sda(self):
        bit = GPIO.input(self.pin_sda)
        self._debug.append(str(bit))
        return bit

    ##
    # I²C building blocks
    ##
    def start_bit(self):
        "sda high to low, during high clock. Also a repeated start."
        self._debug.append("[START]")
        self.sda_high()
        self.scl_high()
        sleep(self.delay*10)
        self.sda_low()
        self.scl_low()

    def stop_bit(self):
        "sda to high during high clock"
        self._debug.append("[STOP]")
        self.scl_low()
        self.sda_low()
        self.scl_high()
        self.sda_high()

    def write_byte(self, data):
        """Write one Byte to the I2C line"""
        assert data >= 0x00 and data <= 0xFF
        self._debug.append("[W:" + hex(data) + "]")
        # Clock should currently be LOW.

        for shift in range(7, -1, -1):
            bit = data & (1 << shift)
            if bit:
                self.sda_high()
            else:
                self.sda_low()
            self.scl_high()
            self.scl_low()

        # Read ack of the slave
        self.sda_in()
        self.scl_high()
        ack = self.read_sda()
        self.scl_low()
        self.sda_out()
        return ack

    def read_byte(self):
        "Read one byte from the SDA line while clocking the SCL line"
        self._debug.append("[R]")
        self.sda_in()
        byte = 0x00
        for shift in range(7, -1, -1):
            self.scl_high()
            bit = self.read_sda()
            if bit:
                byte |= 1<<shift
            self.scl_low()
        self.sda_out()
        return byte

    def nack(self):
        "NACK byte, usually means: don't send more"
        self.sda_high()
        self.scl_high()
        self.scl_low()

    def ack(self):
        "ACK byte, usually means: send more"
        self.sda_low()
        self.scl_high()
        self.scl_low()

    ##
    # "High" level operations
    ##
    def read_register(self, address, register):
        "Read from register"
        self._debug = []
        assert address >= 0 and address <= 127
        addr = address << 1
        self.start_bit()
        ack = self.write_byte(addr)
        if ack != 0:
            self.stop_bit()
            self.show_error()
            return None

        ack = self.write_byte(register)
        if ack != 0:
            self.stop_bit()
            self.show_error()
            return None

        self.start_bit()

        ack = self.write_byte(addr | 0x01) # READ?
        if ack != 0:
            self.stop_bit()
            self.show_error()
            return None
        byte = self.read_byte()
        self.nack()
        self.stop_bit()
        return byte

    def write_register(self, address, register, value):
        "Write value into the register"
        self._debug = []

        assert address >= 0 and address <= 127
        addr = address << 1
        self.start_bit()
        ack = self.write_byte(addr)
        if ack != 0:
            self.stop_bit()
            self.show_error()
            return None

        ack = self.write_byte(register)
        if ack != 0:
            self.stop_bit()
            self.show_error()
            return None

        ack = self.write_byte(value)
        if ack != 0:
            self.stop_bit()
            self.show_error()
            return None

        self.stop_bit()
        return ack
