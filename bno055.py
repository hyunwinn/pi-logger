import time

# I2C addresses
I2C_ADDR_1 = 0x28
I2C_ADDR_2 = 0x29

BNO055_ID = 0xA0

# Chip ID register   
CHIP_ID = 0x00

# Acceleration data register
ACC_DATA_X_LSB = 0x08

# Gyroscope data register
GYR_DATA_X_LSB = 0x14

# Unit selection register
UNIT_SEL = 0x3B

# Mode registers
OPR_MODE = 0x3D
PWR_MODE = 0x3E 
SYS_TRIGGER = 0x3F

# Axis remap register
AXIS_MAP_SIGN = 0x42  # Axis sign register

# Axis remap values
AXIS_REMAP_POSITIVE = 0x00
AXIS_REMAP_NEGATIVE = 0x01

# Sensor configuration regiters
ACC_CONFIG = 0x08
GYR_CONFIG_0 = 0x0A
GYR_CONFIG_1 = 0x0B

# Sensor configuration data
ACCEL_2G = 0x00
ACCEL_7_81HZ = 0x00
ACCEL_NORMAL = 0x00

GYR_500DPS = 0x18
GYR_32HZ = 0x38
GYR_NORMAL = 0x00

# Power mode
NORMAL_POWER = 0x00

# Operation Mode
CONFIG = 0x00
ACCGYRO = 0x05
AMG = 0x07
NDOF = 0x0C


class BNO055(object):

    def __init__(self, bus, address=I2C_ADDR_1, units = 0):
        # create an I2C bus object and set the address
        self.bus = bus
        self.address = address
        self.mode(CONFIG)

        # check the chip ID
        if BNO055_ID != self._read_register(CHIP_ID):
            raise RuntimeError("BNO055 failed to respond")
        
        # reset the device
        self._reset()
 
        # set to normal power mode
        self._write_register(PWR_MODE, NORMAL_POWER)

        # set the unit selection bits
        self._write_register(UNIT_SEL, units)

        # set the axis sign configuration
        self._set_axis()
        
        # set the accelerometer configuration
        self._set_acc()
        
        # set the gyroscope configuration
        self._set_gyr()
        
        # switch to default mode
        self.mode(NDOF)


    def _reset(self):
        self.mode(CONFIG)
        try:
            self._write_register(SYS_TRIGGER, 0x20)
        # error due to the chip resetting
        except OSError: 
            pass
        # wait for the chip to reset
        time.sleep(0.65)


    def _set_axis(self, x_sign=AXIS_REMAP_NEGATIVE,
            y_sign=AXIS_REMAP_NEGATIVE, z_sign = AXIS_REMAP_POSITIVE):
        # Set the axis remap sign register value.
        sign_config = 0x00
        sign_config |= x_sign << 2
        sign_config |= y_sign << 1
        sign_config |= z_sign
        self._write_register(AXIS_MAP_SIGN, sign_config)
        
        
    def _set_acc(self):
        acc_config = ACCEL_NORMAL + ACCEL_7_81HZ + ACCEL_2G 
        self._write_register(ACC_CONFIG, acc_config)
    
    
    def _set_gyr(self):
        gyr_config = GYR_32HZ + GYR_500DPS
        self._write_register(GYR_CONFIG_0, gyr_config)
        self._write_register(GYR_CONFIG_1, GYR_NORMAL)
    

    def mode(self, mode):
        # the mode value is invalid
        if mode not in [CONFIG, ACCGYRO, AMG, NDOF]:
            raise ValueError
        self._mode = mode
        self._write_register(OPR_MODE, mode)
        # delay for more than 20 milliseconds
        time.sleep(0.03)
        

    def _read_vector(self, reg, count = 3):
        # Reference: Dexter Industry sensor code
        data = self.bus.read_i2c_block_data(self.address, reg, count*2)
        result = [0]*count
        for i in range(count):
            result[i] = (((data[(i * 2) + 1] & 0xFF) << 8) | (data[(i * 2)] & 0xFF)) & 0xFFFF
            if result[i] & 0x8000:
                result[i] -= 0x10000
        return result
    

    def acceleration(self):
        # Returns the current accelerometer reading in m/s^2.
        if self._mode in [ACCGYRO, AMG, NDOF]:
            x, y, z = self._read_vector(ACC_DATA_X_LSB)
            return (x / 100.0, y / 100.0, z / 100.0)
        else:
            return (None, None, None)
    

    def gyroscope(self):
        # Returns the current gyroscope reading in degrees per second.
        if self._mode in [ACCGYRO, AMG, NDOF]:
            x, y, z = self._read_vector(GYR_DATA_X_LSB)
            return (x / 16.0, y / 16.0, z / 16.0)
        return (None, None, None)


    def run(self):
        # Returns readings from accelerometer and gyroscope
        return self.acceleration(), self.gyroscope()


    def _write_register(self, reg, data):
        # write a byte of data to a register
        self.bus.write_byte_data(self.address, reg, data)


    def _read_register(self, reg):
        # read a byte of data from a register
        return self.bus.read_byte_data(self.address, reg)
