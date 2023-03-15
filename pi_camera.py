from libcamera import Transform
import cv2
import time

# Set the resolution, framerate, and bitrate
RESOLUTION = (1280, 720)    # 720p
FRAMERATE = (33333, 33333)  # 30 FPS


class Pi_Camera(object):
    
    def __init__(self, camera, file_name):
        # Create a PiCamera object and configure it
        self.camera = camera
        video_config = self.camera.create_video_configuration(main={"format": 'RGB888', "size": RESOLUTION},
                                                              transform=Transform(vflip=1),	# Flip the video vertically
                                                              controls={"FrameDurationLimits": FRAMERATE})
        self.camera.configure(video_config)
        self.camera.start()
        self.video = cv2.VideoWriter(file_name, cv2.VideoWriter_fourcc(*'mp4v'), 30, RESOLUTION)
        

    def record(self):
        frame = self.camera.capture_array()
        self.video.write(frame)
        
    
    def stop(self):
        self.camera.stop()
        self.video.release()
