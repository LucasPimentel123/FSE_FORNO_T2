import smbus2
import bme280

class I2C:
    def __init__(self):
        return self.return_room_temp()

    def return_room_temp(self):
        port = 1
        address = "0x76"
        bus = smbus2.SMBus(port)

        calibration_params = bme280.load_calibration_params(bus, address)


        data = bme280.sample(bus, address, calibration_params)

        return data.temperature
