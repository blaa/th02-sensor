#!/usr/bin/env python
import sys
from libi2c import I2C
from libth02 import TH02

def main():
    i2c = I2C(pin_sda=3, pin_scl=5)
    device = TH02(i2c)

    if sys.argv[-1] == "temperature":
        temp = device.get_temperature()
        print(temp)
    elif sys.argv[-1] == "humidity":
        humidity = device.get_humidity()
        print(humidity)
    else:
        print("Pass 'temperature' or 'humidity' as an argument")

if __name__ == "__main__":
    main()
