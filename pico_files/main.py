from phew import access_point, connect_to_wifi, is_connected_to_wifi, dns, server
from phew.template import render_template
from machine import Pin, I2C, ADC, SoftI2C
from ssd1306 import SSD1306_I2C
from time import sleep
import time, aht, framebuf, sys, time, network, socket, json, uasyncio, machine, os, utime, _thread

AP_NAME = "Pico Thermostat"
AP_DOMAIN = "pipico.net"
AP_TEMPLATE_PATH = "ap_templates"
APP_TEMPLATE_PATH = "app_templates"
WIFI_FILE = "wifi.json"
WIFI_MAX_ATTEMPTS = 3
SETTING_FILE = "settings.json"

def machine_reset():
    utime.sleep(1)
    print("Resetting...")
    machine.reset()

def setup_mode():
    print("Entering setup mode...")
    
    def ap_index(request):
        if request.headers.get("host").lower() != AP_DOMAIN.lower():
            return render_template(f"{AP_TEMPLATE_PATH}/redirect.html", domain = AP_DOMAIN.lower())

        return render_template(f"{AP_TEMPLATE_PATH}/index.html")

    def ap_configure(request):
        print("Saving wifi credentials...")

        with open(WIFI_FILE, "w") as f:
            json.dump(request.form, f)
            f.close()

        # Reboot from new thread after we have responded to the user.
        _thread.start_new_thread(machine_reset, ())
        return render_template(f"{AP_TEMPLATE_PATH}/configured.html", ssid = request.form["ssid"])
        
    def ap_catch_all(request):
        if request.headers.get("host") != AP_DOMAIN:
            return render_template(f"{AP_TEMPLATE_PATH}/redirect.html", domain = AP_DOMAIN)

        return "Not found.", 404

    server.add_route("/", handler = ap_index, methods = ["GET"])
    server.add_route("/configure", handler = ap_configure, methods = ["POST"])
    server.set_callback(ap_catch_all)

    ap = access_point(AP_NAME)
    ip = ap.ifconfig()[0]
    dns.run_catchall(ip)

def application_mode():
    print("Entering application mode.")
    onboard_led = Pin("LED", machine.Pin.OUT)
    # Default thermostat state
    state    = "Standby"
    # Heating Relay
    pin_relay = Pin(26, mode=Pin.OUT)


    def app_index(request):
        return render_template(f"{APP_TEMPLATE_PATH}/index.html")

    def app_toggle_led(request):
        onboard_led.toggle()
        return "OK"
    
    def app_reset(request):
        # Deleting the WIFI configuration file will cause the device to reboot as
        # the access point and request new configuration.
        os.remove(WIFI_FILE)
        # Reboot from new thread after we have responded to the user.
        _thread.start_new_thread(machine_reset, ())
        return render_template(f"{APP_TEMPLATE_PATH}/reset.html", access_point_ssid = AP_NAME)

    def app_catch_all(request):
        return "Not found.", 404

    def app_toggle_heat(request):
        pin_relay.toggle()
        return "OK"

    def app_toggle_cool(request):
        state = "Cooling"
        return "OK", state
    
    def thermostat(request):
        # Temp Sensor:
        i2c = SoftI2C(scl=Pin(15), sda=Pin(14))
        sensor = aht.AHT2x(i2c, crc=True)
        return f"<br> Temperature: {round(sensor.temperature, 2)} <br> Humidity: {round(sensor.humidity,2)} "

    server.add_route("/", handler = app_index, methods = ["GET"])
    server.add_route("/toggle", handler = app_toggle_led, methods = ["GET"])
    server.add_route("/toggleHeat", handler = app_toggle_heat, methods = ["GET"])
    server.add_route("/toggleCool", handler = app_toggle_cool, methods = ["GET"])
    server.add_route("/reset", handler = app_reset, methods = ["GET"])
    server.add_route("/thermostat", handler = thermostat, methods = ["GET"])
    # Add other routes for your application...
    server.set_callback(app_catch_all)

# Figure out which mode to start up in...
try:
    os.stat(WIFI_FILE)

    # File was found, attempt to connect to wifi...
    with open(WIFI_FILE) as f:
        wifi_current_attempt = 1
        wifi_credentials = json.load(f)
        
        while (wifi_current_attempt < WIFI_MAX_ATTEMPTS):
            ip_address = connect_to_wifi(wifi_credentials["ssid"], wifi_credentials["password"])

            if is_connected_to_wifi():
                print(f"Connected to wifi, IP address {ip_address}")
                break
            else:
                wifi_current_attempt += 1
                
        if is_connected_to_wifi():
            application_mode()
        else:
            # Bad configuration, delete the credentials file, reboot
            # into setup mode to get new credentials from the user.
            print("Bad wifi connection!")
            print(wifi_credentials)
            os.remove(WIFI_FILE)
            machine_reset()

except Exception:
    # Either no wifi configuration file found, or something went wrong, 
    # so go into setup mode.
    setup_mode()

# Start the web server...
server.run()

