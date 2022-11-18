from machine import Pin


class Swing:
    def __init__(self, motor):
        self.driver = Pin(motor, Pin.OUT, value=0)
        self.value = 0

    def set_swing(self, value):
        if value not in (0, 1):
            raise Exception("Only binary accepted")
        self.value = value
        self.driver.value(value)
