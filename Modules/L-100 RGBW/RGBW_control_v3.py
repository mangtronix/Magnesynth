# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: MIT

# CREATED BY: Mustafa Bakir
#             Using Claude 4.5
# DATE      : 09/10/2025
# ---------MANGLAB----------
"""
NeoPixel RGBW Control using NeoKey and NeoSlider with Preset Storage
- Button A controls Red channel
- Button B controls Green channel
- Button C controls Blue channel
- Button D controls White/Brightness/Alpha channel
- Slider adjusts the selected channel(s) value (0-255)
- Multiple channels can be selected simultaneously
- Press a selected button again to deselect it
- Last preset is automatically saved and restored on power-up
"""

import board
import time
import neopixel as board_neopixel
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.analoginput import AnalogInput
from adafruit_seesaw import neopixel
from adafruit_neokey.neokey1x4 import NeoKey1x4
import microcontroller

# flip display so buttons on right
display = board.DISPLAY
display.rotation = 180

print("NeoPixel RGBW Control Demo - Multi-Channel with Preset Storage")

# debug flags
ENABLE_DEBUG = True
SHOW_CHANNEL_CHANGES = True
SHOW_VALUE_CHANGES = True

# preset storage config
PRESET_SAVE_DELAY = 2.0  # secs before auto-save
MAGIC_BYTE = 0xA5  # magic byte for valid data
NVM_START_ADDR = 0  # start addr in nvm

# let i2c devices wake up
time.sleep(0.5)

# neopixel strip on A0 (8px)
NUM_PIXELS = 8
main_pixels = board_neopixel.NeoPixel(board.A0, NUM_PIXELS, brightness=1.0, auto_write=False, pixel_order=board_neopixel.GRBW)

# neoslider setup
i2c = board.I2C()
neoslider_address = 0x38  # A3 cut to avoid conflict w/ neokey at 0x30
print("Connecting to NeoSlider at %x" % neoslider_address)
neoslider = Seesaw(i2c, neoslider_address)
fader = AnalogInput(neoslider, 18)  # slider position
slider_pixels = neopixel.NeoPixel(neoslider, 14, 4, pixel_order=neopixel.GRB)

# neokey setup
print("Setting up NeoKey")
neokey = NeoKey1x4(i2c, addr=0x30)

# preset storage funcs
def save_preset(r, g, b, w):
    """save rgbw to nvm: [magic, r, g, b, w, checksum]"""
    try:
        # calc checksum (xor all vals)
        checksum = MAGIC_BYTE ^ r ^ g ^ b ^ w

        # prep data
        data = bytearray([MAGIC_BYTE, r, g, b, w, checksum])

        print("=== SAVING PRESET ===")
        print(f"Saving: R={r}, G={g}, B={b}, W={w}")
        print(f"Data to write: {[hex(b) for b in data]}")

        # write to nvm
        microcontroller.nvm[NVM_START_ADDR:NVM_START_ADDR + 6] = data

        # verify write
        verify = microcontroller.nvm[NVM_START_ADDR:NVM_START_ADDR + 6]
        print(f"Verification read: {[hex(b) for b in verify]}")

        if list(data) == list(verify):
            print("✓ Preset saved and verified successfully")
            print("=== END SAVE ===\n")
            return True
        else:
            print("ERROR: Write verification failed!")
            print("=== END SAVE ===\n")
            return False

    except Exception as e:
        print(f"ERROR saving preset: {e}")
        import traceback
        traceback.print_exception(e)
        return False

