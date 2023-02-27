import time
import adafruit_gps
import serial

class GPS:
    
    def __init__(self):
        # Create a serial connection for the GPS connection 
        uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=10)

        # Create a GPS module instance.
        self.gps = adafruit_gps.GPS(uart, debug=False)

        # Initialize the GPS module   
        self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0") 

        # Set update rate to twice a second (2hz)
        self.gps.send_command(b"PMTK220,500")
        
    
    def fix(self):
        # return True if gps has fixed
        self.gps.update()
        
        if self.gps.has_fix:
            return True
        else:
            return False


    def run(self):
        # return latitude, longitude, altitude, and speed if fixed
        self.gps.update()
        
        if self.fix():
            # Speed knots output of None cannot be converted to m/s
            if self.gps.speed_knots is not None:
                return ("{0:.6f}".format(self.gps.latitude),
                        "{0:.6f}".format(self.gps.longitude),
                        self.gps.altitude_m, self.gps.speed_knots * 0.5144444)
            else:
                return ("{0:.6f}".format(self.gps.latitude),
                        "{0:.6f}".format(self.gps.longitude),
                        self.gps.altitude_m, '0')
        else:
            return ('0', '0', '0', '0')
