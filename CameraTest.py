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

frame = cam.capture_array()
cv2.circle(frame, (100,100), 10, (255,0,255), -1)
cv2.imwrite('test2.jpg', frame)

cam.stop()