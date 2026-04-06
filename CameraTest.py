from picamera2 import Picamera2, MappedArray
import cv2
import time

cam = Picamera2()
def saveImage(request):
	with MappedArray(request, "main") as m:
		cv2.imwrite("test.jpg", m.array)
		print("Saved image...")
		
cam.post_callback = saveImage
cam.start()

cam.stop()
