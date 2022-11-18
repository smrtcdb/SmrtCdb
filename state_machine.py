import machine
from machine import Timer

import settings
from lib.ulogging import logger
from settings import TIMED_MODE_TIMER, SPEED_COUNT, DIMMING_TIMER, WD_STATE_FILE, WATCHDOG_ENABLE
from utils import read_from_json, write_to_json
from version import SW_VERSION


class StateMachine:
    POWER_OFF_MODE = 0
    AUTO_MODE = 5
    MANUAL_MODE = 3
    NATURAL_MODE = 1

    TIMER_OPTIONS = [0, 1, 2, 4, 8]

    def __init__(self, display, sound, motor, temperature):
        self.display = display
        self.display.set_state_machine(self)
        self.sound = sound
        self.motor = motor

        self.timer_index = 0
        self.natural = 0
        self.previous_speed = None
        self.temperature_sensor = temperature

        self.mode = self.POWER_OFF_MODE
        self.mode_timer = Timer(TIMED_MODE_TIMER)
        self.dimming_timer = Timer(DIMMING_TIMER)

        if read_from_json(WD_STATE_FILE, "forced") or \
                (WATCHDOG_ENABLE and machine.reset_cause() == machine.WDT_RESET):
            logger.info("Let's recover the latest state")
            self.load_state()
        else:
            self.init_device()

    def init_device(self):
        # self.display.send_command(self.display.POWER_OFF)  # done in display init
        # self.sound.send_command(self.sound.PLUG_IN) # done in buzzer init
        self.display.set_brightness(7)
        self.motor.set_speed(0)
        self.temperature_sensor.set_status(0)
        self.clear_state()

    def is_power_off(self):
        return self.mode == self.POWER_OFF_MODE

    def get_current_state(self, full=True):
        # todo: @mario Add key sensors: {dust:x...}
        state = {
            "mode": self.mode,
            "speed": self.motor.current_speed,
            "timer": self.TIMER_OPTIONS[self.timer_index],
        }
        if full:
            state.update({
                "sw_version": SW_VERSION,
                "brightness": self.display.brightness,
                "logs": {
                    "level": logger.level_str(),
                    "live": logger.get_live()
                }
            })

        return state

    def to_timer(self, num, user_action=False, write=True):
        self.timer_index = num

        # Display
        self.display.send_command(self.display.TIMER, self.timer_index, write=write)

        if self.timer_index == 0:
            # Timer
            self.mode_timer.deinit()

            if not user_action:
                self.action_on_off()

        else:
            # Timer
            period_time = self.TIMER_OPTIONS[num] - self.TIMER_OPTIONS[num - 1]

            if settings.DEBUG:
                period_time *= 10000  # Timer is shorten when debugging
            else:
                period_time *= 3600000  # Timer is in hours

            next_timer = num - 1
            self.mode_timer.init(mode=Timer.ONE_SHOT, period=period_time,
                                 callback=lambda t: self.do(
                                     self.to_timer, next_timer,
                                 ))

    def action_on_off(self, write=True, reset_timer=True, beep=True):
        if self.is_power_off():
            display_cmd, buzzer_cmd = self.display.POWER_ON, self.sound.POWER_ON
            self.motor.set_speed(1)
            self.mode = self.MANUAL_MODE
            self.temperature_sensor.set_status(1)
        else:
            display_cmd, buzzer_cmd = self.display.POWER_OFF, self.sound.POWER_OFF
            self.motor.set_speed(0)
            self.mode = self.POWER_OFF_MODE
            self.temperature_sensor.set_status(0)

        if beep:
            self.sound.send_command(buzzer_cmd)

        self.display.send_command(display_cmd, write=write)

        self.motor.set_swing(0)

        if self.timer_index > 0 and reset_timer:
            self.to_timer(0, user_action=True, write=False)

    def action_speed(self, next_speed=None, write=True, beep=True, to_auto=True, force=False):
        if not force and (self.is_power_off() and next_speed is None or
                          next_speed is not None and next_speed == self.motor.current_speed):
            logger.warning("Wont update the speed")
            return

        if self.is_power_off():  # Turned on from the WD
            self.action_on_off(write=False, beep=False)

        if next_speed is None:
            next_speed = (self.motor.current_speed + 1) % (SPEED_COUNT + 1)

        logger.info("Next speed: %s", next_speed)

        if next_speed == 0:
            if to_auto:
                return self.action_auto()
            next_speed = 1

        self.mode = self.MANUAL_MODE

        if beep:
            self.sound.send_command(self.sound.UPDATE)

        self.display.send_command(self.display.SPEED, next_speed, write=write)

        self.motor.set_speed(next_speed)

    def action_timer(self, next_timer=None):
        if next_timer is None:
            next_timer = (self.timer_index + 1) % len(self.TIMER_OPTIONS)
        elif next_timer == self.timer_index:
            logger.warning("Timer is already at index %s", self.timer_index)
            return

        logger.debug("Setting timer to %s", self.TIMER_OPTIONS[next_timer])

        self.to_timer(next_timer, user_action=True)
        self.sound.send_command(self.sound.UPDATE)

    def action_auto(self):
        if self.is_power_off():  # when turn on from the app
            return self.action_on_off()

        if self.mode == self.AUTO_MODE:
            self.mode = self.MANUAL_MODE
            command = self.display.SPEED, 1
        else:
            self.mode = self.AUTO_MODE
            command = self.display.AUTO,

        self.display.send_command(*command)
        self.sound.send_command(self.sound.UPDATE)
        self.motor.set_speed(1)

    def action_dimmer(self, brightness=None, beep=True):
        if not brightness:
            brightness = 1 if self.display.brightness == 7 else 7

        logger.debug("Dimming the display to %s", brightness)

        self.display.set_brightness(brightness)

        if beep:
            self.sound.send_command(self.sound.UPDATE)

    def action_swing(self, swing=None, beep=True, show=True):
        if self.is_power_off():
            return

        if swing is None:
            swing = 0 if self.motor.swing_value else 1

        logger.debug("swing to %s", swing)

        self.motor.set_swing(swing)

        if beep:
            self.sound.send_command(self.sound.UPDATE)

        if show:
            self.display.send_command(self.display.SWING, value=swing)

    def action_natural(self, natural=None, beep=True, show=True):
        if self.is_power_off():
            return

        logger.debug("natural to %s", natural)

        if self.mode != self.NATURAL_MODE:
            self.mode = self.NATURAL_MODE
            self.previous_speed = self.motor.current_speed
        else:
            return self.action_speed(next_speed=self.previous_speed or 1, beep=beep, write=show, force=True)

        if beep:
            self.sound.send_command(self.sound.UPDATE)

        if show:
            self.display.send_command(self.display.NATURAL)

    @staticmethod
    def clear_state():
        import os
        try:
            os.remove(WD_STATE_FILE)
            logger.info("States deleted")
        except OSError:
            logger.info("No states.json to delete")

    def write_state(self, forced=False):
        state = self.get_current_state()
        if forced:
            state["forced"] = True

        write_to_json(WD_STATE_FILE, state)
        logger.info("State was saved to Flash")

    def load_state(self):
        previous_state = read_from_json(WD_STATE_FILE)
        if previous_state:
            self.clear_state()
            logger.info("Loaded State")
            self.set_state(previous_state)
            logger.info("States are set. Current state: %s", self.get_current_state())
        else:
            logger.info("States are not saved on Flash. Starting as usual")
            self.init_device()

    def set_state(self, previous_state):
        logger.info("Setting previous state: %s", previous_state)

        previous_mode = previous_state["mode"]
        if previous_mode == self.AUTO_MODE:
            self.do(self.action_on_off, beep=False, reset_timer=False, write=False)
        elif previous_mode == self.MANUAL_MODE:
            self.do(
                self.action_speed, next_speed=previous_state["speed"], beep=False, write=False
            )
        else:
            self.display.send_command(self.display.POWER_OFF, write=False)

        # Set Timer State
        timer = previous_state.get("timer")
        if timer:
            self.do(
                self.to_timer, self.TIMER_OPTIONS.index(timer), user_action=True, write=False
            )

        self.action_dimmer(brightness=previous_state.get("brightness"), beep=False)

        logs = previous_state.get("logs")
        if logs:
            logger.set_live(logs["live"])
            logger.setLevel(logs["level"])

    def post_update(self, write_state=True):
        if WATCHDOG_ENABLE and write_state:
            self.write_state()

        self.dimming_timer.init(
            mode=Timer.ONE_SHOT, period=10000,
            callback=lambda x: self.display.set_brightness(1)
        )

    def do(self, *args, **kwargs):
        write_state = kwargs.pop("write_state", True)
        func = args[0]

        try:
            func(*args[1:], **kwargs)
        except Exception as e:
            logger.exc(e)

        self.display.set_brightness(7)

        if write_state:
            self.post_update()
