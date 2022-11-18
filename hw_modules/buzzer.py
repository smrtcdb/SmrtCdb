import time

import uasyncio
from machine import Pin, PWM

from settings import BUZZER_PIN, DEBUG


class Buzzer:
    POWER_ON = [
        (1661, 110),  # (freq, time)
        (1865, 110),
        (1976, 110),
        (2217, 110),
        (2489, 225)
    ]

    POWER_OFF = [
        (2300, 110),
        (2093, 110),
        (1760, 110),
        (1480, 110),
        (1319, 225)
    ]

    PLUG_IN = [(4500, 200)]
    UPDATE = [(4500, 100)]

    def __init__(self, buzzer_gpio=BUZZER_PIN):
        self.gpio = buzzer_gpio
        self.driver = None
        self.send_command(self.PLUG_IN)

    def send_command(self, commands):
        if DEBUG:  # so it doesn't bother while debugging
            return

        uasyncio.create_task(self.play_sound(commands))

    def __del__(self):
        self.driver.deinit()

    async def play_sound(self, commands):
        if not self.driver:
            self.driver = PWM(Pin(self.gpio, Pin.OUT), freq=400, duty=0)

        for command in commands:
            self.driver.freq(command[0])
            self.driver.duty(300)
            time.sleep(command[1] / 1000)

        self.driver.duty(0)
