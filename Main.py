import RPi.GPIO as GPIO
import time
import sys 
from picamera2 import Picamera2, MappedArray, Preview
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
from libcamera import controls
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

# Quick and dirty vector subtract
def subtract(a, b):
    return [c-d for c,d in zip(a,b)]

def labs(a):
    return [abs(x) for x in a]
    
def list_mult_scalar(l, s):
    return [a*s for a in l]
    
class DeskInterface:
    SERVO_CONTROL_GPIO = 23
    motorL = MotorInterface()
    motorR = MotorInterface()
    manualMode = False
    movementDirection = 0; # 1 -> up, 0 -> still, -1 -> down
    servoPWM = 0
    locked = False
    safetyTripped = False
    angle = 0
    seatedAngle = -10
    seatedToStandAngle = -70
    standToSeatedAngle = 60
    lock_try = 0
    lock_miss = 0
    face_lock = [0,0,0,0]
    leye_lock = [0,0,0,0]
    reye_lock = [0,0,0,0]
    face_locked = False
    directionUp = True;
    setPreset = False
    def button_trigger(self, channel):
        state = GPIO.input(channel)
        print("Trigger on channel " + str(channel))
        if(not state):
            self.button_pressed(channel)
        else:
            self.button_released(channel)
        self.setPresetState()
        
    def setPresetState(self):
        if(self.manualMode):
            GPIO.output(PRESET_EN_GPIO, True)
        else:
            GPIO.output(PRESET_EN_GPIO, False)
            
            
    def button_pressed(self, channel):
        print("Press on " + str(channel))
        if(channel == UP_GPIO and self.manualMode and self.movementDirection == 0):
            self.startMoveUp()
        elif(channel == DOWN_GPIO and self.manualMode and self.movementDirection == 0):
            self.startMoveDown()
        elif(channel == MODE_GPIO):
            pressed = time.time()
            now = pressed
            while(now - pressed < 1 and not GPIO.input(channel)):
                now = time.time()
            if(now - pressed >= 1):
                print("Enabling Set Line")
                GPIO.output(SET_GPIO, True);
                self.setPreset = True
        elif(channel == LOCK_GPIO):
            self.locked = not self.locked
        elif(channel == SAFE_GPIO):
            self.safetyTripped = True
                
    def button_released(self, channel):
        print("Release on " + str(channel))
        if(channel == UP_GPIO and self.manualMode and self.movementDirection == 1):
            self.stopMoving()
        elif(channel == DOWN_GPIO and self.manualMode and self.movementDirection == -1):
            self.stopMoving()
        elif(channel == MODE_GPIO):
            if(not self.setPreset):
                print("Toggling mode.")
                self.manualMode = not self.manualMode
                if(not self.manualMode):
                    self.stopMoving()
            self.setPreset = False
            GPIO.output(SET_GPIO, False);
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
        self.angle = position;
        position += 90
        positionMultiplier = 1000/180
        position *= positionMultiplier
        position = (position/1000) + 1
        position = max(min(position, 2), 1)/1000
        for i in range(100):
            GPIO.output(self.SERVO_CONTROL_GPIO, True)
            now = time.time()
            while(time.time() - now < position):
                pass
            GPIO.output(self.SERVO_CONTROL_GPIO, False)
            while(time.time() - now < 0.02):
                pass
    def Identify(self, request):
        if(not self.manualMode):
            with MappedArray(request, "main") as m:
                faces = face.detectMultiScale(m.array)
                faceFound = False
                face_lock = [0,0,0,0]
                reye_lock = [0,0,0,0]
                leye_lock = [0,0,0,0]
                for (x,y,w,h) in faces:
                    cv2.rectangle(m.array, (x,y), (x+w, y+h), (255, 0, 0), 2)
                    print("person detected")
                    faceFound = True
                    face_lock = [x,y,w,h]
                reyes = reye.detectMultiScale(m.array)
                for (ex,ey,ew,eh) in reyes:
                    cv2.rectangle(m.array, (ex,ey),(ex+ew,ey+eh), (0,0,255), 2)
                    faceFound = True
                    reye_lock = [ex,ey,ew,eh]
                leyes = leye.detectMultiScale(m.array)
                for (ex,ey,ew,eh) in leyes:
                    cv2.rectangle(m.array, (ex,ey),(ex+ew,ey+eh), (0,255,0), 2)
                    faceFound = True
                    leye_lock = [ex,ey,ew,eh]
                if(not faceFound):
                    self.lock_miss += 1
                    self.lock_try = 0
                    self.face_locked = False
                else:
                    foundOne = False
                    if(labs(subtract(self.face_lock, face_lock)) <= list_mult_scalar(self.face_lock, 0.1) and face_lock != [0,0,0,0]):
                        self.lock_miss = 0
                        print("Stable face")
                        foundOne = True
                        self.lock_try += 1
                        self.face_lock = face_lock
                    elif(self.lock_miss > 2):
                        self.face_lock = [0,0,0,0]
                    if(labs(subtract(self.leye_lock, leye_lock)) <= list_mult_scalar(self.leye_lock, 0.1) and leye_lock != [0,0,0,0]):
                        self.lock_miss = 0
                        print("Stable leye")
                        foundOne = True
                        self.leye_lock = leye_lock
                    elif(self.lock_miss > 2):
                        self.leye_lock = [0,0,0,0]
                    if(labs(subtract(self.reye_lock, reye_lock)) <= list_mult_scalar(self.reye_lock, 0.1) and reye_lock != [0,0,0,0]):
                        self.lock_miss = 0
                        print("Stable reye")
                        foundOne = True
                        self.reye_lock = reye_lock
                    elif(self.lock_miss > 2):
                        self.reye_lock = [0,0,0,0]
                    
                    if(face_lock == [0,0,0,0] or self.face_lock == [0,0,0,0] and face_lock != [0,0,0,0]):
                        self.face_lock = face_lock
                    if(leye_lock == [0,0,0,0] or self.leye_lock == [0,0,0,0] and leye_lock != [0,0,0,0]):
                        self.leye_lock = leye_lock
                    if(reye_lock == [0,0,0,0] or self.reye_lock == [0,0,0,0] and reye_lock != [0,0,0,0]):
                        self.reye_lock = reye_lock
                        
                    if(not foundOne):
                        self.lock_miss += 1
                    else:
                        self.lock_try += 1
                if(self.lock_miss > 20):
                    if(self.directionUp):
                        if(self.angle == self.seatedAngle):
                            self.commandServo(self.seatedToStandAngle)
                            self.directionUp = not self.directionUp
                        else:
                            self.commandServo(self.seatedAngle)
                    else:
                        print("Go Down")
                        if(self.angle == self.seatedToStandAngle):
                            self.commandServo(self.seatedAngle)
                        else:
                            self.commandServo(self.standToSeatedAngle)
                            self.directionUp = not self.directionUp
                    self.lock_miss = 0
                elif(self.lock_miss > 5):
                        self.stopMoving()
                if(self.lock_try > 4):
                    self.face_locked = True
                if(self.face_locked):
                    print("Hooray, we have a lock")
                    print(self.face_lock)
                    print(self.reye_lock)
                    print(self.leye_lock)
                    if(self.angle == self.seatedAngle):
                        print("Height discriminator: " + str(self.reye_lock[1]))
                        if(self.reye_lock[1] > 250):
                            print("Go Down")
                            self.startMoveDown()
                        elif(self.reye_lock[1] < 100):
                            print("Go Up")
                            self.startMoveUp()
                        else:
                            print("Don't move")
                            self.stopMoving()
                    elif(self.angle == self.seatedToStandAngle):
                        print("Go to standing")
                        self.startMoveUp()
                    elif(self.angle == self.standToSeatedAngle):
                        print("Go to sit")
                        self.startMoveDown()
                    else:
                        print("Stop moving")
                        self.stopMoving()
                


UP_GPIO = 1
DOWN_GPIO = 17
MODE_GPIO = 27
LOCK_GPIO = 26
SAFE_GPIO = 19
SET_GPIO = 24
PRESET_EN_GPIO = 25
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
    GPIO.setup(SET_GPIO, GPIO.OUT)
    GPIO.setup(PRESET_EN_GPIO, GPIO.OUT)
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
    interface.commandServo(interface.seatedAngle)
    
    cam = Picamera2()
    face = cv2.CascadeClassifier("/home/team9/Capstone/opencv-4.12.0/data/haarcascades/haarcascade_profileface.xml")
    reye = cv2.CascadeClassifier("/home/team9/Capstone/opencv-4.12.0/data/haarcascades/haarcascade_righteye_2splits.xml")
    leye = cv2.CascadeClassifier("/home/team9/Capstone/opencv-4.12.0/data/haarcascades/haarcascade_lefteye_2splits.xml")


    cam.set_controls({"AeEnable": False})
    cam.pre_callback = interface.Identify
    cam.start_preview(Preview.QTGL) # QTGL if running on monitor
    cam.start()
    while(True):
        time.sleep(1)
        
        
