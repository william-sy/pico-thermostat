from machine import Pin, I2C, ADC, SoftI2C
from ssd1306 import SSD1306_I2C
from time import sleep
from neopixel import Neopixel
import time, aht, framebuf, sys, time, network, socket

###
## Variables:
#
minTemp = 5
maxTemp = 40
vacTemp = 15
comTemp = 20
slpTemp = 18
targetTemp = 18
hysteris = 0.2

# Pixel colors
yellow = (255, 100, 0)
orange = (255, 50, 0)
green  = (0, 255, 0)
blue   = (0, 0, 255)
red    = (255, 0, 0)

###
## Settings:
#

# Wifi 
ssid     = 'LOT - Byte Me'
password = 'W3<M0giToo!'
# pixel def.
pixels = Neopixel(1, 1, 27, "GRBW",10)
pixels.brightness(10)
# Switch Buttons
swUp  = Pin(20, Pin.IN, Pin.PULL_UP)
swOk  = Pin(19, Pin.IN, Pin.PULL_UP)
swCol = Pin(28, Pin.IN, Pin.PULL_UP)
swLft = Pin(18, Pin.IN, Pin.PULL_UP)
swDwn = Pin(21, Pin.IN, Pin.PULL_UP)
swRgt = Pin(2, Pin.IN, Pin.PULL_UP)
# Heating Relay
pin_relay = Pin(26, mode=Pin.OUT)
# Temp Sensor:
i2c = SoftI2C(scl=Pin(15), sda=Pin(14))
sensor = aht.AHT2x(i2c, crc=True)
# Display
pix_res_x = 128  # SSD1306 horizontal resolution
pix_res_y = 64   # SSD1306 vertical resolution
# Relay
relay = Pin(22, Pin.OUT)
# Default thermostat state
state = "Standby"
# Set timeout variable
timeOut = 0
# Place holders:
temp    = 0
hum     = 0
# If we just booted up or not
boot    = True
# Display:
i2c_dev = SoftI2C(scl=Pin(0),sda=Pin(1),freq=200000)
i2c_addr = [hex(ii) for ii in i2c_dev.scan()] # get I2C address in hex format
oled = SSD1306_I2C(pix_res_x, pix_res_y, i2c_dev) # oled controller
adc_2 = machine.ADC(2) # ADC channel 2 for input

###
## Debug the display:
# Remove after going to prod. 
if i2c_addr==[]:
    print('No I2C Display Found') 
    sys.exit() # exit routine if no dev found
else:
    print("I2C Address      : {}".format(i2c_addr[0])) # I2C device address
    print("I2C Configuration: {}".format(i2c_dev)) # print I2C params
    

def getData(type):
    ''' Which of the 2 vlaues to get from the sensor
    '''
    if type == "temp":
        return sensor.temperature
    elif type == "hum":
        return sensor.humidity
    else:
        return "NA"
    
def connect():
    ''' Connect to the WLAN
    '''
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    oled.fill(0) # clear the display
    oled.text("Connecting to:",1,1)
    oled.text("{}".format(ssid),1,10)
    oled.text("Connected on:".format(ip),1,20)
    oled.text("{}".format(ip),1,30)
    oled.show()
    print(f'')
    
def setColor(color):
    ''' Set the color of the pixel
    '''
    pixels.set_pixel(0, color)
    pixels.show()


oled.fill(0) # clear the display
oled.text("Connecting to:",1,1)
oled.text("{}".format(ssid),1,10)
oled.text("Version 1.0",1,20)
oled.show()

try:
    connect()
except KeyboardInterrupt:
    machine.reset()

while True:
    if boot == True:
        # We only need this once.
        boot = False
        # Get initial values at boot
        hum  = getData("hum")
        temp = getData("temp")
        # Set standby color  
        pixels.set_pixel(0, yellow)
        pixels.show()

    oled.fill(0) # clear the display
    oled.text("Status: {}".format(state),1,1)
    oled.text("Temp: {:.2f}".format(temp),1,10)
    oled.text("Hum: {:.2f}".format(hum),1,20)
    oled.text("Tar: {}".format(targetTemp),1,30)
    oled.show()

    if swUp.value() == 0:
        targetTemp = targetTemp +1
    if swDwn.value() == 0:
        targetTemp = targetTemp -1
        
    if swLft.value() == 0:
        print("left")
    if swRgt.value() == 0:
        print("right")
    if swOk.value() == 0:
        print("ok")

    # This will to go HP for cooling input.
    if swCol.value() == 0:
        state = "Cooling"
        setColor(blue)
        pin_relay.on()
        time.sleep_ms(200)
        pin_relay.off()
    else:
        state = "Standby"
        setColor(green)

    if timeOut < 100:
        # Update the temp only once every 10 secconds
        timeOut = timeOut +1
    else:
        hum  = getData("hum")
        temp = getData("temp")
        timeOut = 0
        
    time.sleep(0.1)