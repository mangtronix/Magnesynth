import board
import time
import pwmio
from adafruit_motor import servo
from adafruit_neokey.neokey1x4 import NeoKey1x4
# Flip display so buttons are on right
display = board.DISPLAY
display.rotation = 180

# Set false to skip printing debug messages - faster performance
serial_debug = True

from rainbowio import colorwheel
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.analoginput import AnalogInput
from adafruit_seesaw import neopixel
from adafruit_neokey.neokey1x4 import NeoKey1x4

# Give I2C devices a chance to turn on
time.sleep(0.5)

# create a PWMOut object on Pin A2.
pwm = pwmio.PWMOut(board.A0, frequency=100)

# Create a servo object, my_servo.
my_servo = servo.ContinuousServo(pwm)

# variable to toggle between forward and back
forward = True

# control speed with fader
speed = 1.0

## NeoSlider Setup
i2c = board.I2C()  # uses board.SCL and board.SDA
#neoslider = Seesaw(i2c, 0x30) # Default address
neoslider_address = 0x38 # Address with A3 cut, to avoid conflicts with Neokey at 0x30
print("Connecting to Neoslider at %x" % neoslider_address)
neoslider = Seesaw(i2c, neoslider_address) # Object to talk to NeoSlider hardware
fader = AnalogInput(neoslider, 18) # Tracks position of slider
old_fader_value = fader.value # Keep track of old value so we can respond to changes
pixels = neopixel.NeoPixel(neoslider, 14, 4, pixel_order=neopixel.GRB) # For changing colors

## Set up Neokey
print("Setting up NeoKey")
# Create a NeoKey object using existing i2c bus
neokey = NeoKey1x4(i2c, addr=0x30) # Default address


def fader_to_color(value):
    """Scale the fader values (0-1023) to the colorwheel values (0-255)."""
    return value / 1023 * 255

def fader_to_speed(value):
    return value / 1023

print("Entering main loop")
while True:
    ### NeoSlider handling
    new_fader_value = fader.value # Get the current position
    if new_fader_value != old_fader_value:
        # Position has changed
        if serial_debug:
            print(new_fader_value)

        # Fill the pixels a color based on the position of the fader.
        pixels.fill(colorwheel(fader_to_color(new_fader_value)))
        old_fader_value = new_fader_value

    ### NeoKey handling
    # Check each button, if pressed, light up the matching neopixel!
    if neokey[0]:
        if serial_debug:
            print("Button A")
        neokey.pixels[0] = 0xFF0000
        if forward:
            print("forward")
            my_servo.throttle = fader_to_speed(fader.value)
            forward = False
        else:
            print("reverse")
            my_servo.throttle = -1 * fader_to_speed(fader.value)
            forward = True
    else:
        neokey.pixels[0] = 0x0

    if neokey[1]:
        if serial_debug:
            print("Button B")
        neokey.pixels[1] = 0xFFFF00
        my_servo.throttle = 0
        time.sleep(1.0)

    else:
        neokey.pixels[1] = 0x0

    if neokey[2]:
        if serial_debug:
            print("Button C")
        neokey.pixels[2] = 0x00FF00
    else:
        neokey.pixels[2] = 0x0

    if neokey[3]:
        if serial_debug:
            print("Button D")
        neokey.pixels[3] = 0x00FFFF
    else:
        neokey.pixels[3] = 0x0