import time
import os
import concurrent.futures
from datetime import datetime
import RPi.GPIO as GPIO
from smbus2 import SMBus
from picamera2 import Picamera2
from tabulate import tabulate
from bno055 import BNO055
from gps import GPS
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

# Pi camera setup
camera = Picamera2()

# RTC setup
rtc = DS3231(bus)

# GPIO pins setup
START_BUTTON = 26
CAMERA_TOGGLE = 6
GREEN_LED = 17
BLUE_LED = 27
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(START_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(CAMERA_TOGGLE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
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

# Define sampling interval
IMU_SAMPLE_INTERVAL = 10
GPS_SAMPLE_INTERVAL = 500


def millis():
    # Returns current time in milliseconds
    return time.time_ns() // 1000000


def log_imu(t_start):
    # Returns a tuple (including imu readings)
    # The first element of the tuple indicate whether the request was after the sampling interval
    if millis() >= t_start:
        acc, gyr = imu.run()
        return (True, t_start + IMU_SAMPLE_INTERVAL, datetime.now(), acc, gyr)
    else:
        return (False, 0)


def log_gps(t_start):
    # Returns a tuple (including gps readings)
    if millis() >= t_start:
        return (True, t_start + GPS_SAMPLE_INTERVAL, datetime.now(), gps.run())
    else:
        return (False, 0)
    

# Define function to log when start button is pressed
def start_log(channel):
    global toggle_state, file_name, file
    
    if not toggle_state and not GPIO.input(START_BUTTON):
        GPIO.output(GREEN_LED, GPIO.HIGH)	# Turn green LED ON 
        toggle_state = True
        
        # Set start time
        t_imu = millis()
        t_gps = t_imu
        
        # Save to USB drive if mounted
        if os.path.exists(usb_directory):
            file_name = f'{usb_directory}{rtc.now()}'
            video_file = f'{usb_directory}{rtc.now()}.mp4'
        # Save to Pi
        else:
            file_name = f'{directory}{rtc.now()}'
            video_file = f'{directory}{rtc.now()}.mp4'
        
        # Create File    
        file = open(file_name, "w")
        data_imu = [['Timestamp', 'Acceleration (m/s^2)', 'Gyroscope (deg/sec)']]
        data_gps = [['Timestamp', 'Time (ms)', 'Latitude (deg)', 'Longitude (deg)', 'Altitude (m)', 'Velocity (m/s)']]
        
        if not GPIO.input(CAMERA_TOGGLE):	# Camera is ON
            cam = Pi_Camera(camera, video_file)
        
        while toggle_state:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Threading
                f1 = executor.submit(log_imu, t_imu)
                f2 = executor.submit(log_gps, t_gps)
                if not GPIO.input(CAMERA_TOGGLE):
                    cam.record()
                
                imu_res = f1.result()
                gps_res = f2.result()
                
                if imu_res[0]:
                    t_imu = imu_res[1]
                    data_imu.extend([imu_res[2:]])

                if gps_res[0]:
                    t_gps = gps_res[1]
                    data_gps.extend([gps_res[2:]])
            
            # Start button is pressed once more (to terminate)
            if GPIO.input(START_BUTTON):
                toggle_state = False
                GPIO.output(GREEN_LED, GPIO.LOW)    # Turn green LED OFF
                if not GPIO.input(CAMERA_TOGGLE):
                    cam.stop()
                file.write(tabulate(data_imu, headers='firstrow',
                                    tablefmt='fancy_grid', showindex=True))
                file.write('\n')
                file.write(tabulate(data_gps, headers='firstrow',
                                    tablefmt='fancy_grid'))
                file.close()


# Event detection with debounce for start button
GPIO.add_event_detect(START_BUTTON, GPIO.FALLING, callback=start_log,
                      bouncetime=DEBOUNCE_TIME)


# Main loop
try:
    while True:
        if not gps.fix():
            # Blink blue LED
            GPIO.output(BLUE_LED, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(BLUE_LED, GPIO.LOW)
            time.sleep(1)
        else:
            # Turn blue LED OFF
            GPIO.output(BLUE_LED, GPIO.LOW)
            time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()
    bus.close()
