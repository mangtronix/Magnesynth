# SPDX-FileCopyrightText: 2018 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT
#
# Modified by Michael Ang for String Thing
#
# Sets all servos to center position then cycles through min and max angles
# to test servo movement.

"""CircuitPython Essentials Servo standard servo example"""
import time
import board
import pwmio
from adafruit_motor import servo

print("servotest")

pins = [board.D5, board.D6, board.D9, board.D10]
servos = []
for pin in pins:
    pwm = pwmio.PWMOut(pin, duty_cycle = 2 ** 15, frequency = 50)
    servos.append(servo.Servo(pwm))



# # create a PWMOut object on Pin A2.
# pwm = pwmio.PWMOut(board.D10, duty_cycle=2 ** 15, frequency=50)

# # Create a servo object, my_servo.
# my_servo = servo.Servo(pwm)

print("setting angle 90")
for servo in servos:
    servo.angle = 90
    time.sleep(0.05)
time.sleep(5)

min_angle = 70
max_angle = 110
delay = 1

print("starting loop")
while True:
    for servo in servos:
        servo.angle = min_angle
        time.sleep(0.05)
    time.sleep(delay)

    for servo in servos:
        servo.angle = max_angle
        time.sleep(0.05)
    time.sleep(delay)

    # for angle in range(min_angle, max_angle, 1):  # 0 - 180 degrees, 5 degrees at a time.
    #     my_servo.angle = angle
    #     time.sleep(0.05)
    # for angle in range(max_angle, min_angle, -1): # 180 - 0 degrees, 5 degrees at a time.
    #     my_servo.angle = angle
    #     time.sleep(0.05)
