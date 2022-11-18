LF = const(0x0A)  # New Line
CR = const(0x0D)  # Carriage  return
SPC = const(0x20)  # Space

Ch_enable = const(0x01)  # Touch Channel Enable/Disable
i2c_id = const(0x06)  # I2C Address od ANSG08
Clock_ctrl = const(0x34)  # Clock Control Register (init_cal_opt, Reserved, clk_sel, rb_sel)
Global_ctrl1 = const(0x36)  # Global Option Control Register1 
# (response_off_ctrl, response_ctrl, bf_mode, Software Reset)
State_count = const(0x37)  # Cal_pre_scale
Global_ctrl2 = const(0x38)  # Global Option Control Register2
# (imp_sel,Single/Multi ,Cal_Hold_time,Reserved, ck_off)

#  Sensitivity level (threshold, Register Value X 0.025% = (1 Step=0.025%)  
#  The lower value of these register ANSG08 has, the higher sensitivity ANSG08 has. 
#  And if user wants to set higher sensitivity over 0.9%,           
Sensitivity1 = const(0x39)  # ch1,Default: 0x1C X 0.025% = 0.70% (threshold)
Sensitivity2 = const(0x3A)  # ch2
Sensitivity3 = const(0x3B)  # ch3
Sensitivity4 = const(0x3C)  # ch4
Sensitivity5 = const(0x3D)  # ch5
Sensitivity6 = const(0x3E)  # ch6
Sensitivity7 = const(0x3F)  # ch7
Sensitivity8 = const(0x40)  # ch8

Cal_speed1 = const(0x41)  # Calibration Speed Control at BF mode
Cal_speed2 = const(0x42)  # Calibration Speed Control at BS mode

PWM_ctrl1 = const(0x43)  # LED PWM control Register (D2,D1)
PWM_ctrl2 = const(0x44)  # LED PWM control Register (D4,D3)
PWM_ctrl3 = const(0x45)  # LED PWM control Register (D6,D5)
PWM_ctrl4 = const(0x46)  # LED PWM control Regispwqvb
Port_Mode = const(0x4F)  # Select the output port operation mode of each channel.
prom_cmd = const(0x5C)  # EEPROM Control Register
prom_addr = const(0x5F)  # EEPROM data address select register

Output = const(0x2A)  # Touch Output Data Register  (ch = 1bit)

ANSG08_ID = const(0x24)  # 0x48 >> 1 (0b0100100 + W/R Bit1,  7bit=0x24, 8bit=0x48)


def to_bytearray(bytes_list):
    array = bytearray(len(bytes_list))
    for i, b in enumerate(bytes_list):
        array[i] = b
    return array


