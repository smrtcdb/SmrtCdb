from machine import Pin
from machine import Timer

from lib.chinese_cap import ChineseCapSense
from lib.ulogging import logger
from settings import BUTTON_TIMER, BUTTON_TIMER_PERIOD, DEBOUNCE_TIME, LONG_LONG_PRESS_TIME, LONG_PRESS_TIME


class ButtonInt:
    def __init__(self, int_pin, function_map, scl, sda, extra_time=0):
        self.btn = Pin(int_pin, Pin.IN, Pin.PULL_UP)
        self.btn.irq(trigger=Pin.IRQ_RISING, handler=self.btn_down)
        self.timer = Timer(BUTTON_TIMER)
        self.is_short_cb_executed = False
        self.is_long_cb_executed = False
        self.is_longlong_cb_executed = False
        self.press_time = 0
        self.tick_counter = 0
        self.timer_running = False
        self.extra_time = extra_time
        self.function_map = function_map
        print("start cap sense")
        self.driver = ChineseCapSense(None, scl=scl, sda=sda)
        print("finish cap sense")
        self.short_cb, self.long_cb, self.longlong_cb = None, None, None

    def tick(self, timer):
        # todo: cannot use long and longlong because using pressing longlong will also call long
        self.tick_counter = self.tick_counter + 1

        if not self.is_short_cb_executed:
            self.short_cb()
            self.is_short_cb_executed = True

        elif self.tick_counter == LONG_PRESS_TIME + self.extra_time:
            logger.debug("Long Press! Time: %s", self.tick_counter * BUTTON_TIMER_PERIOD + self.timer.value())

            if self.long_cb and not self.is_long_cb_executed:
                self.is_long_cb_executed = True
                self.long_cb()

        elif self.tick_counter == LONG_LONG_PRESS_TIME + self.extra_time:
            logger.debug("Long Long Press! Time: %s", self.tick_counter * BUTTON_TIMER_PERIOD + self.timer.value())

            if self.longlong_cb and not self.is_longlong_cb_executed:
                self.is_longlong_cb_executed = True
                self.longlong_cb()

    async def check_touch(self):  # if we don't want to use the ic interrupt pin, we can check the press value asynch
        import uasyncio

        while True:
            data = self.driver.get_press()
            if data != b'\x00':
                func = self.function_map.get(data)
                if func:
                    logger.debug("Pressed. Function: %s data: %s", func, data)
                    func()
                    while self.driver.get_press() == data:
                        await uasyncio.sleep_ms(10)

            await uasyncio.sleep_ms(200)

    def btn_down(self, btn):
        #         if not btn.value():
        if not self.timer_running:
            press = self.driver.get_press()
            self.short_cb, self.long_cb, self.longlong_cb = self.function_map.get(
                press,
                (None, None, None)
            )
            if self.short_cb is None:
                print("Got unkown pressed:", press)
                return

            self.timer_running = True
            self.timer.init(mode=Timer.PERIODIC, period=BUTTON_TIMER_PERIOD * 1000, callback=self.tick)
            self.is_long_cb_executed = False
            self.is_longlong_cb_executed = False
            self.is_short_cb_executed = False

        #         else:
        else:
            self.timer_running = False
            self.press_time = self.timer.value()
            self.timer.deinit()

            if self.press_time > DEBOUNCE_TIME and not self.is_short_cb_executed:
                if self.tick_counter < 2:
                    logger.debug("Short Press! Time: %s", self.tick_counter * BUTTON_TIMER_PERIOD + self.press_time)
                    if self.short_cb:
                        self.short_cb()
            #             else:
            #                 print("some shitty noise", self.press_time)

            self.press_time = 0
            self.tick_counter = 0
            self.short_cb, self.long_cb, self.longlong_cb = None, None, None
