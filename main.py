import time
import datetime
import os
import RPi.GPIO as GPIO
from smbus2 import SMBus
from bno055 import BNO055
from tabulate import tabulate
from gps import GPS

# ACCGYRO register value
ACCGYRO = 0x05

# BNO055 setup		
bus = SMBus(2)
imu = BNO055(bus)
imu.mode(ACCGYRO)

# Ultimate GPS setup
gps = GPS()

# GPIO pins setup
GREEN_BUTTON = 26
GREEN_LED = 17
BLUE_LED = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(GREEN_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BLUE_LED, GPIO.OUT)
GPIO.setup(GREEN_LED, GPIO.OUT)

# Data directory
directory = "/home/hsc35/data/"

if not os.path.exists(directory):
    os.makedirs(directory)

toggle_state = False
file_name = None
file = None

# Define debounce time of Green button
DEBOUNCE_TIME = 200

# Define sampling intervals
IMU_SAMPLE_INTERVAL = 10
GPS_SAMPLE_INTERVAL = 500

def millis():
    return time.time_ns() // 1000000

# Define function to run when green button is pressed
def green_button_callback(channel):
    global toggle_state, file_name, file
    
    if not toggle_state and not GPIO.input(GREEN_BUTTON):
        GPIO.output(GREEN_LED, GPIO.HIGH)
        toggle_state = True
        t_start = millis()
        t_imu = t_start
        t_gps = t_start
        
        file_name = directory + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        file = open(file_name, "w")
        data_imu = [['Time (s)', 'Acceleration (m/s^2)', 'Gyroscope (deg/sec)']]
        data_gps = [['Time (s)', 'Latitude (deg)', 'Longitude (deg)',
                     'Altitude (m)', 'Velocity (m/s)']]
        
        while toggle_state:
            if millis() >= t_imu + IMU_SAMPLE_INTERVAL:
                t_imu += IMU_SAMPLE_INTERVAL
                acc, gyro = imu.run()
                data_imu.append([((t_imu - t_start) / 1000), acc, gyro])
                
            if millis() >= t_gps + GPS_SAMPLE_INTERVAL:
                t_gps += GPS_SAMPLE_INTERVAL
                lat, long, alt, vel = gps.run()
                data_gps.append([((t_gps - t_start) / 1000), lat, long, alt, vel])
            
            if GPIO.input(GREEN_BUTTON):
                GPIO.output(GREEN_LED, GPIO.LOW)
                file.write(tabulate(data_imu, headers='firstrow',
                                    tablefmt='fancy_grid'))
                file.write('\n')
                file.write(tabulate(data_gps, headers='firstrow',
                                    tablefmt='fancy_grid'))
                toggle_state = False
                file.close()

# Event detection with debounce for green button
GPIO.add_event_detect(GREEN_BUTTON, GPIO.FALLING, callback=green_button_callback,
                      bouncetime=DEBOUNCE_TIME)

# Main loop
try:
    while True:
        if not gps.fix():
            GPIO.output(BLUE_LED, GPIO.LOW)
            time.sleep(1)
            GPIO.output(BLUE_LED, GPIO.HIGH)
            time.sleep(1)
        else:
            GPIO.output(BLUE_LED, GPIO.LOW)
            time.sleep(1)
            
except KeyboardInterrupt:
    GPIO.output(BLUE_LED, GPIO.LOW)
    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.cleanup()
    bus.close()
