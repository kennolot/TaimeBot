import machine
import time

# CHANGE THE PORT
led = machine.Pin(13, machine.Pin.OUT)

led.on() 
time.sleep(0.5)  
led.off()  
time.sleep(0.5) 