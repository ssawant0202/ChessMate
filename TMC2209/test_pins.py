from time import sleep
from RPi import GPIO
GPIO.setmode(GPIO.BCM)  

for pin in [2,3,14,15,16,20,21]:
    GPIO.setup(pin, GPIO.OUT) 
    input(f"Connect GPIO {pin}. Press Enter...")
    GPIO.output(pin, GPIO.HIGH)
    sleep(3)
    GPIO.output(pin, GPIO.LOW)
    
GPIO.cleanup()