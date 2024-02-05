# The main thermostat routine:
from machine import Pin, I2C, ADC, SoftI2C, reset
from ssd1306 import SSD1306_I2C
from time import sleep
import time, aht, framebuf, sys, time, network, socket, uasyncio, json, math

async def run(host, port):
    from . import server 
    uasyncio.create_task(uasyncio.start_server(server._handle_request, host, port)) # Start the webserver up as a seperate process.
    # If the webserver updates these we need a reset. (machine.reset())
    SETTING_FILE = "../settings.json"
    with open(SETTING_FILE) as f:
        settings = json.load(f)
        f.close()
    ###
    ## Variables:
    #
    minTemp 		= settings["minTemp"]			# Least ammount of temp acceptable
    maxTemp 		= settings["maxTemp"]			# Max request room temp / max heat boiler can provide
    tempStep 		= settings["tempStep"]			# How much we want to increase od decrease the temperature per button press.
    targetTemp 		= settings["targetTemp"]		# The default target upon boot
    hysteresis 		= settings["hysteresis"]		#
    displayUpdate 	= settings["displayUpdate"]		# How often we want to update the screen
    displayTimeOut	= settings["displayTimeOut"]	# When should the screen be turned off
    calibration     = settings["calibration"]       # calibration of the temperature sensor.
    state   		= "Standby"						# Default thermostat state
    screen 			= True							# Screen on / off state
    temperature		= 0								# Temperature
#    hum      		= 0								# Humidity
    boot     		= True							# This is set to false after the boot screen
#    menu			= False							# Determine if we are in menu mode
    relay = Pin(26, Pin.OUT)						# The relay for requesting heat
    # Switch Buttons
    swUp  = Pin(20, Pin.IN, Pin.PULL_UP)            # Up
    swOk  = Pin(19, Pin.IN, Pin.PULL_UP)            # OK
    swDwn = Pin(21, Pin.IN, Pin.PULL_UP)            # Down

    # These buttons are not used at the moment. 
    #swLft = Pin(18, Pin.IN, Pin.PULL_UP)            # Left
    #swRgt = Pin(2,  Pin.IN, Pin.PULL_UP)            # Right
    #swMen = Pin(3, Pin.IN, Pin.PULL_UP)             # Menu
    #swBck = Pin(4, Pin.IN, Pin.PULL_UP)             # Back
    #swNM = Pin(2, Pin.IN, Pin.PULL_UP)              # Night Mode
    swCM = Pin(28, Pin.IN, Pin.PULL_UP)             # Cooling Mode

    # Temp Sensor and display:
    i2c      = SoftI2C(scl=Pin(15), sda=Pin(14))
    sensor   = aht.AHT2x(i2c, crc=True)
    i2c_dev  = SoftI2C(scl=Pin(0),sda=Pin(1))
    oled     = SSD1306_I2C(128, 64, i2c_dev)

    while True:
        dewpoint    = dewPoint(sensor.temperature, sensor.humidity)
        temperature = sensor.temperature + calibration
        # Turn on the screen upon boot, we only need this once:
        if boot == True:
            updateScreen(state, temperature, sensor.humidity, targetTemp, dewpoint, oled, True)
            sleep(2)
            updateScreen(state, temperature, sensor.humidity, targetTemp, dewpoint, oled)
            boot = False

        if screen == True:
            if displayTimeOut > 0:
                displayTimeOut = displayTimeOut -1
            elif displayTimeOut == 0:
                displayTimeOut = settings["displayTimeOut"]
                screenState(oled, "off")
                screen = False
                
            # Button controls:
            if swUp.value() == 0:
                displayTimeOut = settings["displayTimeOut"] # Reset display off timer
                if targetTemp < maxTemp:
                    targetTemp = targetTemp + tempStep	    # Up the requested temperature
                updateScreen(state, temperature, sensor.humidity, targetTemp, dewpoint, oled)
            if swDwn.value() == 0:
                displayTimeOut = settings["displayTimeOut"]	# Reset display off timer
                if targetTemp > minTemp:
                    targetTemp = targetTemp - tempStep		# Decrease the requested temperature
                updateScreen(state, temperature, sensor.humidity, targetTemp, dewpoint, oled)
            if swOk.value() == 0:
                mainMenu(oled, tempStep)
                #pass        # menu button pressed, need to go into menu.

            # Auto display update every once in a while.
            if displayUpdate > 0:
                displayUpdate = displayUpdate - 1
            else:
                displayUpdate = settings["displayUpdate"]
                updateScreen(state, temperature, sensor.humidity, targetTemp, dewpoint, oled)
               
            onTemp  = sensor.temperature + hysteresis
            offTemp = sensor.temperature - hysteresis
            if swCM.value() == 0: # If cooling mode is active
                if targetTemp < onTemp:
                    state = "Cooling"
                    relay.value(1)
                    #updateScreen(state, temperature, sensor.humidity, targetTemp, dewpoint, oled)
                elif targetTemp > offTemp:
                    state = "Standby"
                    relay.value(0)
            else: 
                # Normal thermostat mode
                if targetTemp > onTemp:
                    state = "Heating"
                    relay.value(1)
                    #updateScreen(state, temperature, sensor.humidity, targetTemp, dewpoint, oled)
                elif targetTemp < offTemp:
                    state = "Standby"
                    relay.value(0)
                    #updateScreen(state, temperature, sensor.humidity, targetTemp, dewpoint, oled)
        else:
            #Has to be a better way for this but here we are:
            if swUp.value() == 0 or swDwn.value() == 0 or swUp.value() == 0 or swRgt.value() == 0 or swLft.value() == 0 or swOk.value() == 0 or swMen.value() == 0 or swBck.value() == 0 :
                screen = True
                screenState(oled, "on")
                
        await uasyncio.sleep(0.1)

