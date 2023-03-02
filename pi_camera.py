from picamera2 import Picamera2, MappedArray
from picamera2.encoders import H264Encoder, Quality
import time

# Set the resolution, framerate, and bitrate
RESOLUTION = (1280, 720)    # 720p
FRAMERATE = (16666, 16666)  # 60 FPS
BITRATE = 5000000   # 5 Mbps


class Pi_Camera:
    
    def __init__(self):
        # Create a PiCamera object and configure it
        self.camera = Picamera2()
        self.encoder = H264Encoder(BITRATE)
        config = self.camera.create_video_configuration(main={"size": RESOLUTION}, 
                                                        controls={"FrameDurationLimits": FRAMERATE})
        self.camera.configure(config)
        time.sleep(0.1)
        

    def start_recording(self, file_name):
        self.camera.start_recording(self.encoder, file_name, Quality.MEDIUM)
        
    
    def stop_recording(self):
        self.camera.stop_recording()
