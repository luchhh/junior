import RPi.GPIO as gpio
import time

def init():
    gpio.setmode(gpio.BCM)
    gpio.setup(17, gpio.OUT) 
    gpio.setup(22, gpio.OUT) 
    gpio.setup(23, gpio.OUT)
    gpio.setup(24, gpio.OUT)
    gpio.setup(12, gpio.OUT)
    gpio.setup(13, gpio.OUT)



def forward(sec, pw=100):
    init()
    pwm17 = gpio.PWM(12,100)
    pwm22 = gpio.PWM(13,100)
    pwm17.start(pw)
    pwm22.start(pw)
    
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(24, True)
    time.sleep(sec)
    gpio.cleanup()

def left_turn(sec, pw=100):
    init()
    pwm17 = gpio.PWM(12,100)
    pwm22 = gpio.PWM(13,100)
    pwm17.start(pw)
    pwm22.start(pw)
    
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(24, False)
    time.sleep(sec)
    gpio.cleanup()
    

def reverse(sec, pw=100):
    init()
    pwm17 = gpio.PWM(12,100)
    pwm22 = gpio.PWM(13,100)
    pwm17.start(pw)
    pwm22.start(pw)
    
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(24, False)
    time.sleep(sec)
    gpio.cleanup()
    
def right_turn(sec, pw=100):
    
    init()
    pwm17 = gpio.PWM(12,100)
    pwm22 = gpio.PWM(13,100)
    pwm17.start(pw)
    pwm22.start(pw)
    
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(24, True)
    time.sleep(sec)
    gpio.cleanup()  