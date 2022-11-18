import time

from machine import Pin

from lib.ulogging import logger
from settings import IR_PIN


class IRReceiver:
    TIME_0 = 1125
    TIME_1 = 2225
    PERIOD_TIME = 67500
    LEADING_BURST = 9000
    LEADING_SPACE = 4500

    def __init__(self):
        self.p = Pin(IR_PIN, Pin.IN)
        self.p.irq(trigger=Pin.IRQ_FALLING, handler=self.ir_callback)
        self.action_speed = None
        self.action_timer = None
        self.action_auto = None
        self.action_dimmer = None
        self.action_onoff = None
        self.l = [0] * 34

    def ir_callback(self, pin):
        self.l.append(time.ticks_us())
        del self.l[0]
        if abs(self.l[1] - self.l[0] - (self.LEADING_BURST + self.LEADING_SPACE)) < 5000 and abs(
                self.l[-1] - self.l[0] - self.PERIOD_TIME) < 5000:
            data_a = [0] * 4
            data_b = [0] * 4
            for i in range(2, 6):
                data_a[i - 2] = (self.l[i + 1 + 16] - self.l[i + 16]) > (self.TIME_0 + self.TIME_1) / 2
                data_b[i - 2] = (self.l[i + 1 + 24] - self.l[i + 24]) < (self.TIME_0 + self.TIME_1) / 2

            if data_a == data_b:
                if data_a == [1, 1, 0, 0]:
                    logger.debug("IR Controller Speed.")
                    self.action_speed()
                elif data_a == [1, 0, 1, 0]:
                    logger.debug("IR Controller Timer.")
                    self.action_timer()
                elif data_a == [0, 0, 0, 1]:
                    logger.debug("IR Controller Auto.")
                    self.action_auto()
                elif data_a == [0, 1, 1, 0]:
                    logger.debug("IR Controller Dimmer")
                    self.action_dimmer()
                elif data_a == [1, 0, 0, 0]:
                    logger.debug("IR Controller OnOff.")
                    self.action_onoff()
                else:
                    logger.warning("Not my Controller! Data Recieved: %s", data_a)