def load_preset():
    """load rgbw from nvm, returns (r,g,b,w) or None"""
    try:
        # read 6 bytes
        data = microcontroller.nvm[NVM_START_ADDR:NVM_START_ADDR + 6]

        # debug: show raw mem
        print("=== NVM DEBUG ===")
        print(f"Raw NVM bytes: {[hex(b) for b in data]}")
        print(f"Magic byte expected: {hex(MAGIC_BYTE)}, found: {hex(data[0])}")

        # verify magic byte
        if data[0] != MAGIC_BYTE:
            print("No valid preset found (magic byte mismatch)")
            print(f"This is likely first boot or memory was cleared")
            return None

        # extract vals
        r, g, b, w = data[1], data[2], data[3], data[4]
        stored_checksum = data[5]

        print(f"Stored values: R={r}, G={g}, B={b}, W={w}")
        print(f"Stored checksum: {hex(stored_checksum)}")

        # verify checksum
        calculated_checksum = MAGIC_BYTE ^ r ^ g ^ b ^ w
        print(f"Calculated checksum: {hex(calculated_checksum)}")

        if calculated_checksum != stored_checksum:
            print("ERROR: Preset corrupted (checksum mismatch)")
            return None

        # validate ranges (0-255)
        if not all(0 <= val <= 255 for val in [r, g, b, w]):
            print("ERROR: Preset values out of range")
            return None

        print(f"✓ Preset loaded successfully: R={r}, G={g}, B={b}, W={w}")
        print("=== END NVM DEBUG ===\n")
        return (r, g, b, w)

    except Exception as e:
        print(f"ERROR loading preset: {e}")
        import traceback
        traceback.print_exception(e)
        return None

def clear_preset():
    """clear stored preset"""
    try:
        microcontroller.nvm[NVM_START_ADDR:NVM_START_ADDR + 6] = bytearray([0] * 6)
        debug_print("Preset cleared", "general")
    except Exception as e:
        print(f"Error clearing preset: {e}")

# init rgbw - try load from storage first
stored_preset = load_preset()
if stored_preset:
    red_value, green_value, blue_value, white_value = stored_preset
    print(f"Restored preset: R={red_value}, G={green_value}, B={blue_value}, W={white_value}")
else:
    red_value = 0
    green_value = 0
    blue_value = 0
    white_value = 0
    print("Starting with default values (all zeros)")

# track selected channels [r, g, b, w]
selected_channels = [False, False, False, False]

# prev button states for edge detection
prev_button_states = [False, False, False, False]

# prev slider val for change detection
prev_slider_value = -1

# auto-save tracking
last_change_time = time.monotonic()
values_need_saving = False
last_saved_values = (red_value, green_value, blue_value, white_value)

def debug_print(message, debug_type="general"):
    """print debug msgs based on flags"""
    if not ENABLE_DEBUG:
        return

    if debug_type == "channel" and SHOW_CHANNEL_CHANGES:
        print(message)
    elif debug_type == "value" and SHOW_VALUE_CHANGES:
        print(message)
    elif debug_type == "general":
        print(message)

def map_slider_to_byte(value):
    """map slider val (0-1023) to byte (0-255)"""
    return int(value * 255 / 1023)

def update_main_pixels():
    """update all neopixels w/ current rgbw"""
    for i in range(NUM_PIXELS):
        if hasattr(main_pixels, 'fill'):
            main_pixels[i] = (red_value, green_value, blue_value, white_value)
        else:
            # rgb pixels - use white as brightness
            brightness_factor = (white_value / 255.0) if white_value > 0 else 1.0
            main_pixels[i] = (
                int(red_value * brightness_factor),
                int(green_value * brightness_factor),
                int(blue_value * brightness_factor)
            )
    main_pixels.show()

def update_slider_leds():
    """update slider leds to show channel selection"""
    num_selected = sum(selected_channels)

    if num_selected == 0:
        # no channels - dim white
        slider_pixels.fill((10, 10, 10))
    elif num_selected == 1:
        # single channel - show color
        if selected_channels[0]:  # red
            slider_pixels.fill((255, 0, 0))
        elif selected_channels[1]:  # green
            slider_pixels.fill((0, 255, 0))
        elif selected_channels[2]:  # blue
            slider_pixels.fill((0, 0, 255))
        elif selected_channels[3]:  # white
            slider_pixels.fill((255, 255, 255))
    else:
        # multi channel - show mix
        r = 255 if selected_channels[0] else 0
        g = 255 if selected_channels[1] else 0
        b = 255 if selected_channels[2] else 0
        w = 255 if selected_channels[3] else 0

        # blend white in if selected
        if selected_channels[3]:
            r = min(255, r + 128)
            g = min(255, g + 128)
            b = min(255, b + 128)

        slider_pixels.fill((r, g, b))

def get_selected_channels_string():
    """get string repr of selected channels"""
    channel_names = ["R", "G", "B", "W"]
    selected = [channel_names[i] for i, sel in enumerate(selected_channels) if sel]
    return "+".join(selected) if selected else "None"

