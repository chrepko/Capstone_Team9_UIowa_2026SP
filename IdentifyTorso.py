from picamera2 import Picamera2, MappedArray, Preview
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
import cv2
import time

cam = Picamera2()
face = cv2.CascadeClassifier("/home/team9/Capstone/opencv-4.12.0/data/haarcascades/haarcascade_profileface.xml")
reye = cv2.CascadeClassifier("/home/team9/Capstone/opencv-4.12.0/data/haarcascades/haarcascade_righteye_2splits.xml")
leye = cv2.CascadeClassifier("/home/team9/Capstone/opencv-4.12.0/data/haarcascades/haarcascade_lefteye_2splits.xml")

def Identify(request):
    print("frame")
    with MappedArray(request, "main") as m:
        faces = face.detectMultiScale(m.array)
        faceFound = False
        for (x,y,w,h) in faces:
            cv2.rectangle(m.array, (x,y), (x+w, y+h), (255, 0, 0), 2)
            print("person detected")
        reyes = reye.detectMultiScale(m.array)
        for (ex,ey,ew,eh) in reyes:
            cv2.rectangle(m.array, (ex,ey),(ex+ew,ey+eh), (0,0,255), 2)
        leyes = leye.detectMultiScale(m.array)
        for (ex,ey,ew,eh) in leyes:
            cv2.rectangle(m.array, (ex,ey),(ex+ew,ey+eh), (0,255,0), 2)
        
cam.pre_callback = Identify
cam.start_preview(Preview.QTGL)
cam.start()

time.sleep(20)

cam.stop()