import time
import subprocess
import os
import RPi.GPIO as GPIO

device = "/dev/sda1"

# set up GPIO pins
EJECT_BUTTON = 16
YELLOW_LED = 25
GPIO.setmode(GPIO.BCM)
GPIO.setup(EJECT_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(YELLOW_LED, GPIO.OUT)

# Define debounce time of eject button
DEBOUNCE_TIME = 200
toggle_state = False


# Define function to blink yellow led
def _blink():
    GPIO.output(YELLOW_LED, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(YELLOW_LED, GPIO.LOW)
    time.sleep(0.5)
    
    
# Define function to eject USB drive
def eject_device(channel):
    global toggle_state
    
    if not toggle_state and not GPIO.input(EJECT_BUTTON):
        # Device is mounted
        if os.path.exists(device):
            toggle_state = True
            subprocess.call(["sudo", "umount", device])
            subprocess.call(["sudo", "eject", device])
            _blink()
            toggle_state = False
        # Device is not mounted
        else:
            toggle_state = True
            _blink()
            _blink()
            toggle_state = False
            

# Event detection with debounce for eject button
GPIO.add_event_detect(EJECT_BUTTON, GPIO.FALLING, callback=eject_device,
                      bouncetime=DEBOUNCE_TIME)                                                                                                                            


# Main loop
try:
    while True:
        pass

except KeyboardInterrupt:
    GPIO.cleanup()
