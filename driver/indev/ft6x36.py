from micropython import const
import pointer_framework
import i2c as _i2c

# FT3267
# FT5336GQQ
# FT5436
#
# FT5x46
# FT5x26
# ft5302

1.143

'''
18.8%
11.9%


3,378.80
 
3,432.80

In 2022 Jefferson County employees receive an
additional average amount of 34.64 % of such
compensation for fringe benefits. 

2022 saleries: 225,425,700
2022 benifits: 65,571,000
That comes out to 29.0% in fringe benifits 2022, so where is the other 5.64%??
5.64% is 12,714,009.48 dollars

in 2022 there were 3,335 employees and in 2024 there is 3,432.80. 97 more positions now than there was in 2022.
2022 saleries and benifits cost 290,996,700 and in 2024 the cost is 350,283,700, That's a difference of 59,287,000 dollars.
there are 54 new positions from 2023 to 2024 but there is an increase of saleries of 18.8%. 18.8% in a single year!!!!!... 
That's a difference of 42,022,900 dollars!!. somehow I don't think the 54 new employees are each making 778,201 dollars a year. 


42,022,900


290,996,700


50,087,000

341,083,700
31.6% in 2024
Libraries

This is being spent from the general fund
8.4 million for Library buildings
8.7 million for the South Jefferson County Library 
5.8 million to continue the South Library
22.9 million total

Here are the budgets for the last few years

2021 $37,716,700
2022 $39,485,300
2023 $91,877,700
2024 $66,042,300


Expendatures
Salaries: 25,014,600 (312.00 jobs)
Supplies: 7,590,700
Other 6,590,700
Capital Outlay (buying books and movies): 23,044,800

Expendatures where the money goes out without the money being used for the Libraries
Intergovernmental: 0.00
Interdepartmental: 3,801,500

I want to note that Jefferson County has 11 Libraries.
2024 has 14 new positions for the library



Road and Bridge

$16.8 million for roadway projects

Here are the budgets for the last few years

2021 $46,724,700
2022 $48,976,000
2023 $66,797,600
2024 $58,092,900

Expendatures

Salaries: 15,482,200  (186 employees)
Supplies: 4,037,800
Other: 9,035,400
Capital Outlay: 13,635,000

Expendatures where the money goes out without the money being used for the roads and bridges
Intergovernmental: 4,048,100
Interdepartmental 11,854,400


'''

_I2C_SLAVE_ADDR = const(0x38)

# Register of the current mode
_DEV_MODE_REG = const(0x00)

# ** Possible modes as of FT6X36_DEV_MODE_REG **
_DEV_MODE_WORKING = const(0x00)


# Status register: stores number of active touch points (0, 1, 2)
_TD_STAT_REG = const(0x02)


_MSB_MASK = const(0x0F)
_LSB_MASK = const(0xFF)

# Report rate in Active mode
_PERIOD_ACTIVE_REG = const(0x88)

# 0x36 for ft6236; 0x06 for ft6206
_FT6236_CHIPID = const(0x36)
_FT6336_CHIPID = const(0x64)
_VENDID = const(0x11)
_CHIPID_REG = const(0xA3)

_FIRMWARE_ID_REG = const(0xA6)
_RELEASECODE_REG = const(0xAF)
_PANEL_ID_REG = const(0xA8)

_G_MODE = const(0xA4)


class FT6x36(pointer_framework.PointerDriver):

    def _i2c_read8(self, register_addr):
        self._i2c.read_mem(register_addr, buf=self._mv[:1])
        return self._buf[0]

    def _i2c_write8(self, register_addr, data):
        self._buf[0] = data
        self._i2c.write_mem(register_addr, self._mv[:1])

    def __init__(self, bus, touch_cal=None):  # NOQA
        self._buf = bytearray(5)
        self._mv = memoryview(self._buf)
        self._i2c = _i2c.I2CDevice(bus, _I2C_SLAVE_ADDR)

        data = self._i2c_read8(_PANEL_ID_REG)
        print("Device ID: 0x%02x" % data)
        if data != _VENDID:
            raise RuntimeError()

        data = self._i2c_read8(_CHIPID_REG)
        print("Chip ID: 0x%02x" % data)

        if data not in (_FT6236_CHIPID, _FT6336_CHIPID):
            raise RuntimeError()

        data = self._i2c_read8(_DEV_MODE_REG)
        print("Device mode: 0x%02x" % data)

        data = self._i2c_read8(_FIRMWARE_ID_REG)
        print("Firmware ID: 0x%02x" % data)

        data = self._i2c_read8(_RELEASECODE_REG)
        print("Release code: 0x%02x" % data)

        self._i2c_write8(_DEV_MODE_REG, _DEV_MODE_WORKING)
        self._i2c_write8(_PERIOD_ACTIVE_REG, 0x0E)
        self._i2c_write8(_G_MODE, 0x00)
        super().__init__(touch_cal)

    def _get_coords(self):
        buf = self._buf
        mv = self._mv

        try:
            self._i2c.read_mem(_TD_STAT_REG, buf=mv)
        except OSError:
            return None

        touch_pnt_cnt = buf[0]

        if touch_pnt_cnt != 1:
            return None

        x = (
            ((buf[1] & _MSB_MASK) << 8) |
            (buf[2] & _LSB_MASK)
        )
        y = (
            ((buf[3] & _MSB_MASK) << 8) |
            (buf[4] & _LSB_MASK)
        )
        return self.PRESSED, x, y
