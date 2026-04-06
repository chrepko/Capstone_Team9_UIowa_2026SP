import RPi.GPIO as GPIO
import time
import sys 
from picamera2 import Picamera2, MappedArray, Preview
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
import cv2
import time


class MotorInterface:
    currentValues = [0, 0]
    currentdirection = 0
    def TestDirection(self, changedChannel):
        # Check if the two channels are matching
        if(self.currentValues[0] == self.currentValues[1]):
            # If the last change was to channel 1, we're going down
            if(changedChannel == 1):
                self.currentdirection = -1
            # Otherwise, we're going up.
            else:
                self.currentdirection = 1
        else:
            # If the last change was to channel 1, we're going up.
            if(changedChannel == 1):
                self.currentdirection = 1
            # Otherwise, we're going down.
            else:
                self.currentdirection = -1

    def switchChannel1(self, channel):
        state = GPIO.input(channel)
        if(state):
            self.channel1Rise()
        else:
            self.channel1Fall()
            
    def switchChannel2(self, channel):
        state = GPIO.input(channel)
        if(state):
            self.channel2Rise()
        else:
            self.channel2Fall()
        
        
    def channel1Rise(self):
        self.currentValues[0] = 1
        self.TestDirection(1)
        
    def channel2Rise(self):
        self.currentValues[1] = 1
        self.TestDirection(2)
    
    def channel1Fall(self):
        self.currentValues[0] = 0
        self.TestDirection(1)
    
    def channel2Fall(self):
        self.currentValues[1] = 0
        self.TestDirection(2)

    def printDirection(self):
        if(self.currentdirection > 0):
            print("Going up")
        elif(self.currentdirection < 0):
            print("Going down")
        else:
            print("Not Moving")



class DeskInterface:
    SERVO_CONTROL_GPIO = 23
    motorL = MotorInterface()
    motorR = MotorInterface()
    manualMode = True
    movementDirection = 0; # 1 -> up, 0 -> still, -1 -> down
    servoPWM = 0
    locked = False
    safetyTripped = False
    angle = -20
    lock_try = 0
    lock_miss = 0
    face_lock = [0,0,0,0]
    leye_lock = [0,0,0,0]
    reye_lock = [0,0,0,0]
    directionUp = True;
    def button_trigger(self, channel):
        state = GPIO.input(channel)
        print("Trigger on channel " + str(channel))
        if(not state):
            self.button_pressed(channel)
        else:
            self.button_released(channel)
            
    def button_pressed(self, channel):
        print("manual mode: " + str(self.manualMode))
        print("Movement direction: " + str(self.movementDirection))
        if(channel == UP_GPIO and self.manualMode and self.movementDirection == 0):
            self.startMoveUp()
        elif(channel == DOWN_GPIO and self.manualMode and self.movementDirection == 0):
            self.startMoveDown()
        elif(channel == MODE_GPIO):
            self.manualMode = not self.manualMode
            if(not self.manualMode):
                self.stopMoving()
        elif(channel == LOCK_GPIO):
            self.locked = not self.locked
        elif(channel == SAFE_GPIO):
            self.safetyTripped = True
                
    def button_released(self, channel):
        if(channel == UP_GPIO and self.manualMode and self.movementDirection == 1):
            self.stopMoving()
        elif(channel == DOWN_GPIO and self.manualMode and self.movementDirection == -1):
            self.stopMoving()
        elif(channel == MODE_GPIO):
            pass
        elif(channel == SAFE_GPIO):
            self.safetyTripped = False
            
    def startMoveUp(self):
        if(not self.locked):
            self.movementDirection = 1
            if(len(sys.argv) == 1):
                GPIO.output(CONTROL_UP_GPIO, True)
                GPIO.output(CONTROL_DOWN_GPIO, False)
            else: 
                GPIO.output(CONTROL_UP_GPIO, False)
                GPIO.output(CONTROL_DOWN_GPIO, True)
    def startMoveDown(self):
        if(not (self.locked or self.safetyTripped)):
            self.movementDirection = -1
            if(len(sys.argv) == 1):
                GPIO.output(CONTROL_UP_GPIO, False)
                GPIO.output(CONTROL_DOWN_GPIO, True)
            else:
                GPIO.output(CONTROL_UP_GPIO, True)
                GPIO.output(CONTROL_DOWN_GPIO, False)
        
    def stopMoving(self):
        self.movementDirection = 0
        if(len(sys.argv) == 1):
            GPIO.output(CONTROL_UP_GPIO, False)
            GPIO.output(CONTROL_DOWN_GPIO, False)
        else:
            GPIO.output(CONTROL_UP_GPIO, True)
            GPIO.output(CONTROL_DOWN_GPIO, True)
    # Position is in degrees, (-90, 90)        
    def commandServo(self, position):
        position = min(max(position, -90), 90)
        position += 90
        positionMultiplier = 1000/180
        position *= positionMultiplier
        position = (position/1000) + 1
        position = max(min(position, 2), 1)/1000
        print("Pulse length: " + str(position) + " s") 
        for i in range(100):
            GPIO.output(self.SERVO_CONTROL_GPIO, True)
            now = time.time()
            while(time.time() - now < position):
                pass
            GPIO.output(self.SERVO_CONTROL_GPIO, False)
            while(time.time() - now < 0.02):
                pass
    def Identify(self, request):
        print("frame")
        with MappedArray(request, "main") as m:
            faces = face.detectMultiScale(m.array)
            faceFound = False
            for (x,y,w,h) in faces:
                cv2.rectangle(m.array, (x,y), (x+w, y+h), (255, 0, 0), 2)
                print("person detected")
                faceFound = True
                self.face_lock = [x,y,w,h]
            reyes = reye.detectMultiScale(m.array)
            for (ex,ey,ew,eh) in reyes:
                cv2.rectangle(m.array, (ex,ey),(ex+ew,ey+eh), (0,0,255), 2)
                faceFound = True
                self.reye_lock = [ex,ey,ew,eh]
            leyes = leye.detectMultiScale(m.array)
            for (ex,ey,ew,eh) in leyes:
                cv2.rectangle(m.array, (ex,ey),(ex+ew,ey+eh), (0,255,0), 2)
                faceFound = True
                self.reye_lock = [ex,ey,ew,eh]
            if(not faceFound):
                self.lock_miss += 1
            if(self.lock_miss > 5):
                if(self.directionUp):
                    self.angle -= 20
                    if(self.angle <= -80):
                        self.angle = -80
                        self.direction = not self.directionUp
                    self.commandServo(self.angle)
                else:
                    self.angle += 20
                    if(self.angle >= 80):
                        self.angle = 80
                        self.direction = not self.directionUp
                    self.commandServo(self.angle)
                self.lock_miss = 0
                


