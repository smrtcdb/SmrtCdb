from hw_modules.ac_motor import ACMotor

# AC Motor
motor = ACMotor()

from hw_modules.button_int import ButtonInt
from hw_modules.buzzer import Buzzer
from hw_modules.slide_display import SlideDisplay
from settings import SHIFT_REGISTER_SRK, SHIFT_REGISTER_SER, SHIFT_REGISTER_SCK

display = SlideDisplay(srk=SHIFT_REGISTER_SRK, ser=SHIFT_REGISTER_SER, sck=SHIFT_REGISTER_SCK)

# Buzzer
sound = Buzzer()

from state_machine import StateMachine

print("-------------- Starting :) --------------")

from hw_modules.temperature import Temperature
import micropython
import uasyncio
import machine

from esp32 import Partition

from hw_modules.ir_remote import IRReceiver
from settings import WD_TIMEOUT, WATCHDOG_ENABLE, TEMPERATURE_PIN
from lib.ulogging import logger

# Validate OTA Update Partition
Partition.mark_app_valid_cancel_rollback()

micropython.alloc_emergency_exception_buf(100)


# async def garbage_collection_task():
#     gc.collect()
#     gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
#     await uasyncio.sleep(5)


async def wdt_task():
    wdt = machine.WDT(timeout=WD_TIMEOUT)
    while True:
        wdt.feed()
        await uasyncio.sleep(1)


# Display Task
async def display_task():
    loop = uasyncio.get_event_loop()
    while True:
        if not state_machine.is_power_off() and not display.is_displaying_command:
            if state_machine.mode == state_machine.NATURAL_MODE:
                value = state_machine.previous_speed
            else:
                value = motor.current_speed - 1

            await loop.create_task(
                display.display_driver.send_command(display.display_driver.SPEEDS, value)
            )
            display.write_to_leds()

        await uasyncio.sleep_ms(500)


# Set Motor Speed Task
async def motor_task():
    while True:
        previous = False
        while state_machine.mode == state_machine.NATURAL_MODE:
            # Calculate AC Fan Speed
            if previous:
                if state_machine.previous_speed == 1:
                    motor.set_speed(1)
                else:
                    motor.set_speed(state_machine.previous_speed - 1)

                previous = False
            else:
                if state_machine.previous_speed == 1:
                    motor.set_speed(2)
                else:
                    motor.set_speed(state_machine.previous_speed)

                previous = True

            await uasyncio.sleep(4)

        await uasyncio.sleep(5)


temperature = Temperature(TEMPERATURE_PIN)

# State Machine
state_machine = StateMachine(display, sound, motor, temperature)
logger.state_machine = state_machine

# OnBoard Buttons
action_on_off = lambda: state_machine.do(state_machine.action_on_off)
action_speed = lambda: state_machine.do(state_machine.action_speed, to_auto=False)
action_timer = lambda: state_machine.do(state_machine.action_timer)
action_natural = lambda: state_machine.do(state_machine.action_natural)
action_auto = lambda: state_machine.do(state_machine.action_auto)
action_dimmer = lambda: state_machine.do(state_machine.action_dimmer)
action_swing = lambda: state_machine.do(state_machine.action_swing)

button_mapping = {
    b'\x10': (action_on_off, None, None),
    b'\x08': (action_speed, None, None),
    b'\x04': (action_swing, None, None),
    b' ': (action_timer, None, None),
    b'@': (action_natural, None, None)
}
buttons = ButtonInt(int_pin=35, scl=18, sda=19, function_map=button_mapping)

# Start IR Receiver
ir_receiver = IRReceiver()
ir_receiver.action_auto = action_auto
ir_receiver.action_dimmer = action_dimmer
ir_receiver.action_onoff = action_on_off
ir_receiver.action_speed = action_speed
ir_receiver.action_timer = action_timer

# Create Tasks
loop = uasyncio.get_event_loop()
loop.create_task(display_task())
loop.create_task(temperature.temperature_task())  # temperature is not shown anywhere just yet
loop.create_task(motor_task())
loop.set_exception_handler(lambda _, context: logger.exc(context["exception"]))

if WATCHDOG_ENABLE:
    loop.create_task(wdt_task())

try:
    loop.run_forever()
except KeyboardInterrupt:
    print("Thanks for running :)")
finally:
    loop.close()  # close the loop once stopped running so we can start again
