import math

import uasyncio
from machine import Pin, ADC

invBeta = 1.00 / 3977.00
adcMax = 1023
invT0 = 1.00 / 298.15
numSamples = 5


class Temperature:
    def __init__(self, pin):
        self.driver = ADC(Pin(pin))
        self.driver.atten(ADC.ATTN_11DB)
        self.driver.width(ADC.WIDTH_10BIT)
        self.measure = 0
        self.status = 0

    def set_status(self, status):
        self.status = status

    async def temperature_task(self):
        while True:
            while not self.status:
                await uasyncio.sleep(2)

            adcVal = 0
            for i in range(numSamples):
                adcVal += self.driver.read() * 0.72
                await uasyncio.sleep_ms(100)

            adcVal = adcVal / numSamples

            try:
                K = 1.00 / (invT0 + invBeta * (math.log(adcMax / adcVal - 1.00)))
            except ZeroDivisionError:
                print("zero divison")
                continue

            C = K - 273.15
            self.measure = int(C)
            print("temperature measure", self.measure)
            await uasyncio.sleep_ms(5000)  # wait for 5 seconds

            # F = ((9.0 * C) / 5.00) + 32.00  # convert to Celsius
            # print("Kelvin", K, "deg. C", C, " deg. F", F)
            # print("temperature measure", self.measure)

    def get_temperature(self):
        import utime

        adcVal = 0

        for i in range(numSamples):
            adcVal += self.driver.read() * 0.72
            utime.sleep_ms(100)

        adcVal = adcVal / numSamples
        K = 1.00 / (invT0 + invBeta * (math.log(adcMax / adcVal - 1.00)))
        C = K - 273.15
        # F = ((9.0 * C) / 5.00) + 32.00  # convert to Celsius
        # print("Kelvin", K, "deg. C", C, " deg. F", F)
        self.measure = int(C)
        print("temperature measure", self.measure)
