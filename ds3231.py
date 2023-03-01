import time

# I2C address
I2C_ADDR = 0x68

# Time registers
SECOND = 0x00
MINUTE = 0x01
HOUR = 0x02
DAY = 0x03
DATE = 0x04
MONTH = 0x05
YEAR = 0x06

# Control register
CONTROL = 0x0E


class DS3231(object):

    def __init__(self, bus, address=I2C_ADDR):
        self.bus = bus
        self.address = address
        self._write_register(CONTROL, 0x18)  # Enable 8.192kHz Output

    
    def now(self):
        # Output current time in datetime.datetime.now() format
        def _bcdToDec(bcd): # Convert binary coded decimal (BCD) to decimal
            return ((bcd & 0x70) >> 4) * 10 + (bcd & 0x0F)
        
        data = bytearray(7)
        data = self.bus.read_i2c_block_data(self.address, 0x00, 7)
        # weekday not outputted in datetime.dateime.now()
        S, M, H, wday, d, m, Y = [_bcdToDec(x) for x in data]
        m &= 0x1F   # Strip century bit
        Y += 2000
        
        return (f'{Y:02d}-{m:02d}-{d:02d} {H:02d}:{M:02d}:{S:02d}')


    def set_time(self, t=None):
        # Set time to current time if t=None or to desired time
        def _decToBcd(self, dec, is_month=False):
            # Convert decimal to BCD
            tens, units = divmod(dec, 10)
            bcd = (tens << 4) + units
            if is_month:   # Add century bit to MSB
                bcd |= 0x80
            return bcd.to_bytes(1, "little")

        Y, m, d, H, M, S, wday, yday = time.localtime() if t is None else t

        self._write_register(SECOND, _decToBcd(S))
        self._write_register(MINUTE, _decToBcd(M))
        self._write_register(HOUR, _decToBcd(H))
        self._write_register(DAY, _decToBcd(wday))
        self._write_register(DATE, _decToBcd(d))
        self._write_register(MONTH, _decToBcd(m, True))
        self._write_register(YEAR, _decToBcd(Y))
    

    def _write_register(self, reg, data):
        # write a byte of data to a register
        self.bus.write_byte_data(self.address, reg, data)
