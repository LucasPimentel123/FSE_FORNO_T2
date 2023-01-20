import RPi.GPIO as GPIO

class Forno:
    def __init__(self):
        resistor_port = 23
        fan_port = 24
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(resistor_port, GPIO.OUT)
        GPIO.setup(fan_port, GPIO.OUT)

        
        self.resistor = GPIO.PWM(resistor_port, 1000)
        self.resistor.start(0)

        self.fan = GPIO.PWM(fan_port, 1000)
        self.fan.start(0)
    
    def heat(self, pid):
        self.resistor.ChangeDutyCycle(pid)

    def cool_down(self, pid):
        self.fan.ChangeDutyCycle(pid) 