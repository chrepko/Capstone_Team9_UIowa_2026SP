import RPi.GPIO as GPIO
import time
import sys 

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
    motorL = MotorInterface()
    motorR = MotorInterface()
    manualMode = True
    movementDirection = 0; # 1 -> up, 0 -> still, -1 -> down
    
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
                
    def button_released(self, channel):
        if(channel == UP_GPIO and self.manualMode and self.movementDirection == 1):
            self.stopMoving()
        elif(channel == DOWN_GPIO and self.manualMode and self.movementDirection == -1):
            self.stopMoving()
        elif(channel == MODE_GPIO):
            pass
            
    def startMoveUp(self):
        self.movementDirection = 1
        if(len(sys.argv) == 1):
            GPIO.output(CONTROL_UP_GPIO, True)
            GPIO.output(CONTROL_DOWN_GPIO, False)
        else: 
            GPIO.output(CONTROL_UP_GPIO, False)
            GPIO.output(CONTROL_DOWN_GPIO, True)
    def startMoveDown(self):
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
        

UP_GPIO = 1
DOWN_GPIO = 17
MODE_GPIO = 27
MOTOR_1_SENSOR_1_GPIO = 10
MOTOR_1_SENSOR_2_GPIO = 11
MOTOR_2_SENSOR_1_GPIO = 12
MOTOR_2_SENSOR_2_GPIO = 13

CONTROL_UP_GPIO = 5
CONTROL_DOWN_GPIO = 6

if __name__ == "__main__":
    interface = DeskInterface()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(UP_GPIO, GPIO.IN)
    GPIO.setup(DOWN_GPIO, GPIO.IN)
    GPIO.setup(MODE_GPIO, GPIO.IN)
    GPIO.setup(MOTOR_1_SENSOR_1_GPIO, GPIO.IN)
    GPIO.setup(MOTOR_1_SENSOR_2_GPIO, GPIO.IN)
    GPIO.setup(MOTOR_2_SENSOR_1_GPIO, GPIO.IN)
    GPIO.setup(MOTOR_2_SENSOR_2_GPIO, GPIO.IN)
    GPIO.setup(CONTROL_UP_GPIO, GPIO.OUT)
    GPIO.setup(CONTROL_DOWN_GPIO, GPIO.OUT)
    
    GPIO.add_event_detect(UP_GPIO, GPIO.BOTH, 
        callback=interface.button_trigger, bouncetime=10)
    
    GPIO.add_event_detect(DOWN_GPIO, GPIO.BOTH, 
        callback=interface.button_trigger, bouncetime=10)
    
    GPIO.add_event_detect(MODE_GPIO, GPIO.BOTH, 
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
    while(True):
        time.sleep(1000)
        