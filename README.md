# pico-thermostat
A pi pico thermostat

## Thermostat
Simple proof of concept added. 


## Wires
There is a kicad project in the kicad folder with the latest files needed.
This is subjective to changes, as it still needs more work (debounce/dc-dc stepdown/onboard relay)

## currently working:
- 7 buttons (up,down,l,r,ok,back,menu)
- 2 inputs
- 1 relay
- 1 display
- 1 temperature / humidity sensor (might upgrade to one with co2)
- dewpoint calulation
- basic web portal to setup wifi

## To do
- More software
- More debugging 
- Finalizing the design

## Why?
Because I could not find a cheap alternative on the usual spots with 2 dry contact inputs. 

The inputs:
- Cooling mode, this signal from the heatpump indicates that it is cooling instead of heating the house, the thermostat needs to behave differently
- Night mode, when you have multiple thermosats, you can signal them all to go into night mode (to indicate a lower temperature is requested than in day mode saving money)


![Version1](https://github.com/william-sy/pico-thermostat/blob/283dc2f304fdcb1536dcbbf625a0f4007fa67c08/pictures/v1.JPG)
