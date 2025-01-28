import network
import socket
from machine import Pin, ADC

SSID = "PlantWateringAuto"
PASSWORD = "12345678"

moisture_sensor = ADC(Pin(27))
moisture_sensor.atten(ADC.ATTN_11DB)  # Set attenuation for full range (0-3.3V)

water_level_sensor = Pin(14, Pin.IN)  # Water level sensor on GPIO 4 (digital)

# GPIO setup for water pump
pump = Pin(15, Pin.OUT)
pump.value(0)  # Pump starts off

def start_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=SSID, password=PASSWORD)
    
    print("Starting Access Point...")
    while not ap.active():
        pass
    print("Access Point active with IP:", ap.ifconfig()[0])
    return ap.ifconfig()[0]  # Return the IP address

def web_page():    
    moisture_value = moisture_sensor.read()  # Read moisture level (0-4095)
    water_level = "Full" if water_level_sensor.value() == 1 else "Low"  # Water level status
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Plant Watering System</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
            button {{ font-size: 20px; padding: 10px 20px; margin: 10px; }}
        </style>
    </head>
    <body>
        <h1>Plant Watering System</h1>
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
            setInterval(updateData, 5000);  // Refresh every 5 seconds    
        </script>
    </body>
    </html>
    """
    return html

def start_web_server():
    """Start the web server."""
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print("Listening on:", addr)

    while True:
        conn, addr = s.accept()
        print("Client connected from", addr)
        request = conn.recv(1024).decode()
        print("Request:", request)

        # Handle the request
        if "/start" in request:
            pump.value(1)
            response = "Pump started!"
        elif "/stop" in request:
            pump.value(0)
            response = "Pump stopped!"
        else:
            response = web_page()

        # Send the response
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + response)
        conn.close()

try:
    ip_address = start_access_point()
    print(f"Web server running at http://{ip_address}")
    start_web_server()
except Exception as e:
    print("Error:", e)
    pump.value(0)  # Ensure the pump is off in case of an error
