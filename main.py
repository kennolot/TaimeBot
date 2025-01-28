#######
# 
#   Main applitaction
#
#   Possible updates:
#   1) static web address
#
#######

import network
import socket
import time
from machine import Pin, ADC

wifi_credentials = {"ssid": None, "password": None}

# ###
# PINS DEFINITION
# ##

# REPLACE PIN
pump = Pin(2, Pin.OUT)
# pump off by default
pump.value(0)

# REPLACE
water_level_sensor = Pin(4, Pin.IN)

# !!!!!!
# REPLACE - see on kahtlane
moisture_sensor = ADC(Pin(36))
moisture_sensor.atten(ADC.ATTN_11DB)


# initial setup in AP mode
def start_ap_mode():    
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    # will be provided to users with manual, default credentials.
    ap.config(essid="PlantWateringAuto", authmode=network.AUTH_WPA_WPA2_PSK,
              password="") # REPLACE 
    print("AP Mode Started. Connect to Wi-Fi")
    print("Default configuration page http://192.168.4.1")
    return ap

# after setup we get to the actual web app
# source: https://docs.micropython.org/en/latest/esp8266/tutorial/network_basics.html
def start_sta_mode(ssid, password):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.connect(ssid, password)
    
    print("Connecting to Wi-Fi...")
    timeout = 10
    while not sta.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1

    if sta.isconnected():
        print("Connected to Wi-Fi:", sta.ifconfig())
        return sta
    else:
        print("Failed to connect to Wi-Fi.")
        return None
    
# config page 
def serve_ap_page():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print("Listening for connections on 192.168.4.1...")

    while True:
        conn, addr = s.accept()
        print("Client connected from", addr)
        request = conn.recv(1024).decode()
        print("Request:", request)
        
        if "POST /" in request:
            try:
                body = request.split("\r\n\r\n")[1]
                params = {kv.split('=')[0]: kv.split('=')[1] for kv in body.split('&')}
                ssid = params.get("ssid", "").replace("+", " ")
                password = params.get("password", "").replace("+", " ")
                
                # save credentials
                wifi_credentials["ssid"] = ssid
                wifi_credentials["password"] = password
                print("Received Wi-Fi credentials:", ssid, password)

                # respond with success page
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                response += "<html><body><h1>Configuration Saved!</h1><p>Restarting...</p></body></html>"
                conn.send(response)
                conn.close()
                
                # restart sta mode
                time.sleep(2)
                return
            except Exception as e:
                print("Error parsing request:", e)

        # serve the configuration page
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Wi-Fi Setup</title></head>
        <body>
            <h1>Configure Wi-Fi</h1>
            <form method="POST" action="/">
                <label for="ssid">Wi-Fi SSID:</label><br>
                <input type="text" id="ssid" name="ssid" required><br><br>
                <label for="password">Wi-Fi Password:</label><br>
                <input type="password" id="password" name="password" required><br><br>
                <button type="submit">Save</button>
            </form>
        </body>
        </html>
        """
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html
        conn.send(response)
        conn.close()

def start_main_web_server(sta):
    """Start the main web server in STA mode."""
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print("Web server running at http://", sta.ifconfig()[0])

    while True:
        conn, addr = s.accept()
        print("Client connected from", addr)
        request = conn.recv(1024).decode()
        print("Request:", request)

        # Handle requests for start/stop
        if "/start" in request:
            pump.value(1)
            response = "Pump started!"
        elif "/stop" in request:
            pump.value(0)
            response = "Pump stopped!"
        else:
            # Serve the main page
            moisture_value = moisture_sensor.read()
            water_level = "Full" if water_level_sensor.value() == 1 else "Low"
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Plant Watering System</title></head>
            <body>
                <h1>Plant Watering System</h1>
                <p><b>Moisture Level:</b> {moisture_value} / 4096</p>
                <p><b>Water Level:</b> {water_level}</p>
                <button onclick="location.href='/start'">Start</button>
                <button onclick="location.href='/stop'">Stop</button>
            </body>
            </html>
            """
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html

        conn.send(response)
        conn.close()

# reading both the sensors (moisture & water level)
def read_sensors():
    moisture_value = moisture_sensor.read()  # 0-4095 ??
    moisture_percentage = int((moisture_value / 4095) * 100)

    water_value = 
    return moisture_percentage, water_value

# HTML code for web UI
def web_page(): 
    # read the sensors
    moisture_percentage, water_value = read_sensors()
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Plant Watering Automation</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
            button { font-size: 20px; padding: 10px 20px; margin: 10px; }
            .data-box {{ font-size: 24px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>Plant Watering Automation</h1>
        
        <div class="data-box"><b>Moisture Percentage:</b> {moisture_percentage} / 4096</div>
        <div class="data-box"><b>Water Level:</b> {water_value}</div>
        
        <button onclick="sendRequest('start')">Start</button>
        <button onclick="sendRequest('stop')">Stop</button>
        
        <script>
            // fetch sensor data every 5 sec
            function fetchSensorData() {
                fetch('/')
                    .then(response => response.text())
                    .then(html => document.body.innerHTML = html)
                    .catch(err => console.error(err));
            }
            setInterval(fetchSensorData, 5000);

            function sendRequest(action) {
                fetch('/' + action)
                    .then(response => response.text())
                    .then(data => alert(data))
                    .catch(err => console.error(err));
            }
        </script>
    </body>
    </html>
    """
    return html

def start_web_server():   
    # https://docs.micropython.org/en/latest/esp8266/tutorial/network_tcp.html 
    # 0.0.0.0 listen to all interfaces.
    # 80 port for web server
    # get the tuple
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    print("tuple:", addr)
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print("Listening on:", addr)

    while True:
        conn, addr = s.accept()
        print("Client connected from", addr)
        request = conn.recv(1024).decode()
        print("Request:", request)

        # handle the request
        if "/start" in request:
            pump.value(1)
            response = "Pump started!"
        elif "/stop" in request:
            pump.value(0)
            response = "Pump stopped!"
        else:
            response = web_page()

        # send the response
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + response)
        conn.close()

try:
    ip_address = connect_to_wifi()
    print(f"Web server running at http://{ip_address}")
    start_web_server()
except Exception as e:
    print("Error:", e)
    # pump has to be off if error happens.
    pump.value(0)



if wifi_credentials["ssid"] is None:
    ap = start_ap_mode()
    serve_ap_page()
else:
    sta = start_sta_mode(wifi_credentials["ssid"], wifi_credentials["password"])
    if sta:
        start_main_web_server(sta)
    else:
        print("Failed to connect. Restarting in AP mode.")
        ap = start_ap_mode()
        serve_ap_page()

