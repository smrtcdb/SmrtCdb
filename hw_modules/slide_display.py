import uasyncio
from machine import Pin, PWM, Timer

from hw_modules.DotMatrix import DotMatrix
from hw_modules.shift_register import ShiftRegister


class SlideDisplay:
    POWER_ON = 0b1010100101
    POWER_OFF = 0b1111111111000011
    SWING = 4
    TIMER = 11
    SPEED = 6
    NATURAL = 3

    def __init__(self, srk, ser, sck):
        self.led_driver = ShiftRegister(srk=srk, ser=ser, sck=sck)
        self.display_driver = DotMatrix()
        self.led_driver_payload = 0
        self.clear_display()
        print("Display cleared")
        self.is_displaying_command = False
        self.brightness_driver = PWM(Pin(5, Pin.OUT), freq=400, duty=0)
        self.brightness = 1
        self.state_machine = None

    def write_to_leds(self):
        self.led_driver.write((1 << 16) - 1 - self.led_driver_payload)

    def set_brightness(self, brightness):
        if 0 < brightness <= 7:
            raise Exception("brightness should be from 1 to 7")

        if brightness < 2:
            self.set_bit(0, True)
            self.write_to_leds()

        duty = (brightness * 1023) / 7
        self.brightness_driver.duty(int(duty))

    def set_bit(self, bit, value):
        if value:
            self.led_driver_payload |= (1 << bit)
        else:
            self.led_driver_payload &= ~(1 << bit)

    def clear_display(self):
        self.display_driver.clear()

        self.led_driver_payload = 1
        self.write_to_leds()

    def send_command(self, command, value=None, write=True):
        self.is_displaying_command = True

        matrix_cmd, matrix_value = None, None

        if command == self.POWER_OFF:
            matrix_cmd, matrix_value = self.display_driver.POWER_OFF, None
            self.clear_display()

        else:
            if command == self.SPEED:
                self.led_driver_payload &= 0b1100000111110111  # turn off speeds and natural led
                for i in range(9, 9 + value):
                    self.led_driver_payload += 2 ** i

                self.set_bit(self.SPEED - 1, value=1)  # speed button
                matrix_cmd, matrix_value = self.display_driver.SPEED_TRANSITIONS, (value - 2) % 5

            elif command == self.SWING:
                self.set_bit(self.SWING, value=value)
                matrix_cmd, matrix_value = self.display_driver.SWINGS, value

            elif command == self.NATURAL:
                self.set_bit(self.NATURAL, value=1)
                matrix_cmd, matrix_value = self.display_driver.NATURAL_WIND, None

            elif command == self.TIMER:
                print("timer")
                matrix_cmd, matrix_value = self.display_driver.TIMERS, value

            elif command == self.POWER_ON:
                self.led_driver_payload = self.POWER_ON
                matrix_cmd, matrix_value = self.display_driver.POWER_ON, None

            else:
                self.led_driver_payload = command

        if write:
            self.write_to_leds()
            if matrix_cmd:
                uasyncio.run(
                    self.display_driver.send_command(matrix_cmd, matrix_value)
                )
                if not self.state_machine.is_power_off():
                    self.is_displaying_command = False
