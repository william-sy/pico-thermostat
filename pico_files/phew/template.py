# The main thermostat routine:
from machine import Pin, I2C, ADC, SoftI2C
from ssd1306 import SSD1306_I2C
from time import sleep
from neopixel import Neopixel
import time, aht, framebuf, sys, time, network, socket,uasyncio,json

async def run(host, port):
    # Start the webserver up.
    from . import server
    uasyncio.create_task(uasyncio.start_server(server._handle_request, host, port))
    # If the webserver updates these we need a reset. (machine.reset())
    SETTING_FILE = "../settings.json"
    # File was found, attempt to connect to wifi...
    with open(SETTING_FILE) as f:
        settings = json.load(f)
        f.close()
    ###
    ## Variables:
    #
    minTemp = settings["minTemp"]
    maxTemp = settings["maxTemp"]
    targetTemp = settings["targetTemp"]
    hysteresis = settings["hysteresis"]
    displayUpdate = settings["displayUpdate"]
    state = "Stanby"
    # Switch Buttons
    swUp  = Pin(20, Pin.IN, Pin.PULL_UP)
    swOk  = Pin(19, Pin.IN, Pin.PULL_UP)
    swCol = Pin(28, Pin.IN, Pin.PULL_UP)
    swLft = Pin(18, Pin.IN, Pin.PULL_UP)
    swDwn = Pin(21, Pin.IN, Pin.PULL_UP)
    swRgt = Pin(2, Pin.IN, Pin.PULL_UP)
    #swMen = Pin(2, Pin.IN, Pin.PULL_UP) # Menu
    #swBck = Pin(2, Pin.IN, Pin.PULL_UP) # Back
    #swNM = Pin(2, Pin.IN, Pin.PULL_UP) # Night Mode
    #swCM = Pin(2, Pin.IN, Pin.PULL_UP) # Cooling Mode

    # Temp Sensor and display:
    i2c      = SoftI2C(scl=Pin(15), sda=Pin(14))
    sensor   = aht.AHT2x(i2c, crc=True)
    i2c_dev  = SoftI2C(scl=Pin(0),sda=Pin(1))
    oled     = SSD1306_I2C(128, 64, i2c_dev)

    # Relay
    relay    = Pin(22, Pin.OUT)
    # Set timeout variable
    timeOut  = 0
    # Place holders:
    temp     = 0
    hum      = 0
    # If we just booted up or not
    boot     = True
    
    while True:
        # Turn on the screen upon boot, we only need this once:
        if boot == True:
            updateScreen(state, sensor.temperature, sensor.humidity, targetTemp, i2c_dev, oled, True)
            sleep(2)
            updateScreen(state,sensor.temperature, sensor.humidity,targetTemp, i2c_dev, oled)
            boot = False
         
        # Button controls:
        if swUp.value() == 0:
            targetTemp = targetTemp + 0.5
            updateScreen(state,sensor.temperature, sensor.humidity,targetTemp, i2c_dev, oled)
        if swDwn.value() == 0:
            targetTemp = targetTemp - 0.5
            updateScreen(state,sensor.temperature, sensor.humidity,targetTemp, i2c_dev, oled)
        if swLft.value() == 0:
            print("left")
        if swRgt.value() == 0:
            print("right")
        if swOk.value() == 0:
            mainMenu()
            updateScreen(state,sensor.temperature, sensor.humidity,targetTemp, i2c_dev, oled)
        
        # Auto display update every once in a while.
        if displayUpdate > 0:
            displayUpdate = displayUpdate - 1
        else:
            displayUpdate = settings["displayUpdate"]
            updateScreen(state,sensor.temperature, sensor.humidity,targetTemp, i2c_dev, oled)
           
        # heating / cooling logic eventually..
        # Add cooling and hyst. 
        if targetTemp > sensor.temperature:
            state = "Heating"
        elif targetTemp < sensor.temperature:
            state = "Standby"
            
        await uasyncio.sleep(0.1)

def updateScreen(state, temp, hum, target,  i2c_dev, oled, boot=False):
        if boot == False: 
            oled.fill(0) # clear the display
            oled.text("Status: {}".format(state),1,1)
            oled.hline(0, 10, 128, 1) 
            oled.text("Temp: {:.2f}".format(temp),1,15)
            oled.text("Hum: {:.2f}".format(hum),1,25)
            oled.text("Tar: {}".format(target),1,35)
            oled.hline(0, 45, 128, 1) 
            oled.text("OK for menu",1,50)
            oled.show()
        else:
            oled.fill(0)
            oled.text("Version 1",1,1)
            oled.text("Build:",1,10)
            oled.text("2024.01.01-01",1,20)
            oled.show()
     
def mainMenu():
    # This will update the values live, and persist them in the json file.
    SETTING_FILE = "../settings.json"
    menu = 1
    while menu == 1:
        oled.fill(0) # clear the display
        oled.text("Settings:",1,1)
        oled.hline(0, 10, 128, 1) 
        oled.text("U/D: Change val.",1,15)
        oled.text("L/R: Next/prev.",1,25)
        oled.text("OK: Next",1,35)
        oled.text("",1,45)
        oled.show()
        sleep(3) 
        setting = [hysteresis]
        for i in setting:
#{"minTemp": 5, "maxTemp": 40, "hysteresis": 0.2, "targetTemp": 20, "displayUpdate": 600, "calibrationUp": 0, "calibrationDwn": 0, "power": 1, "displayTimeOut": 30}
            menu = 0
    #with open(SETTING_FILE, "w") as f:
    #    settings = json.load(f)
        # Greet with tutorial:
    #    f.close()
    
