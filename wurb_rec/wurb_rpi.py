#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import os
import datetime
import pathlib


class WurbRaspberryPi(object):
    """ """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.os_raspbian = None

    async def rpi_control(self, command):
        """ """
        # First check: OS Raspbian. Only valid for Raspbian and user pi.
        if self.is_os_raspbian():
            # Select command.
            if command == "rpi_shutdown":
                await self.rpi_shutdown()
            elif command == "rpi_reboot":
                await self.rpi_reboot()
            elif command == "rpi_sd_to_usb":
                await self.rpi_sd_to_usb()
            # elif command == "rpi_clear_sd_ok":
            elif command == "rpi_clear_sd":
                await self.rpi_clear_sd()
            elif command == "rpi_status":
                await self.rpi_status()
            elif command == "rpi_update_sw":
                await self.rpi_update_sw
            else:
                # Logging.
                message = "Detector command failed. Not  valid command."
                self.wurb_manager.wurb_logging.error(message, short_message=message)
        else:
            # Logging.
            message = "Detector command failed, not Raspbian OS."
            self.wurb_manager.wurb_logging.warning(message, short_message=message)

    async def set_detector_time(self, posix_time_s, cmd_source=""):
        """ Only valid for Raspbian and user pi. """
        try:
            local_datetime = datetime.datetime.fromtimestamp(posix_time_s)
            # utc_datetime = datetime.datetime.utcfromtimestamp(posix_time_s)
            # local_datetime = utc_datetime.replace(
            #     tzinfo=datetime.timezone.utc
            # ).astimezone(tz=None)
            time_string = local_datetime.strftime("%Y-%m-%d %H:%M:%S")
            print(time_string)
            # Logging.
            message = "Detector time update: " + time_string
            if cmd_source:
                message += " (" + cmd_source + ")."
            self.wurb_manager.wurb_logging.info(message, short_message=message)
            # First check: OS Raspbian.
            if self.is_os_raspbian():
                # Second check: User pi exists. Perform: "date --set".
                os.system('cd /home/pi && sudo date --set "' + time_string + '"')
            else:
                # Logging.
                message = "Detector time update failed, not Raspbian OS."
                self.wurb_manager.wurb_logging.warning(message, short_message=message)
        except Exception as e:
            print("EXCEPTION: set_detector_time: ", e)

    def get_settings_dir_path(self):
        """ """
        rpi_dir_path = "/home/pi/"  # For RPi SD card with user 'pi'.
        # Default for not Raspberry Pi.
        dir_path = pathlib.Path("wurb_files")
        if pathlib.Path(rpi_dir_path).exists():
            dir_path = pathlib.Path(rpi_dir_path, "wurb_files")
        # Create directories.
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
        return dir_path

    def get_wavefile_target_dir_path(self):
        """ """
        file_directory = self.wurb_manager.wurb_settings.get_setting("file_directory")
        target_rpi_media_path = "/media/pi/"  # For RPi USB.
        target_rpi_internal_path = "/home/pi/"  # For RPi SD card with user 'pi'.
        dir_path = None

        # hdd = psutil.disk_usage(str(dir_path))
        # total_disk = hdd.total / (2**20)
        # used_disk = hdd.used / (2**20)
        # free_disk = hdd.free / (2**20)
        # percent_disk = hdd.percent
        # print("Total disk: ", total_disk, "MB")
        # print("Used disk: ", used_disk, "MB")
        # print("Free disk: ", free_disk, "MB")
        # print("Percent: ", percent_disk, "%")

        # Check mounted USB memory sticks. At least 20 MB left.
        rpi_media_path = pathlib.Path(target_rpi_media_path)
        if rpi_media_path.exists():
            for usb_stick_name in sorted(list(rpi_media_path.iterdir())):
                usb_stick_path = pathlib.Path(rpi_media_path, usb_stick_name)
                # Directory may exist even when no USB attached.
                if usb_stick_path.is_mount():
                    hdd = psutil.disk_usage(str(usb_stick_path))
                    free_disk = hdd.free / (2 ** 20)  # To MB.
                    if free_disk >= 20.0:  # 20 MB.
                        return pathlib.Path(usb_stick_path, file_directory)

        # Check internal SD card. At least 500 MB left.
        rpi_internal_path = pathlib.Path(target_rpi_internal_path)
        if rpi_internal_path.exists():
            hdd = psutil.disk_usage(str(rpi_internal_path))
            free_disk = hdd.free / (2 ** 20)  # To MB.
            if free_disk >= 500.0:  # 500 MB.
                return pathlib.Path(rpi_internal_path, "wurb_files", file_directory)
            else:
                print("ERROR: Not enough space left on RPi SD card.")
                return None  # Not enough space left on RPi SD card.

        # Default for not Raspberry Pi.
        dir_path = pathlib.Path("wurb_files", file_directory)
        return dir_path

    def is_os_raspbian(self):
        """ Check OS version for Raspberry Pi. """
        if self.os_raspbian is not None:
            return self.os_raspbian
        else:
            try:
                os_version_path = pathlib.Path("/etc/os-release")
                if os_version_path.exists():
                    with os_version_path.open("r") as os_file:
                        os_file_content = os_file.read()
                        print("Content of /etc/os-release: ", os_file_content)
                        if "raspbian" in os_file_content:
                            self.os_raspbian = True
                        else:
                            self.os_raspbian = False
                else:
                    self.os_raspbian = False
            except Exception as e:
                print("EXCEPTION: is_os_raspbian: ", e)
        #
        return self.os_raspbian

    async def rpi_shutdown(self):
        """ """
        # Logging.
        message = "Raspberry Pi command 'Shutdown' is activated."
        self.wurb_manager.wurb_logging.info(message, short_message=message)
        await asyncio.sleep(1.0)
        #
        os.system("cd /home/pi && sudo shutdown -h now")

    async def rpi_reboot(self):
        """ """
        # Logging.
        message = "Raspberry Pi command 'Reboot' is activated."
        self.wurb_manager.wurb_logging.info(message, short_message=message)
        await asyncio.sleep(1.0)
        #
        os.system("cd /home/pi && sudo reboot")

    async def rpi_sd_to_usb(self):
        """ """
        # Logging.
        message = "Raspberry Pi command 'Copy SD to USB' is not implemented."
        self.wurb_manager.wurb_logging.info(message, short_message=message)

    async def rpi_clear_sd(self):
        """ """
        # Logging.
        message = "Raspberry Pi command 'Clear SD card' is not implemented."
        self.wurb_manager.wurb_logging.info(message, short_message=message)

    async def rpi_status(self):
        """ """
        # Logging.
        message = "Raspberry Pi command 'Detector status' is not implemented."
        self.wurb_manager.wurb_logging.info(message, short_message=message)
 
    async def rpi_update_sw(self):
        """ """
        # Logging.
        message = "Raspberry Pi command 'Software update' is activated."
        self.wurb_manager.wurb_logging.info(message, short_message=message)
        asyncio.sleep(1.0)
        #
        command_string = "cd /home/pi/cloudedbats_wurb_2020"
        command_string += " && git pull"
        command_string += " && source venv/bin/activate"
        command_string += " && pip install -r requirements.txt "
        await asyncio.sleep(1.0)
        #
        os.system(command_string)

        # Logging.
        message = "Software is updated."
        self.wurb_manager.wurb_logging.info(message, short_message=message)
        asyncio.sleep(1.0)
        #
