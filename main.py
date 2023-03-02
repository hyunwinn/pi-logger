import time
import datetime
import os
import RPi.GPIO as GPIO
from smbus2 import SMBus
from bno055 import BNO055
from gps import GPS
from tabulate import tabulate
from ds3231 import DS3231
from pi_camera import Pi_Camera

# BNO055 mode register
ACCGYRO = 0x05

# BNO055 setup		
bus = SMBus(2)
imu = BNO055(bus)
imu.mode(ACCGYRO)

# Ultimate GPS setup
gps = GPS()

# RTC setup
rtc = DS3231(bus)

# Initialise camera object
camera = Pi_Camera()

# GPIO pins setup
START_BUTTON = 26
GREEN_LED = 17
BLUE_LED = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(START_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BLUE_LED, GPIO.OUT)
GPIO.setup(GREEN_LED, GPIO.OUT)

# File directory
usb_directory = "/media/hsc35/8235-4EBC/data/"
directory = "/home/hsc35/data/"

# Define File
file_name = None
video_file = None
file = None

# Define debounce time of start button
DEBOUNCE_TIME = 200
toggle_state = False

# Define sampling intervals
IMU_SAMPLE_INTERVAL = 10
GPS_SAMPLE_INTERVAL = 500


def millis():
    return time.time_ns() // 1000000


# Define function to log when start button is pressed
def start_log(channel):
    global toggle_state, file_name, file
    
    if not toggle_state and not GPIO.input(START_BUTTON):
        GPIO.output(GREEN_LED, GPIO.HIGH)	# Turn green LED ON 
        toggle_state = True
        # Set start time
        t_start = millis()
        t_imu = t_start
        t_gps = t_start
        
        # Save to USB drive if mounted
        if os.path.exists(usb_directory):
            file_name = usb_directory + rtc.now()
            video_file = usb_directory + rtc.now() + '.h264'
        # Save to Pi
        else:
            file_name = directory + rtc.now()
            video_file = directory + rtc.now() + '.h264'
            
        file = open(file_name, "w")
        data_imu = [['Time (s)', 'Acceleration (m/s^2)', 'Gyroscope (deg/sec)']]
        data_gps = [['Time (s)', 'Latitude (deg)', 'Longitude (deg)',
                     'Altitude (m)', 'Velocity (m/s)']]
        
        while toggle_state:
            # Log IMU data
            if millis() >= t_imu + IMU_SAMPLE_INTERVAL:
                t_imu += IMU_SAMPLE_INTERVAL
                acc, gyro = imu.run()
                data_imu.append([((t_imu - t_start) / 1000), acc, gyro])
            
            # Log GPS data
            if millis() >= t_gps + GPS_SAMPLE_INTERVAL:
                t_gps += GPS_SAMPLE_INTERVAL
                lat, long, alt, vel = gps.run()
                data_gps.append([((t_gps - t_start) / 1000), lat, long, alt, vel])
            
            camera.start_recording(video_file)
            
            if GPIO.input(START_BUTTON):
                GPIO.output(GREEN_LED, GPIO.LOW)
                file.write(tabulate(data_imu, headers='firstrow',
                                    tablefmt='fancy_grid'))
                file.write('\n')
                file.write(tabulate(data_gps, headers='firstrow',
                                    tablefmt='fancy_grid'))
                camera.stop_recording()
                toggle_state = False
                file.close()


# Event detection with debounce for start button
GPIO.add_event_detect(START_BUTTON, GPIO.FALLING, callback=start_log,
                      bouncetime=DEBOUNCE_TIME)


# Main loop
try:
    while True:
        if not gps.fix():
            # Blink blue led
            GPIO.output(BLUE_LED, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(BLUE_LED, GPIO.LOW)
            time.sleep(1)
        else:
            GPIO.output(BLUE_LED, GPIO.LOW)
            time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()
    bus.close()