def screenState(oled, action):
    if action == "on":
        oled.poweron()
    elif action == "off":
        oled.poweroff()

def updateScreen(state, temp, hum, target, dewpoint, oled, boot=False):
    """Screen updater.
    """
    st = ""
    if state == "Standby":
        st = "S"
    elif state == "Heating":
        st = "H"
    elif state == "Cooling":
        st = "C"

    if boot == False: 
        oled.fill(0) # clear the display
        #oled.text("Status: {}".format(state),1,1)
        #oled.hline(0, 10, 128, 1) 
        oled.text("Temp:",1,15)
        oled.text("{:.2f}".format(temp),65,15)
        oled.text("{}".format(st),110,15)
        oled.text("Target:",1,25)
        oled.text("{:.2f}".format(target),65,25)
        oled.text("Hum:",1,35)
        oled.text("{:.2f}".format(hum),65,35)
        oled.text("DPT:",1,45)
        oled.text("{}".format(dewpoint),65,45)
        #oled.hline(0, 45, 128, 1) 
        #oled.text("OK for menu",1,50)
        oled.show()
    else:
        oled.fill(0)
        oled.text("Version 2",1,1)
        oled.text("Build:",1,10)
        oled.text("2024.02.01-01",1,20)
        oled.show()

def menuScreen(oled, setting, value, expl):
    oled.fill(0) # clear the display
    oled.text("Settings:",1,1)
    oled.hline(0, 10, 128, 1)
    if value == 9999:
        oled.text("{}".format(setting),1,15)
        oled.text("{}".format(expl),1,25)
    else:
        oled.text("{}".format(setting),1,15)
        oled.text("{:.2f}".format(value),1,25)
        oled.text("{}".format(expl),1,35)
    oled.show()

def dewPoint(temp, hum):
    """Compute the dew point in degrees Celsius
    """
    A = 17.27
    B = 237.7
    alpha = ((A * temp) / (B + temp)) + math.log(hum/100.0)
    roundedDewPoint = round((B * alpha) / (A - alpha), 2)
    return roundedDewPoint #(B * alpha) / (A - alpha)
        
def mainMenu(oled, tempStep):
    swUp  = Pin(20, Pin.IN, Pin.PULL_UP)            # Up
    swOk  = Pin(19, Pin.IN, Pin.PULL_UP)            # OK
    swDwn = Pin(21, Pin.IN, Pin.PULL_UP)            # Down
    # Load the values:
    SETTING_FILE = "../settings.json"
    with open(SETTING_FILE) as f:
        settings = json.load(f)
        f.close()
    # Iterate on the values and change them where needed:
    menu = True
    while menu == True:
        oled.fill(0) # clear the display
        oled.text("Settings:",1,1)
        oled.hline(0, 10, 128, 1) 
        oled.text("Up/Down:",1,15)
        oled.text("Change value",1,25)
        oled.text("OK: Next",1,45)
        oled.text("",1,45)
        oled.show()
        sleep(3)
        for key, value in settings.items():
            subMenuItem = 1
            while subMenuItem == 1:
                sleep(0.1)
                menuScreen(oled, key, value, "")
                if swUp.value() == 0:
                    value = value + tempStep
                    menuScreen(oled, key, value, "")
                if swDwn.value() == 0:
                    value = value - tempStep
                    menuScreen(oled, key, value, "")
                if swOk.value() == 0:
                    settings[key] = value
                    subMenuItem = 0
        # We need to ask if we want ot exit or go again
        exitQuestion = True
        key 	= "Want to exit?"
        expl 	= "Stay / Exit"
        value 	= 9999
        while exitQuestion == True:
            sleep(0.1)
            menuScreen(oled, key, value, expl)
            if swUp.value() == 0:
                expl = "Exit"
                menuScreen(oled, key, value, expl)
            if swDwn.value() == 0:
                expl = "Stay"
                menuScreen(oled, key, value, expl)
            if swOk.value() == 0:
                if expl == "Exit":
                    # Write changes to file, reload thermostat.
                    with open(SETTING_FILE, 'w') as f:
                        json.dump(settings, f)
                        f.close()
                      
                    reset()
                elif expl == "Stay":
                    exitQuestion 	= False
                    menu 			= True
                    
       
                            
    

