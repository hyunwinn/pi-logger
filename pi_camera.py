from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
import datetime
import time

# Set the resolution and framerate
RESOLUTION = (1280, 720)
FRAMERATE = 60

# Create a PiCamera object and configure it
camera = Picamera2()
camera.sensor_mode = 4
camera.resolution = RESOLUTION
camera.framerate = FRAMERATE

# File directory
directory = "/home/hsc35/data/"

# Create output file
video = directory + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + '.h264'

# Recording
camera.start_recording(video)
time.sleep(5)
camera.stop_recording()
camera.close()