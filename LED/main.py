import machine
import time

# CHANGE THE PORT
led1 = machine.Pin(13, machine.Pin.OUT)

# CHANGE THE PORT
led2 = machine.Pin(13, machine.Pin.OUT)

# CHANGE THE PORT
led3 = machine.Pin(13, machine.Pin.OUT)

sleeptime = 1

# Led1
led1.on() 
time.sleep(sleeptime)  
led1.off()  
time.sleep(sleeptime) 

# Led2
led2.on() 
time.sleep(sleeptime)  
led2.off()  
time.sleep(sleeptime) 

# Led3
led3.on() 
time.sleep(sleeptime)  
led3.off()  
time.sleep(sleeptime) 