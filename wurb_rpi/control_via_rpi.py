#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import os
import time
import pathlib
import logging.handlers

# Check if GPIO is available.
gpio_available = True
try:
    import RPi.GPIO as GPIO
except:
    gpio_available = False


class ControlViaRaspberryPi(object):
    """For Raspberry Pi. Uses GPIO or a computer mouse to control
       Raspberry Pi shutdown and to activate various recording modes.
       This module is running as a process separated from the WURB
       recorder process. The REST API is used when sending commands
       to the recorder.

    Installation:
    - Add the launch of this module to /etc/rc.local.
    - Add a three way position switch. Connect ground (GPIO pin 39) to the middle pin,
      GPIO pin 36 (aka. GPIO 16) and GPIO pin 37 (aka. GPIO 26) to the two other pins.
    - Add a label for the switch: "Power off - Normal - User default mode".
    - Connect an USB mouse.
    """

    def __init__(self):
        """ """
        global gpio_available
        # Set up logging.
        self.logger = logging.getLogger("WURB_RPi")
        self.logging_setup()
        self.logger.info("\n\n=== Raspberry Pi for WURB control. ===\n")
        # GPIO pin numbers 1-40.
        # GPIO pin number 34 and 39 are both Ground.
        self.gpio_pin_user_default = 36  # Also called GPIO 16.
        self.gpio_pin_shutdown = 37  # Also called GPIO 26.

        # Settings for mouse control.
        self.left_and_right_time = 3.0  # Left and right buttons. 3 sec.
        self.left_time = 1.0  # Left button. 1 sec.
        self.middle_time = 1.0  # Left button. 1 sec.
        self.right_time = 1.0  # Right button. 1 sec.
        # Internals.
        self.left_and_right_start = False
        self.left_start = False
        self.middle_start = False
        self.right_start = False
        self.last_command = ""

    def raspberry_pi_shutdown(self):
        """ """
        try:
            self.logger.info("RPi GPIO control: Raspberry Pi shutdown.")
            # os.system("sudo shutdown -h now")
        except:
            self.logger.error("RPi GPIO control: Shutdown failed.")

    def send_wurb_rec_mode(self, rec_mode):
        """ """
        try:
            self.logger.info("RPi GPIO control: WURB User default mode: ", rec_mode)
            # os.system("wget localhost:8000/?rec_mode=" + rec_mode)
        except:
            self.logger.error("RPi GPIO control: Command failed.")

    def mouse_left_and_right_action(self):
        """ """
        self.raspberry_pi_shutdown()

    def mouse_left_action(self):
        """ """
        self.send_wurb_rec_mode(rec_mode="user_default_off")

    def mouse_middle_action(self):
        """ """
        # Not used.

    def mouse_right_action(self):
        """ """
        self.send_wurb_rec_mode(rec_mode="user_default_on")

    # === Internals. ===
    async def setup_gpio(self):
        """ """
        global gpio_available
        if gpio_available:
            GPIO.setmode(GPIO.BOARD)  # Use pin numbers, 1-40.
            # Activate and use the built in pull-up resistors.
            GPIO.setup(self.gpio_pin_user_default, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.gpio_pin_shutdown, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    async def run_gpio_check(self):
        """ """
        # Is this running on a Raspberry Pi with GPIO support installed?
        global gpio_available
        if not gpio_available:
            self.logger.warning("RPi GPIO control: GPIO not available.")
            return
        # Wait here if the switch is in wrong (= RPi-off) position.
        # Used to avoid accidental shutdown at startup.
        while not GPIO.input(self.gpio_pin_shutdown):
            # Low = active.
            await asyncio.sleep(0.8)
        # Start check loop.
        while True:
            # Wait.
            await asyncio.sleep(0.8)
            try:
                # Check for Raspberry Pi shutdown.
                if GPIO.input(self.gpio_pin_shutdown):
                    # High = inactive.
                    pass
                else:
                    # Low = active.
                    await asyncio.sleep(0.05)  # Check if stable, not bouncing.
                    if not GPIO.input(self.gpio_pin_shutdown):
                        await asyncio.sleep(0.05)  # Second check.
                        if not GPIO.input(self.gpio_pin_shutdown):
                            # Perform action.
                            self.raspberry_pi_shutdown()

                # Check for WURB user default mode.
                if GPIO.input(self.gpio_pin_user_default):
                    # High = inactive.
                    await asyncio.sleep(0.1)  # Check if stable, not bouncing.
                    if GPIO.input(self.gpio_pin_user_default):
                        if self.user_default_mode_state == True:
                            # Perform action.
                            self.send_wurb_rec_mode(rec_mode="user_default_on")
                            self.user_default_mode_state = False
                else:
                    # Low = active.
                    await asyncio.sleep(0.1)  # Check if stable, not bouncing.
                    if not GPIO.input(self.gpio_pin_user_default):
                        if self.user_default_mode_state == False:
                            # Perform action.
                            self.send_wurb_rec_mode(rec_mode="user_default_off")
                            self.user_default_mode_state = True
                    else:
                        self.user_default_mode_count += 1
            except:
                pass

    async def run_mouse_check(self):
        """ Check for mouse actions. """
        try:
            while True:
                await asyncio.sleep(0.2)

                if self.left_and_right_start and (
                    (time.time() - self.left_and_right_start)
                    >= self.left_and_right_time
                ):
                    if self.last_command != "left_and_right":
                        try:
                            self.logger.info(
                                "Mouse control: Left and right buttons pressed."
                            )
                            self.mouse_left_and_right_action()
                        except:
                            pass
                        self.last_command = "left_and_right"
                    #
                    continue
                #
                if self.left_start and (
                    (time.time() - self.left_start) >= self.left_time
                ):
                    if self.last_command != "left":
                        try:
                            self.logger.info("Mouse control: Left button pressed.")
                            self.mouse_left_action()
                        except:
                            pass
                        self.last_command = "left"
                    #
                    continue
                #
                if self.middle_start and (
                    (time.time() - self.middle_start) >= self.middle_time
                ):
                    if self.last_command != "middle":
                        try:
                            self.logger.info("Mouse control: Middle button pressed.")
                            self.mouse_middle_action()
                        except:
                            pass
                        self.last_command = "middle"
                    #
                    continue
                #
                if self.right_start and (
                    (time.time() - self.right_start) >= self.right_time
                ):
                    if self.last_command != "right":
                        try:
                            self.logger.info("Mouse control: Right button pressed.")
                            self.mouse_right_action()
                        except:
                            pass
                        self.last_command = "right"
                    #
                    continue

        except Exception as e:
            self.logger.error("Mouse control: Failed to check actions: " + str(e))

    def mouse_device_reader(self):
        """ Contains blocking io. Running inside executor. """
        # Open 'file' for reading mouse actions.
        try:
            with open("/dev/input/mice", "rb") as mice_file:
                # Loop and check mouse buttons.
                while True:
                    time.sleep(0.01)  # Should be short.

                    # The read command waits until next mouse action.
                    mouse_buffer = mice_file.read(3)  # Note: This is blocking.
                    buttons = mouse_buffer[0]
                    button_left = (buttons & 0x1) > 0
                    button_right = (buttons & 0x2) > 0
                    button_middle = (buttons & 0x4) > 0

                    # Left and right buttons.
                    if button_left and button_right:
                        if not self.left_and_right_start:
                            self.left_and_right_start = time.time()
                            self.left_start = False
                            self.middle_start = False
                            self.right_start = False
                        #
                        continue
                    # Left button.
                    if button_left:
                        if not self.left_start:
                            self.left_and_right_start = False
                            self.left_start = time.time()
                            self.middle_start = False
                            self.right_start = False
                        #
                        continue
                    # Middle button.
                    if button_middle:
                        if not self.middle_start:
                            self.left_and_right_start = False
                            self.left_start = False
                            self.middle_start = time.time()
                            self.right_start = False
                        #
                        continue
                    # Right button.
                    if button_right:
                        if not self.right_start:
                            self.left_and_right_start = False
                            self.left_start = False
                            self.middle_start = False
                            self.right_start = time.time()
                        #
                        continue
                    # No valid button pressed. Reset last command.
                    self.left_and_right_start = False
                    self.left_start = False
                    self.middle_start = False
                    self.right_start = False
                    self.last_command = None

        except Exception as e:
            self.logger.error("Mouse control: Failed to read mouse device: " + str(e))

    def logging_setup(self):
        """ """
        log = logging.getLogger("WURB_RPi")
        log.setLevel(logging.INFO)
        # Define rotation log files.
        dir_path = os.path.dirname(os.path.abspath(__file__))
        log_file_dir = "../wurb_files"
        log_file_name = "wurb_rpi_log.txt"
        log_file_path = pathlib.Path(dir_path, log_file_dir, log_file_name)
        if not pathlib.Path(dir_path, log_file_dir).exists():
            pathlib.Path(dir_path, log_file_dir).mkdir(parents=True)
        #
        log_handler = logging.handlers.RotatingFileHandler(
            str(log_file_path), maxBytes=128 * 1024, backupCount=4
        )
        log_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-10s : %(message)s ")
        )
        log_handler.setLevel(logging.DEBUG)
        log.addHandler(log_handler)


# === MAIN Asyncio ===
async def main():
    """ """
    control = ControlViaRaspberryPi()
    # GPIO.
    # await control.setup_gpio()
    # Run GPIO and mouse checkers as tasks.
    asyncio.create_task(control.run_gpio_check())
    asyncio.create_task(control.run_mouse_check())
    # The mouse device reader contains blocking io. Use executor.
    loop = asyncio.get_running_loop()
    mouse_device = loop.run_in_executor(None, control.mouse_device_reader)
    await mouse_device


if __name__ == "__main__":
    """ """
    asyncio.run(main(), debug=True)