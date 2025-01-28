import network
import socket
from machine import Pin, ADC
import time


# defaults, user can change these afterwards
SSID = "PlantWateringAuto"
PASSWORD = "12345678"


###
# PIN inits
###
moisture_sensor = ADC(Pin(27))
moisture_sensor.atten(ADC.ATTN_11DB) # 3.3V
# 0 if not enough water supplied
water_level_sensor = Pin(14, Pin.IN)

pump = Pin(15, Pin.OUT)
pump.value(0)  # water pump off by default



# starting our access point, which hosts web app
def start_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=SSID, password=PASSWORD)
    
    print("Starting Access Point...")
    while not ap.active():        
        print("AP is taking some time..")
        time.sleep(1)
          
    return ap.ifconfig()[0]

    
def web_page():        
    # read the sensor values to display on webapp    
    moisture_value = moisture_sensor.read()
    water_level = "Full" if water_level_sensor.value() == 1 else "Low" 
    
    print("####################")
    print("moisture sensor is reading:", moisture_value)                
    print("water level sensor is reading:", water_level)
    print("####################")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Plant Watering Automation</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
            button {{ font-size: 20px; padding: 10px 20px; margin: 10px; }}
        </style>
    </head>
    <body>
        <h1>Plant Watering Automation</h1>
        <p><b>Moisture Level:</b> {moisture_value}</p>
        <p><b>Water Level:</b> {water_level}</p>
        
        <button onclick="sendRequest('start')">Start</button>
        <button onclick="sendRequest('stop')">Stop</button>
        
        <script>
            function sendRequest(action) {{
                fetch('/' + action)
                    .then(response => response.text())
                    .then(data => alert(data))
                    .catch(err => console.error(err));
            }}  
            function updateData() {{
                fetch('/')
                    .then(response => response.text())
                    .then(data => document.body.innerHTML = data)
                    .catch(err => console.error(err));
            }}        
            setInterval(updateData, 5000); // 5 sec    
        </script>
    </body>
    </html>
    """
    return html

def start_web_server():    
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)    

    while True:
        conn, addr = s.accept()
        print("Client connected from", addr)
        request = conn.recv(1024).decode()        
        
        if "/start" in request:
            #pump.value(1)
            response = "Pump started!"
        elif "/stop" in request:
            #pump.value(0)
            response = "Pump stopped!"
        else:            
            response = web_page()            
        
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + response)
        conn.close()

# MAIN
try:
    ip_address = start_access_point()
    print(f"Web server running at http://{ip_address}")        
    start_web_server()
except Exception as e:
    print("Error:", e)
    # pump off in case of error
    pump.value(0)