def check_and_save_preset():
    """check if preset needs saving and save if appropriate"""
    global values_need_saving, last_saved_values

    current_values = (red_value, green_value, blue_value, white_value)

    if values_need_saving and current_values != last_saved_values:
        current_time = time.monotonic()

        # save if enough time passed since last change
        if current_time - last_change_time >= PRESET_SAVE_DELAY:
            if save_preset(red_value, green_value, blue_value, white_value):
                last_saved_values = current_values
                values_need_saving = False

# init neokey leds to show current vals
for i in range(4):
    if i == 0:
        neokey.pixels[0] = (red_value//8, 0, 0)
    elif i == 1:
        neokey.pixels[1] = (0, green_value//8, 0)
    elif i == 2:
        neokey.pixels[2] = (0, 0, blue_value//8)
    elif i == 3:
        neokey.pixels[3] = (white_value//8, white_value//8, white_value//8)

# init display w/ restored preset
update_main_pixels()
update_slider_leds()

print("Entering main loop")
print("Press buttons to select/deselect color channels")
print("Multiple channels can be selected simultaneously")
print("Move slider to adjust selected channel(s)")
print(f"Preset will auto-save after {PRESET_SAVE_DELAY}s of inactivity")

while True:
    # neokey handling - check button presses (edge detection)
    for i in range(4):
        current_state = neokey[i]

        # detect button press (rising edge)
        if current_state and not prev_button_states[i]:
            # toggle selection
            selected_channels[i] = not selected_channels[i]

            channel_names = ["Red", "Green", "Blue", "White/Brightness"]

            if selected_channels[i]:
                debug_print(f"Selected {channel_names[i]} channel", "channel")
            else:
                debug_print(f"Deselected {channel_names[i]} channel", "channel")

            debug_print(f"Active channels: {get_selected_channels_string()}", "channel")
            update_slider_leds()

        prev_button_states[i] = current_state

    # update neokey leds to show selection and vals
    for i in range(4):
        if selected_channels[i]:
            # bright color for selected
            if i == 0:
                neokey.pixels[0] = (255, 0, 0)
            elif i == 1:
                neokey.pixels[1] = (0, 255, 0)
            elif i == 2:
                neokey.pixels[2] = (0, 0, 255)
            elif i == 3:
                neokey.pixels[3] = (255, 255, 255)
        else:
            # dim indicator showing current val
            if i == 0:
                neokey.pixels[0] = (red_value//8, 0, 0)
            elif i == 1:
                neokey.pixels[1] = (0, green_value//8, 0)
            elif i == 2:
                neokey.pixels[2] = (0, 0, blue_value//8)
            elif i == 3:
                neokey.pixels[3] = (white_value//8, white_value//8, white_value//8)

    # neoslider handling - adjust selected channel(s)
    if any(selected_channels):
        current_slider_value = map_slider_to_byte(fader.value)

        # only update if slider val changed
        if current_slider_value != prev_slider_value:
            prev_slider_value = current_slider_value
            values_changed = False
            changed_channels = []

            # update all selected channels
            if selected_channels[0]:  # red
                red_value = current_slider_value
                values_changed = True
                changed_channels.append(f"R:{red_value}")

            if selected_channels[1]:  # green
                green_value = current_slider_value
                values_changed = True
                changed_channels.append(f"G:{green_value}")

            if selected_channels[2]:  # blue
                blue_value = current_slider_value
                values_changed = True
                changed_channels.append(f"B:{blue_value}")

            if selected_channels[3]:  # white/brightness
                white_value = current_slider_value
                values_changed = True
                changed_channels.append(f"W:{white_value}")

            if values_changed:
                update_main_pixels()

                # mark vals need saving and update timestamp
                values_need_saving = True
                last_change_time = time.monotonic()

                if changed_channels:
                    debug_print(f"Updated: {', '.join(changed_channels)}", "value")
                    debug_print(f"Current RGBW: [{red_value}, {green_value}, {blue_value}, {white_value}]", "value")

    # check if we need to auto-save preset
    check_and_save_preset()

    # small delay to prevent overwhelming i2c bus
    time.sleep(0.01)