class ChineseCapSense:
    def __init__(self, i2c_id=None, scl=None, sda=None):
        if i2c_id is not None:
            from machine import I2C
            self.i2c = I2C(0, freq=200000)
        else:
            from machine import SoftI2C, Pin
            self.i2c = SoftI2C(scl=Pin(scl), sda=Pin(sda), freq=200000)
        print([hex(i) for i in self.i2c.scan()])
        self.init_display()

    def init_display(self):
        l = []
        # ------------------ Software Reset Enable (Set)----------------------
        l.clear()
        l.append(Global_ctrl1)  #
        l.append(0x4D)  #
        self.i2c.writeto(0x24, to_bytearray(l))

        # --------------- Hidden Register Start ---------------------------------
        # user does not change the register. please contact us to change.
        # -----------------------------------------------------------------------
        l.clear()
        l.append(0x05)  # address
        l.append(0x80)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x08)  # address
        l.append(0x11)  # 0x08h
        l.append(0x11)  # 0x09h
        l.append(0x11)  # 0x0Ah
        l.append(0x11)  # 0x0Bh
        l.append(0x11)  # 0x0Ch
        l.append(0x11)  # 0x0Dh
        l.append(0xA1)  # 0x0Eh
        l.append(0x10)  # 0x0Fh
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x10)  # address
        l.append(0xCE)  # 0x10h  # IC Reset Value: 0xF5 (-0.55%) ->0xCE (-2.55%)
        l.append(0x20)  # 0x11h
        l.append(0xFF)  # 0x12h
        # l.append(0x88)  #0x12h
        # Change the value of the register 0x12h when a problem occurs due to voltage drop
        l.append(0x92)  # 0x13h
        l.append(0x83)  # 0x14h  #IC Reset Value: 0x83 (3ch) -> 0x87(7ch)
        l.append(0x73)  # 0x15h
        l.append(0x64)  # 0x16h
        l.append(0xFF)  # 0x17h
        l.append(0x2B)  # 0x18h
        l.append(0x11)  # 0x19h
        l.append(0x03)  # 0x1Ah  # IC Reset Value: 0x01 ->0x03
        l.append(0xFF)  # 0x1Bh
        l.append(0x10)  # 0x1Ch
        l.append(0xFF)  # 0x1Dh
        l.append(0xFF)  # 0x1Eh
        l.append(0xFD)  # 0x1Fh
        l.append(0x7F)  # 0x20h
        l.append(0x00)  # 0x21h
        l.append(0xC0)  # 0x22h
        l.append(0x00)  # 0x23h
        l.append(0xC0)  # 0x24h
        l.append(0x00)  # 0x25h
        l.append(0xFF)  # 0x26h
        l.append(0xFF)  # 0x27h
        l.append(0xFF)  # 0x28h
        l.append(0xFF)  # 0x29h
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x2B)  # address
        l.append(0x00)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x2C)  # address
        l.append(0x00)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x35)  # address
        l.append(0xC0)  # data
        # IC Reset Value = 0xC0 (Sensing Frequency Low) -> 0x40 (Sensing Frequency High)
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x47)  # address
        l.append(0x0D)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x48)  # address
        l.append(0x00)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x49)  # address
        l.append(0x80)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x4A)  # address
        l.append(0x08)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x59)  # address
        l.append(0x00)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x5A)  # address
        l.append(0x00)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x5F)  # address
        l.append(0x00)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x60)  # address
        l.append(0x00)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x61)  # address
        l.append(0x00)  # data
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(0x7F)  # address
        l.append(0x00)  # data
        self.i2c.writeto(0x24, to_bytearray(l))
        # --------------- Hidden Register End-------------------------------

        # ---------------- user code ---------------------#
        l.clear()
        l.append(Ch_enable)  # 0x01h
        l.append(0xFF)  # 0:Touch Key Disable, 1: Touch Key Enable
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(Clock_ctrl)  # 0x34h
        l.append(0x65)  # #IC Reset value 0x05 -> 0x65
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(Global_ctrl1)  # 0x36h
        l.append(0x4D)  #
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(State_count)  # 0x37
        l.append(0xE6)  # #IC Reset value 0xFF -> 0xE6
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(Global_ctrl2)  # 0x38h
        l.append(0xFC)  # Low imp. Multi, touch out expire time enable
        # l.append(0xC0) # touch out expire time disable
        self.i2c.writeto(0x24, to_bytearray(l))

        # ------------ Sensitivity control  -----------------------------------
        l.clear()
        l.append(Sensitivity1)  # 0x39h
        l.append(0x24)  # HEX x 0.025 = 0.90%
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(Sensitivity2)  # 0x3Ah
        l.append(0x24)  # HEX x 0.025 = 0.90%
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(Sensitivity3)  # 0x3Bh
        l.append(0x24)  # HEX x 0.025 = 0.90%
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(Sensitivity4)  # 0x3Ch
        l.append(0x24)  # HEX x 0.025 = 0.90%
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(Sensitivity5)  # 0x3Dh
        l.append(0x24)  # HEX x 0.025 = 0.90%
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(Sensitivity6)  # 0x3Eh
        l.append(0x24)  # HEX x 0.025 = 0.90%
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(Sensitivity7)  # 0x3Fh
        l.append(0x24)  # HEX x 0.025 = 0.90%
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(Sensitivity8)  # 0x40h
        l.append(0x24)  # HEX x 0.025 = 0.90%
        self.i2c.writeto(0x24, to_bytearray(l))

        # ------------ Calibration Speed Control ------------------------
        l.clear()
        l.append(Cal_speed1)  # 0x41h
        l.append(0x66)  #
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(Cal_speed2)  # 0x42h
        l.append(0x66)  #
        self.i2c.writeto(0x24, to_bytearray(l))
        # -------------------- LED PWM Control -----------------------------
        l.clear()
        l.append(PWM_ctrl1)  # 0x43h
        l.append(0x00)  # D2,D1
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(PWM_ctrl2)  # 0x44h
        l.append(0x00)  # D4,D3
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(PWM_ctrl3)  # 0x45h
        l.append(0x00)  # D6,D5
        self.i2c.writeto(0x24, to_bytearray(l))

        l.clear()
        l.append(PWM_ctrl4)  # 0x46h
        l.append(0x00)  # D8,D7
        self.i2c.writeto(0x24, to_bytearray(l))
        # ---------------- Port Mode Control Register --------------------------
        l.clear()
        l.append(Port_Mode)  # 0x4Fh
        l.append(0x01)  # 0: Parallel output mode, 1: LED Drive mode
        self.i2c.writeto(0x24, to_bytearray(l))

        # ------------------ Software Reset Disable (Clear) ---------------------
        l.clear()
        l.append(Global_ctrl1)  #
        l.append(0x4C)  #
        self.i2c.writeto(0x24, to_bytearray(l))

    def brightness(self, val=None):
        self.i2c.writeto(0x24, to_bytearray([PWM_ctrl1, val]))

    def get_press(self):
        self.i2c.writeto(0x24, to_bytearray([Output]))
        r = self.i2c.readfrom(0x24, 1)
        print(r)
        return r