UP_GPIO = 1
DOWN_GPIO = 17
MODE_GPIO = 27
LOCK_GPIO = 26
SAFE_GPIO = 19
MOTOR_1_SENSOR_1_GPIO = 10
MOTOR_1_SENSOR_2_GPIO = 11
MOTOR_2_SENSOR_1_GPIO = 12
MOTOR_2_SENSOR_2_GPIO = 13

CONTROL_UP_GPIO = 5
CONTROL_DOWN_GPIO = 6

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    interface = DeskInterface()
    GPIO.setup(UP_GPIO, GPIO.IN)
    GPIO.setup(DOWN_GPIO, GPIO.IN)
    GPIO.setup(MODE_GPIO, GPIO.IN)
    GPIO.setup(LOCK_GPIO, GPIO.IN)
    GPIO.setup(SAFE_GPIO, GPIO.IN)
    GPIO.setup(MOTOR_1_SENSOR_1_GPIO, GPIO.IN)
    GPIO.setup(MOTOR_1_SENSOR_2_GPIO, GPIO.IN)
    GPIO.setup(MOTOR_2_SENSOR_1_GPIO, GPIO.IN)
    GPIO.setup(MOTOR_2_SENSOR_2_GPIO, GPIO.IN)
    GPIO.setup(CONTROL_UP_GPIO, GPIO.OUT)
    GPIO.setup(CONTROL_DOWN_GPIO, GPIO.OUT)
    GPIO.setup(interface.SERVO_CONTROL_GPIO, GPIO.OUT)
    
    GPIO.add_event_detect(UP_GPIO, GPIO.BOTH, 
        callback=interface.button_trigger, bouncetime=10)
    
    GPIO.add_event_detect(DOWN_GPIO, GPIO.BOTH, 
        callback=interface.button_trigger, bouncetime=10)
    
    GPIO.add_event_detect(MODE_GPIO, GPIO.BOTH, 
        callback=interface.button_trigger, bouncetime=10)
    GPIO.add_event_detect(LOCK_GPIO, GPIO.BOTH, 
        callback=interface.button_trigger, bouncetime=10)
    GPIO.add_event_detect(SAFE_GPIO, GPIO.BOTH, 
        callback=interface.button_trigger, bouncetime=10)
        
    GPIO.add_event_detect(MOTOR_1_SENSOR_1_GPIO, GPIO.BOTH, 
        callback=interface.motorL.switchChannel1, bouncetime=10)
    GPIO.add_event_detect(MOTOR_1_SENSOR_2_GPIO, GPIO.BOTH, 
        callback=interface.motorL.switchChannel2, bouncetime=10)
        
    GPIO.add_event_detect(MOTOR_2_SENSOR_1_GPIO, GPIO.BOTH, 
        callback=interface.motorR.switchChannel1, bouncetime=10)
    GPIO.add_event_detect(MOTOR_2_SENSOR_2_GPIO, GPIO.BOTH, 
        callback=interface.motorR.switchChannel2, bouncetime=10)
    
    interface.stopMoving();
    interface.commandServo(interface.angle)
    
    cam = Picamera2()
    face = cv2.CascadeClassifier("/home/team9/Capstone/opencv-4.12.0/data/haarcascades/haarcascade_profileface.xml")
    reye = cv2.CascadeClassifier("/home/team9/Capstone/opencv-4.12.0/data/haarcascades/haarcascade_righteye_2splits.xml")
    leye = cv2.CascadeClassifier("/home/team9/Capstone/opencv-4.12.0/data/haarcascades/haarcascade_lefteye_2splits.xml")


            
    cam.pre_callback = interface.Identify
    try:
        cam.start_preview(Preview.QTGL)
    except Exception:
        pass
    cam.start()
    while(True):
        time.sleep(1)
        
        
