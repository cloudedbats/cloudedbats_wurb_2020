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
        self.latitude_dd = None
        self.longitude_dd = None
        self.os_raspbian = None
        self.default_settings = None
        self.current_settings = None
        #
        self.setup_default_settings()
        self.current_settings = self.default_settings.copy()
        self.load_settings()

    def setup_default_settings(self):
        """ """
        self.default_settings = {
            "geo_source_option": "geo-default",
            "geo_latitude": "56.7890",
            "geo_longitude": "12.3456",
            "rec_mode": "rec-mode-manual",
            "filename_prefix": "wurb",
            "default_latitude": "56.78",
            "default_longitude": "12.34",
            "detection_limit": "17.0",
            "detection_sensitivity": "-50",
            "file_directory": "recorded_files",
            "detection_algorithm": "detection-simple",
            "scheduler_start_event": "on-sunset",
            "scheduler_start_adjust": "-15",
            "scheduler_stop_event": "off-sunset",
            "scheduler_stop_adjust": "15",
        }

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

    def load_settings(self):
        """ """
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

    def save_settings(self):
        """ """
        settings_file_path = pathlib.Path(self.settings_file_path)
        with settings_file_path.open("w") as settings_file:
            for key, value in self.current_settings.items():
                settings_file.write(key + ": " + str(value) + "\n")

    async def update_settings(self, settings_dict={}):
        """ """
        for key, value in settings_dict.items():
            self.current_settings[key] = value
        self.save_settings()

    async def set_location(self, latitude_dd, longitude_dd):
        """ """
        self.current_settings["geo_latitude"] = str(latitude_dd)
        self.current_settings["geo_longitude"] = str(longitude_dd)

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
