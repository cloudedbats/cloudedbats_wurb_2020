#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import os
import datetime
import pathlib


class WurbSettings(object):
    """ """

    def __init__(self):
        """ """
        self.settings_file_path = "wurb_rec_settings.txt"
        self.default_settings = None
        self.current_settings = None
        self.default_location = None
        self.current_location = None
        self.settings_event = None
        self.location_event = None
        self.os_raspbian = None
        #
        self.define_default_settings()
        self.current_settings = self.default_settings.copy()
        self.define_default_location()
        self.current_location = self.default_location.copy()
        self.load_settings_from_file()

    def define_default_settings(self):
        """ """
        self.default_settings = {
            "rec_mode": "rec-mode-manual",
            "file_directory": "recorded_files",
            "filename_prefix": "wurb",
            "detection_limit": "17.0",
            "detection_sensitivity": "-50",
            "detection_algorithm": "detection-simple",
            "scheduler_start_event": "on-sunset",
            "scheduler_start_adjust": "-15",
            "scheduler_stop_event": "off-sunset",
            "scheduler_stop_adjust": "15",
        }

    def define_default_location(self):
        """ """
        self.default_location = {
            "geo_source_option": "geo-not-used",
            "latitude_dd": "0.0",
            "longitude_dd": "0.0",
        }

    async def save_settings(self, settings_dict={}):
        """ """
        for key, value in settings_dict.items():
            if value is not None:
                self.current_settings[key] = value
        self.save_settings_to_file()
        # Create a new event and release all from the old event.
        old_settings_event = self.settings_event
        self.settings_event = asyncio.Event()
        if old_settings_event:
            old_settings_event.set()

    def get_setting(self, key=None):
        """ """
        if key:
            return self.current_settings.get(key, "")
        return ""

    async def get_settings(self, default=False):
        """ """
        if default:
            return self.default_settings
        return self.current_settings

    async def save_location(self, location_dict={}):
        """ """
        for key, value in location_dict.items():
            if value is not None:
                self.current_location[key] = value
        self.save_settings_to_file()
        # Create a new event and release all from the old event.
        old_location_event = self.location_event
        self.location_event = asyncio.Event()
        if old_location_event:
            old_location_event.set()

    async def get_location(self):
        """ """
        return self.current_location

    async def set_detector_time(self, posix_time_s):
        """ Only valid for Raspbian and user pi. """
        time_string = datetime.datetime.utcfromtimestamp(posix_time_s).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        print(time_string)

        try:
            # First check: OS Raspbian.
            if self.is_os_raspbian():
                time_string = datetime.datetime.utcfromtimestamp(posix_time_s).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                print(time_string)
                # Second check: User pi exists.
                os.system('cd /home/pi && sudo date --set "' + time_string + '"')
        except Exception as e:
            print("EXCEPTION: set_detector_time: ", e)

    async def rpi_control(self, command):
        """ Only valid for Raspbian and user pi. """
        # First check: OS Raspbian.
        if self.is_os_raspbian():
            # Second check: User pi exists.
            if command == "rpi_shutdown":
                os.system("cd /home/pi && sudo shutdown -h now")
            elif command == "rpi_reboot":
                os.system("cd /home/pi && sudo reboot")
            elif command == "rpi_update_sw":
                os.system("cd /home/pi/cloudedbats_wurb_2020 && git pull")
            else:
                print("DEBUG: Settings: rpi_control: Failed, command not valid:", command)
        else:
            print("DEBUG: Settings: rpi_control: Failed, not Raspbian.")

    async def get_settings_event(self):
        """ """
        try:
            if self.settings_event == None:
                self.settings_event = asyncio.Event()
            return self.settings_event
        except Exception as e:
            print("Exception: ", e)

    async def get_location_event(self):
        """ """
        try:
            if self.location_event == None:
                self.location_event = asyncio.Event()
            return self.location_event
        except Exception as e:
            print("Exception: ", e)

    def load_settings_from_file(self):
        """ Load from file. """
        settings_file_path = pathlib.Path(self.settings_file_path)
        if settings_file_path.exists():
            with settings_file_path.open("r") as settings_file:
                for row in settings_file:
                    if ":" in row:
                        row_parts = row.split(":")
                        key = row_parts[0].strip()
                        value = row_parts[1].strip()
                        if key in self.current_settings.keys():
                            self.current_settings[key] = value
                        if key in self.current_location.keys():
                            self.current_location[key] = value

    def save_settings_to_file(self):
        """ Save to file. """
        settings_file_path = pathlib.Path(self.settings_file_path)
        with settings_file_path.open("w") as settings_file:
            for key, value in self.current_location.items():
                settings_file.write(key + ": " + str(value) + "\n")
            for key, value in self.current_settings.items():
                settings_file.write(key + ": " + str(value) + "\n")

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
