from machine import SoftSPI, Pin

from settings import SHIFT_REGISTER_SRK, SHIFT_REGISTER_SER, SHIFT_REGISTER_SCK


class ShiftRegister:
    def __init__(self, srk, ser, sck, init_value=None):
        self.spi = SoftSPI(baudrate=1000000, polarity=1, phase=0,
                           sck=Pin(sck), mosi=Pin(ser), miso=Pin(2))
        self.spi.init()
        self.rclk = Pin(srk, Pin.OUT)
        if init_value:
            self.write(init_value)

    def write(self, data):
        nums = (data >> 8, data & 255)
        self.rclk.value(0)
        for num in nums:
            buf = num.to_bytes(1, 'little')
            self.spi.write(bytes(buf))
        self.rclk.value(1)  # latch data to output

    def write_single(self, data):
        self.rclk.value(0)
        buf = data.to_bytes(1, 'little')
        self.spi.write(bytes(buf))
        self.rclk.value(1)  # latch data to output
