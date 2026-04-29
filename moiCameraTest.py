import os
os.environ["DISPLAY"] = ":0"

from picamera2 import Picamera2

picam2 = Picamera2()
picam2.start(show_preview=True)

import time
time.sleep(1000)

picam2.stop()