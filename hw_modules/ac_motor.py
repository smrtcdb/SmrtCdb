from machine import Pin

from settings import SPEED_PINS, SWING_PIN

from hw_modules.swing import Swing


class ACMotor:
    def __init__(self, speed_pins=SPEED_PINS):
        self.speed_driver = [Pin(pin_number, Pin.OUT, value=0) for pin_number in speed_pins]

        self.current_speed = 0
        self.swing = Swing(SWING_PIN)

    @property
    def swing_value(self):
        return self.swing.value

    def set_speed(self, relative_speed):
        print("MOTOR set speed", relative_speed)
        if self.current_speed == relative_speed:
            return

        self.current_speed = relative_speed
        [speed_pin.off() for speed_pin in self.speed_driver]
        if relative_speed != 0:
            self.speed_driver[relative_speed - 1].on()

    def set_swing(self, value):
        print("SWING set speed", value)

        self.swing.set_swing(value)
