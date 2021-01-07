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

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.wurb_logging = wurb_manager.wurb_logging
        self.wurb_rpi = wurb_manager.wurb_rpi
        self.default_settings = None
        self.current_settings = None
        self.default_location = None
        self.current_location = None
        self.settings_event = None
        self.location_event = None
        self.latlong_event = None
        # self.os_raspbian = None
        #
        self.settings_file_name = "wurb_rec_settings.txt"
        self.settings_user_file_name = "wurb_rec_settings_user.txt"
        self.settings_startup_file_name = "wurb_rec_settings_startup.txt"
        self.settings_dir_path = self.wurb_rpi.get_settings_dir_path()
        #
        self.define_default_settings()
        self.current_settings = self.default_settings.copy()
        self.define_default_location()
        self.current_location = self.default_location.copy()
        # Select settings for startup.
        self.load_settings_from_file()
        startup_option = self.current_settings.get("startup_option", "")
        if startup_option == "startup-settings":
            self.load_settings_from_file(
                settings_file_name=self.settings_startup_file_name
            )

    def define_default_settings(self):
        """ """
        self.default_settings = {
            "rec_mode": "mode-off",
            "file_directory": "Station-1",
            "date_in_file_directory": "date-post-before",
            "filename_prefix": "wurb",
            "detection_limit_khz": "17.0",
            "detection_sensitivity_dbfs": "-50",
            "detection_algorithm": "detection-simple",
            "rec_length_s": "6",
            "rec_type": "FS",
            "feedback_filter_low_khz": "15",
            "feedback_filter_high_khz": "150",
            "startup_option": "as-last-session",
            "scheduler_start_event": "on-sunset",
            "scheduler_start_adjust": "-15",
            "scheduler_stop_event": "off-sunrise",
            "scheduler_stop_adjust": "15",
            "scheduler_post_action": "post-none",
            "scheduler_post_action_delay": "5",
        }

    def define_default_location(self):
        """ """
        self.default_location = {
            "geo_source": "geo-not-used",
            "latitude_dd": "0.0",
            "longitude_dd": "0.0",
            "manual_latitude_dd": "0.0",
            "manual_longitude_dd": "0.0",
            "last_gps_latitude_dd": "0.0",
            "last_gps_longitude_dd": "0.0",
        }

    async def startup(self):
        """ """
        # GPS.
        geo_source = self.current_location["geo_source"]
        if geo_source in ["geo-gps", "geo-gps-or-manual", "geo-last-gps-or-manual"]:
            await self.save_latlong(0.0, 0.0)
            await self.wurb_manager.wurb_gps.startup()
        else:
            await self.wurb_manager.wurb_gps.shutdown()
        # Rec. mode. Scheduler, rec-on or rec-off.
        rec_mode = self.current_settings["rec_mode"]
        if rec_mode in [
            "mode-off",
            "mode-on",
            "mode-auto",
            "mode-manual",
            "mode-scheduler-on",
            "mode-scheduler-auto",
        ]:
            await self.wurb_manager.wurb_scheduler.startup()
        else:
            await self.wurb_manager.wurb_scheduler.shutdown()

    async def shutdown(self):
        """ """
        # GPS.
        await self.wurb_manager.wurb_gps.shutdown()

    async def save_settings(self, settings_dict={}, settings_type=None):
        """ """
        for key, value in settings_dict.items():
            if value is not None:
                # Clean up filename_prefix.
                if key == "filename_prefix":
                    value = value.replace(" ", "-")
                    value = value.replace("_", "-")
                self.current_settings[key] = value
        self.save_settings_to_file()
        if settings_type is not None:
            if settings_type == "user-default":
                self.save_settings_to_file(
                    settings_file_name=self.settings_user_file_name,
                    skip_keys=["startup_option"],
                )
            if settings_type == "startup":
                self.save_settings_to_file(
                    settings_file_name=self.settings_startup_file_name,
                    skip_keys=["startup_option"],
                )

        # Active modes.
        rec_mode = self.current_settings["rec_mode"]
        if rec_mode in ["mode-on", "mode-auto", "mode-manual"]:
            await self.wurb_manager.start_rec()
        if rec_mode in ["mode-off"]:
            await self.wurb_manager.stop_rec()
        # Passive modes, and monitoring active.
        if rec_mode in [
            "mode-off",
            "mode-on",
            "mode-auto",
            "mode-manual",
            "mode-scheduler-on",
            "mode-scheduler-auto",
        ]:
            await self.wurb_manager.wurb_scheduler.startup()
        else:
            await self.wurb_manager.wurb_scheduler.shutdown()

        # Create a new event and release all from the old event.
        old_settings_event = self.settings_event
        self.settings_event = asyncio.Event()
        if old_settings_event:
            old_settings_event.set()

        # Logging.
        message = "Settings saved."
        self.wurb_logging.info(message, short_message=message)

        # Restart recording. Needed for some settings.
        await self.wurb_manager.restart_rec()

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

        geo_source = self.current_location["geo_source"]
        # Manual.
        if geo_source == "geo-manual":
            self.current_location["latitude_dd"] = self.current_location[
                "manual_latitude_dd"
            ]
            self.current_location["longitude_dd"] = self.current_location[
                "manual_longitude_dd"
            ]
        # GPS.
        if geo_source in ["geo-gps", "geo-gps-or-manual", "geo-last-gps-or-manual"]:
            self.current_location["latitude_dd"] = 0.0
            self.current_location["longitude_dd"] = 0.0

        self.save_settings_to_file()
        # Create a new event and release all from the old event.
        old_location_event = self.location_event
        self.location_event = asyncio.Event()
        if old_location_event:
            old_location_event.set()

        # GPS.
        if geo_source in ["geo-gps", "geo-gps-or-manual", "geo-last-gps-or-manual"]:
            await self.wurb_manager.wurb_gps.startup()
        else:
            await self.wurb_manager.wurb_gps.shutdown()

    async def save_latlong(self, latitude_dd, longitude_dd):
        """ """
        geo_source = self.current_location["geo_source"]
        # Manual.
        if geo_source in ["geo-gps", "geo-gps-or-manual", "geo-last-gps-or-manual"]:
            self.current_location["latitude_dd"] = latitude_dd
            self.current_location["longitude_dd"] = longitude_dd
            if (latitude_dd > 0.0) and (longitude_dd > 0.0):
                self.current_location["last_gps_latitude_dd"] = latitude_dd
                self.current_location["last_gps_longitude_dd"] = longitude_dd
        self.save_settings_to_file()
        # Create a new event and release all from the old event.
        old_latlong_event = self.latlong_event
        self.latlong_event = asyncio.Event()
        if old_latlong_event:
            old_latlong_event.set()

    def get_valid_location(self):
        """ """
        latitude = 0.0
        longitude = 0.0
        location_dict = self.get_location_dict()
        latitude = float(location_dict.get("latitude_dd", "0.0"))
        longitude = float(location_dict.get("longitude_dd", "0.0"))
        manual_latitude = float(location_dict.get("manual_latitude_dd", "0.0"))
        manual_longitude = float(location_dict.get("manual_longitude_dd", "0.0"))
        last_gps_latitude = float(location_dict.get("last_gps_latitude_dd", "0.0"))
        last_gps_longitude = float(location_dict.get("last_gps_longitude_dd", "0.0"))
        geo_source = location_dict.get("geo_source", "")
        if (latitude == 0.0) or (longitude == 0.0):
            if geo_source in ["geo-gps-or-manual"]:
                latitude = manual_latitude
                longitude = manual_longitude
        if (latitude == 0.0) or (longitude == 0.0):
            if geo_source in ["geo-last-gps-or-manual"]:
                latitude = last_gps_latitude
                longitude = last_gps_longitude
                if (latitude == 0.0) or (longitude == 0.0):
                    latitude = manual_latitude
                    longitude = manual_longitude
        # Result.
        return latitude, longitude

    def get_location_status(self):
        """ """
        lat, long = self.get_valid_location()
        if (lat == 0.0) and (long == 0.0):
            return "Not valid. Scheduler not started."
        else:
            geo_source = self.get_location_dict().get("geo_source", "")
            if geo_source == "geo-gps":
                if self.wurb_manager.wurb_gps:
                    no_of_satellites = (
                        self.wurb_manager.wurb_gps.get_number_of_satellites()
                    )
                    return "Number of satellites: " + str(no_of_satellites)
            else:
                return "Lat: " + str(lat) + " Long: " + str(long)

    def get_location_dict(self):
        """ """
        return self.current_location

    async def get_location(self):
        """ """
        return self.current_location

    async def get_settings_event(self):
        """ """
        try:
            if self.settings_event == None:
                self.settings_event = asyncio.Event()
            return self.settings_event
        except Exception as e:
            # Logging error.
            message = "Logging: get_settings_event: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def get_location_event(self):
        """ """
        try:
            if self.location_event == None:
                self.location_event = asyncio.Event()
            return self.location_event
        except Exception as e:
            # Logging error.
            message = "Logging: get_location_event: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def get_latlong_event(self):
        """ """
        try:
            if self.latlong_event == None:
                self.latlong_event = asyncio.Event()
            return self.latlong_event
        except Exception as e:
            # Logging error.
            message = "Logging: get_latlong_event: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def load_settings(self, settings_type):
        """ """
        # Keep startup_option.
        startup_option = self.current_settings.get("startup_option", "")
        if settings_type == "user-default":
            self.load_settings_from_file(
                settings_file_name=self.settings_user_file_name
            )
        elif settings_type == "start-up":
            self.load_settings_from_file(
                settings_file_name=self.settings_startup_file_name
            )
        elif settings_type == "factory-default":
            self.current_settings = self.default_settings.copy()
            self.current_location = self.default_location.copy()
        # Keep startup_option.
        self.current_settings["startup_option"] = startup_option
        # Create a new event and release all from the old event.
        old_settings_event = self.settings_event
        self.settings_event = asyncio.Event()
        if old_settings_event:
            old_settings_event.set()
        # Create a new event and release all from the old event.
        old_location_event = self.location_event
        self.location_event = asyncio.Event()
        if old_location_event:
            old_location_event.set()

    def load_settings_from_file(self, settings_file_name=None):
        """ Load from file. """
        if settings_file_name is None:
            settings_file_name = self.settings_file_name
        settings_file_path = pathlib.Path(self.settings_dir_path, settings_file_name)
        if settings_file_path.exists():
            with settings_file_path.open("r") as settings_file:
                for row in settings_file:
                    if len(row) > 0:
                        if row[0] == "#":
                            continue
                    if ":" in row:
                        row_parts = row.split(":")
                        key = row_parts[0].strip()
                        value = row_parts[1].strip()
                        if key in self.default_settings.keys():
                            self.current_settings[key] = value
                        if key in self.default_location.keys():
                            self.current_location[key] = value

    def save_settings_to_file(self, settings_file_name=None, skip_keys=[]):
        """ Save to file. """
        if settings_file_name is None:
            settings_file_name = self.settings_file_name
        settings_file_path = pathlib.Path(self.settings_dir_path, settings_file_name)
        with settings_file_path.open("w") as settings_file:
            settings_file.write("# CloudedBats, http://cloudedbats.org" + "\n")
            settings_file.write("# Settings for the WURB bat detector." + "\n")
            settings_file.write(
                "# Saved: "
                + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                + "\n"
            )
            settings_file.write("# " + "\n")
            #
            for key, value in self.current_location.items():
                if key not in skip_keys:
                    settings_file.write(key + ": " + str(value) + "\n")
            for key, value in self.current_settings.items():
                if key not in skip_keys:
                    settings_file.write(key + ": " + str(value) + "\n")
