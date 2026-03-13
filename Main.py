import RPi.GPIO as GPIO

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

    def switchChannel1(self):
        self.currentValues[0] += 1
        if(self.currentValues[0] > 1): 
            self.currentValues[0] = 0
        self.TestDirection(1)
            
    def switchChannel2(self):
        self.currentValues[1] += 1
        if(self.currentValues[1] > 1): 
            self.currentValues[1] = 0
        self.TestDirection(2)
        
    def channel1Rise(self):
        seld.currentValues[0] = 1
        self.TestDirection(1)
        
    def channel2Rise(self):
        seld.currentValues[1] = 1
        self.TestDirection(2)
    
    def channel1Fall(self):
        seld.currentValues[0] = 0
        self.TestDirection(1)
    
    def channel2Fall(self):
        seld.currentValues[1] = 0
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
    def button_pressed(self, channel):
        if(channel == UP_GPIO and self.manualMode and self.movementDirection == 0):
            self.startMoveUp()
        elif(channel == DOWN_GPIO and self.manualMode and self.movementDirection == 0):
            self.startMoveDown()
        elif(channel == MODE_GPIO):
            self.manualMode = not self.manualMode
            if(not self.manualMode):
                self.stopMoving()
                
    def button_released(self, channel):
        if(channel == UP_GPIO and self.manualMode):
            self.stopMoving()
        elif(channel == DOWN_GPIO and self.manualMode):
            self.stopMoving()
        elif(channel == MODE_GPIO):
            pass
            
    def startMoveUp(self):
        selfmovementDirection = 1
        GPIO.output(CONTROL_UP_GPIO, True)
        GPIO.output(CONTROL_DOWN_GPIO, False)
        
    def startMoveDown(self):
        self.movementDirection = -1
        GPIO.output(CONTROL_UP_GPIO, False)
        GPIO.output(CONTROL_DOWN_GPIO, True)
        
    def stopMoving(self):
        self.movementDirection = 0
        GPIO.output(CONTROL_UP_GPIO, False)
        GPIO.output(CONTROL_DOWN_GPIO, False)
        

UP_GPIO = 1
DOWN_GPIO = 2
MODE_GPIO = 3
MOTOR_1_SENSOR_1_GPIO = 4
MOTOR_1_SENSOR_2_GPIO = 5
MOTOR_2_SENSOR_1_GPIO = 6
MOTOR_2_SENSOR_2_GPIO = 7

CONTROL_UP_GPIO = 8
CONTROL_DOWN_GPIO = 9

if __name__ == "__main__":
    interface = DeskInterface()
    GPIO.setmode(GPIO.BCM)
    GPIO.add_event_detect(UP_GPIO, GPIO.FALLING, 
        callback=interface.button_released, bouncetime=10)
    GPIO.add_event_detect(UP_GPIO, GPIO.RISING, 
        callback=interface.button_pressed, bouncetime=10)
    
    GPIO.add_event_detect(DOWN_GPIO, GPIO.FALLING, 
        callback=interface.button_released, bouncetime=10)
    GPIO.add_event_detect(DOWN_GPIO, GPIO.RISING, 
        callback=interface.button_pressed, bouncetime=10)
    
    GPIO.add_event_detect(MODE_GPIO, GPIO.FALLING, 
        callback=interface.button_released, bouncetime=10)
    GPIO.add_event_detect(MODE_GPIO, GPIO.RISING, 
        callback=interface.button_pressed, bouncetime=10)
        
    GPIO.add_event_detect(MOTOR_1_SENSOR_1_GPIO, GPIO.FALLING, 
        callback=interface.motorL.channel1Fall, bouncetime=10)
    GPIO.add_event_detect(MOTOR_1_SENSOR_1_GPIO, GPIO.RISING, 
        callback=interface.motorL.channel1Rise, bouncetime=10)
    GPIO.add_event_detect(MOTOR_1_SENSOR_2_GPIO, GPIO.FALLING, 
        callback=interface.motorL.channel2Fall, bouncetime=10)
    GPIO.add_event_detect(MOTOR_1_SENSOR_2_GPIO, GPIO.RISING, 
        callback=interface.motorL.channel2Rise, bouncetime=10)
        
    GPIO.add_event_detect(MOTOR_2_SENSOR_1_GPIO, GPIO.FALLING, 
        callback=interface.motorR.channel1Fall, bouncetime=10)
    GPIO.add_event_detect(MOTOR_2_SENSOR_1_GPIO, GPIO.RISING, 
        callback=interface.motorR.channel1Rise, bouncetime=10)
    GPIO.add_event_detect(MOTOR_2_SENSOR_2_GPIO, GPIO.FALLING, 
        callback=interface.motorR.channel2Fall, bouncetime=10)
    GPIO.add_event_detect(MOTOR_2_SENSOR_2_GPIO, GPIO.RISING, 
        callback=interface.motorR.channel2Rise, bouncetime=10
    interface.motorL.printDirection()
    
    for i in range(10):
        interface.switchChannel1()
        interface.motorL.printDirection()
        interface.motorL.switchChannel2()
        interface.motorL.printDirection()
    for i in range(10):
        interface.motorL.switchChannel2()
        interface.motorL.printDirection()
        interface.motorL.switchChannel1()
        interface.motorL.printDirection()
        