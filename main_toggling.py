import network
import socket
from machine import Pin, ADC, reset
import time
import _thread

# server side log
log = []

# 50% default moisture
user_input_value = 50
# 10 minute default
user_input_value2 = 10

# defaults, user can change these afterwards
SSID = "PlantWateringAuto"
PASSWORD = "12345678"

# default sensor datas to later read periodically
sensor_data = {"moisture": 0, "water_level": "Unknown"}

###
# PIN inits
###
moisture_sensor = ADC(Pin(27))
moisture_sensor.atten(ADC.ATTN_11DB) # 3.3V
# 0 if not enough water supplied
water_level_sensor = Pin(14, Pin.IN)

pump = Pin(15, Pin.OUT)
pump.value(0)  # water pump off by default
# green
led_green = Pin(25, Pin.OUT)
led_green.value(1)
# blue
led_blue = Pin(32, Pin.OUT)
led_blue.value(0)
# red
led_red = Pin(33, Pin.OUT)
led_red.value(0)

# pole kindel, veenduda
button = Pin(12, Pin.IN, Pin.PULL_DOWN)

def reset_esp32(pin):
    print("Button pressed! Resetting ESP32...")
    reset()
    
button.irq(trigger=Pin.IRQ_RISING, handler=reset_esp32)

def update_log(message):
    global log
    # insert new messages at the top
    log.insert(0, message)

def toggle_wifi_off():
    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    time.sleep(0.1)
    
    
def toggle_wifi_on():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=SSID, password=PASSWORD)
    time.sleep(0.1)

def read_sensors():
    global sensor_data
    toggle_wifi_off()
    try:        
        sensor_data["moisture"] = moisture_sensor.read()
        sensor_data["water_level"] = "Full" if water_level_sensor.value() == 1 else "Low"
    finally:
        toggle_wifi_on()

# call this periodically
def update_sensor_data():
    while True:
        read_sensors()
        # sensor read interval, while wifi is off
        time.sleep(30)

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
    global user_input_value, user_input_value2, log  
    # read the sensor values to display on webapp
    # disable wifi since it uses ADC2 like sensors do, causing collision

    moisture_value = sensor_data["moisture"]
    water_level = sensor_data["water_level"]
    moisture_value_percentage = int(100 * (moisture_value/4095))
    
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
            button, input[type="submit"] {{ font-size: 20px; padding: 10px 20px; margin: 10px; }}
            input[type="text"] {{ padding: 10px; font-size: 18px; width: 50px; }}
            .log {{ max-height: 200px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; }}
        </style>
    </head>
    <body>
        <h1>Plant Watering Automation</h1>
        <p><b>Moisture Level:</b> {moisture_value}</p>
        <p><b>Moisture %:</b> {moisture_value_percentage}</p>
        <p><b>Water Level:</b> {water_level}</p>
        
        <p><b>Set moisture thresh:</b> {user_input_value}</p>
        <p><b>Set delay:</b> {user_input_value2}</p>
        
        <form action="/" method="post">
            <label for="input_value">Moisture threshold %:</label>
            <input type="text" id="input_value" name="input_value"><br><br>
            <label for="input_value2">Checking time minutes:</label>
            <input type="text" id="input_value2" name="input_value2"><br><br>
            <input type="submit" value="Submit">
        </form>
        
        <button onclick="sendRequest('start')">Start</button>
        <button onclick="sendRequest('stop')">Stop</button>
        
        <div class="log">
            <h3>Log:</h3>
            <ul>
                {"".join([f"<li>{{msg}}</li>" for msg in log[-5:]])}
            </ul>
        </div>
        
        <script>
            function sendRequest(action) {{
                fetch('/' + action)
                    .then(response => response.text())
                    .then(data => alert(data))
                    .catch(err => console.error(err));
            }}              
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
        
        if "POST" in request:
            try:
                body_start = request.find("\r\n\r\n") + 4
                post_data = request[body_start:]
                print("POST Data:", post_data)

                params = {}
                for param in post_data.split('&'):
                    key, value = param.split('=')
                    params[key] = value

                global user_input_value, user_input_value2
                user_input_value = int(params.get("input_value", 0))
                user_input_value2 = int(params.get("input_value2", 0))
                print(f"Received input_value: {user_input_value}")
                print(f"Received input_value2: {user_input_value2}")

                # compare
                moisture_value = sensor_data["moisture"]
                moisture_value_percentage = int(100 * (moisture_value/4095))
                moisture_threshold = user_input_value
                
                print("comparing moisture w user input")
                if moisture_value_percentage < moisture_threshold:
                    response = "Moisture is below threshold. Activating pump."
                else:
                    response = "Moisture level is sufficient."


            except Exception as e:
                # green LED off, red OFF, blue ON                
                led_blue.value(1)
                led_red.value(0)
                led_green.value(0)
                print("Error parsing POST data:", e)
                response = "Failed to process input value!"
        
        # manual controls
        elif "/start" in request:
            #pump.value(1)
            response = "Pump started!"
        elif "/stop" in request:
            #pump.value(0)
            response = "Pump stopped!"
        else:            
            response = web_page()            
        
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + response)
        conn.close()        

# used with threads
def watering_cycle():
    needs_watering = False
    while True:
        # wait for user inputed time
        if needs_watering == False:            
            time.sleep(user_input_value2 * 60)  #  minutes to seconds

        # read the moisture value again
        moisture_value = sensor_data["moisture"]
        moisture_value_percentage = int(100 * (moisture_value / 4095))

        if moisture_value_percentage < user_input_value:
            needs_watering = True
            log_message = "Moisture below threshold. Activating pump."
            update_log(log_message)
            #pump.value(1)  # turn on the pump
            time.sleep(3)  # keep the pump on for 3 seconds
            #pump.value(0)  # turn off the pump
        else:
            needs_watering = False
            log_message = "Moisture level is sufficient."
            update_log(log_message)

        # 30 seconds before checking again
        time.sleep(30)


try:
    ip_address = start_access_point()
    print(f"Web server running at http://{ip_address}")
    
    # thread to periodicallt update sensors
    _thread.start_new_thread(update_sensor_data, ())
    
    _thread.start_new_thread(watering_cycle, ())
    
    start_web_server()
except Exception as e:
    led_red.value(1)
    led_green.value(0)
    led_blue.value(0)
    print("Error:", e)
    # pump off in case of error
    pump.value(0)
