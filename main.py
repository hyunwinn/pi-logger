import time
from datetime import datetime
import os
import concurrent.futures
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

# RTC setup
rtc = DS3231(bus)

# Pi camera setup
camera = Picamera2()

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

# Define sampling intervals
IMU_SAMPLE_INTERVAL = 10
GPS_SAMPLE_INTERVAL = 500


def millis():
    return time.time_ns() // 1000000


def log_imu(data, t_start, t_imu):
    if millis() >= t_imu:
        acc, gyro = imu.run()
        data.append([datetime.now(), t_imu - t_start, acc, gyro])
        return t_imu + IMU_SAMPLE_INTERVAL
    

def log_gps(data, t_start, t_gps):
    if millis() >= t_gps:
        lat, long, alt, vel = gps.run()
        data.append([datetime.now(), t_gps - t_start, lat, long, alt, vel])
        return t_gps + GPS_SAMPLE_INTERVAL
    

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
            file_name = f'{usb_directory}{rtc.now()}'
            video_file = f'{usb_directory}{rtc.now()}.mp4'
        # Save to Pi
        else:
            file_name = f'{directory}{rtc.now()}'
            video_file = f'{directory}{rtc.now()}.mp4'
        
        # Create File    
        file = open(file_name, "w")
        data_imu = [['Timestamp', 'Time (ms)', 'Acceleration (m/s^2)', 'Gyroscope (deg/sec)']]
        data_gps = [['Timestamp', 'Time (ms)', 'Latitude (deg)', 'Longitude (deg)', 'Altitude (m)', 'Velocity (m/s)']]
        
        cam = Pi_Camera(camera, video_file)
        
        while toggle_state:
            with concurrent.futures.ProcessPoolExecutor() as executor:
                f1 = executor.submit(log_imu, t_start, t_imu)
                f2 = executor.submit(log_gps, t_start, t_gps)
                t_imu = f1.result()
                t_gps = f2.result()
            
            cam.record()
            
            # Start button is pressed once more (to terminate)
            if GPIO.input(START_BUTTON):
                toggle_state = False
                GPIO.output(GREEN_LED, GPIO.LOW)    # Turn green LED OFF
                cam.stop()
                file.write(tabulate(data_imu, headers='firstrow',
                                    tablefmt='fancy_grid'))
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
