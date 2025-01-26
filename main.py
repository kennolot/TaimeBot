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
from machine import Pin

# REPLACE
SSID = "Your_WiFi_SSID"
PASSWORD = "Your_WiFi_Password"

# GPIO pin to control the water pump
# make it an output pin as it is controlled by esp32
# REPLACE PIN
pump = Pin(2, Pin.OUT)
# pump off by default
pump.value(0)

# connect to user's home network, can be accesses locally from home network.
def connect_to_wifi():
    # source: https://docs.micropython.org/en/latest/esp8266/tutorial/network_basics.html
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    print("Connecting to Wi-Fi...")
    while not wlan.isconnected():
        pass
    print("Connected to Wi-Fi:", wlan.ifconfig())
    return wlan.ifconfig()[0]



# HTML code for web UI
def web_page():    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Plant Watering Automation</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
            button { font-size: 20px; padding: 10px 20px; margin: 10px; }
        </style>
    </head>
    <body>
        <h1>Plant Watering Automation</h1>
        <button onclick="sendRequest('start')">Start</button>
        <button onclick="sendRequest('stop')">Stop</button>
        <script>
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





