#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import datetime
import wurb_rec


class WurbScheduler(object):
    """ """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.wurb_settings = wurb_manager.wurb_settings
        self.wurb_logging = wurb_manager.wurb_logging
        self.main_loop_task = None
        self.solartime = wurb_rec.SolarTime()
        self.solartime_lookup_dict = {}
        self.solartime_last_used_key = ""
        # For logging.
        self.last_used_mode = ""
        self.current_mode = ""
        self.last_used_scheduler_state = ""
        self.current_scheduler_state = ""
        # Config.
        self.main_loop_interval_s = 10  # Unit: sec.
        # Translate user modes.
        self.user_mode_for_humans = {
            "mode-off": "Microphone off.",
            "mode-on": "Rec continuously.",
            "mode-auto": "Auto detection.",
            "mode-manual": "Manual triggering.",
            "mode-scheduler-on": "By scheduler - Rec on.",
            "mode-scheduler-auto": "By scheduler - Auto.",
        }

    async def startup(self):
        """ """
        if not self.main_loop_task:
            self.main_loop_task = asyncio.create_task(self.main_loop())
        #
        await self.update_status()

    async def shutdown(self):
        """ """
        if self.main_loop_task:
            self.main_loop_task.cancel()
            self.main_loop_task = None

    async def main_loop(self):
        """ """
        try:
            while True:
                try:
                    await asyncio.sleep(self.main_loop_interval_s)
                    await self.update_status()
                except asyncio.CancelledError:
                    break
        except Exception as e:
            # Logging error.
            message = "Scheduler main loop: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)
        finally:
            # Logging error.
            message = "Scheduler main loop terminated."
            self.wurb_manager.wurb_logging.debug(message)

    async def update_status(self):
        """ """
        try:
            rec_mode = self.wurb_settings.get_setting("rec_mode")
            self.current_mode = rec_mode
            if rec_mode in ["mode-on", "mode-auto", "mode-manual"]:
                self.last_used_scheduler_state = ""
                self.current_scheduler_state = ""
                await self.wurb_manager.start_rec()
            if rec_mode in ["mode-off"]:
                self.last_used_scheduler_state = ""
                self.current_scheduler_state = ""
                await self.wurb_manager.stop_rec()
            if rec_mode in ["mode-scheduler-on", "mode-scheduler-auto"]:
                await self.check_scheduler()
            # Logging of changes in state.
            if self.current_mode != self.last_used_mode:
                mode_humans = self.user_mode_for_humans.get(self.current_mode, "Undefined")
                message = "Mode: " + mode_humans
                self.wurb_manager.wurb_logging.info(message, short_message=message)
                self.last_used_mode = self.current_mode
            if self.current_scheduler_state != self.last_used_scheduler_state:
                message = "Scheduler state: " + self.current_scheduler_state
                self.wurb_manager.wurb_logging.info(message, short_message=message)
                self.last_used_scheduler_state = self.current_scheduler_state
        except Exception as e:
            # Logging error.
            message = "Scheduler update status: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def check_scheduler(self):
        """ """
        # Start/stop time.
        start_event_local, stop_event_local = await self.calculate_start_stop()
        if (start_event_local is None) or (stop_event_local is None):
            # Can't calculate start or stop.
            self.current_scheduler_state = "Time or position is missing."
            await self.wurb_manager.stop_rec()
            return

        # Evaluate action.
        now_local = datetime.datetime.now().astimezone()
        if start_event_local == stop_event_local:
            # Always off.
            await self.wurb_manager.stop_rec()
        if start_event_local < stop_event_local:
            # Same day.
            if (start_event_local < now_local) and (now_local < stop_event_local):
                self.current_scheduler_state = "Recording active."
                await self.wurb_manager.start_rec()
            else:
                self.current_scheduler_state = "Recording not active."
                await self.wurb_manager.stop_rec()
        else:
            # Different days.
            start_local_new = start_event_local
            stop_local_new = stop_event_local
            # Prepare.
            if now_local < stop_event_local:
                start_local_new = start_event_local - datetime.timedelta(days=1)
            if now_local > stop_event_local:
                stop_local_new = stop_event_local + datetime.timedelta(days=1)
            # Check.
            if (start_local_new < now_local) and (now_local < stop_local_new):
                self.current_scheduler_state = "Recording active."
                await self.wurb_manager.start_rec()
            else:
                self.current_scheduler_state = "Recording not active."
                await self.wurb_manager.stop_rec()

    async def calculate_start_stop(self):
        """ """
        # Get settings.
        start_event = self.wurb_settings.get_setting("scheduler_start_event")
        start_event_adjust = self.wurb_settings.get_setting("scheduler_start_adjust")
        stop_event = self.wurb_settings.get_setting("scheduler_stop_event")
        stop_event_adjust = self.wurb_settings.get_setting("scheduler_stop_adjust")
        # Get sunset, sunrise, etc.
        solartime_dict = await self.get_solartime_data()
        # Start event.
        if start_event in ["on-sunset", "on-dusk", "on-dawn", "on-sunrise"]:
            if not solartime_dict:
                # Lat/long needed to calculate start.
                return (None, None)
            start_event = start_event.replace("on-", "")
            start_event_utc = solartime_dict.get(start_event, None)
            start_event_local = start_event_utc.astimezone()
        else:
            start_event = start_event.replace("on-", "")
            start_event_hour = int(float(start_event))
            start_event_local = datetime.datetime.now().astimezone()
            start_event_local = start_event_local.replace(
                hour=start_event_hour, minute=0, second=0, microsecond=0
            )
        # Stop event.
        if stop_event in ["off-sunset", "off-dusk", "off-dawn", "off-sunrise"]:
            if not solartime_dict:
                # Lat/long needed to calculate stop.
                return (None, None)
            stop_event = stop_event.replace("off-", "")
            stop_event_utc = solartime_dict.get(stop_event, None)
            stop_event_local = stop_event_utc.astimezone()
        else:
            stop_event = stop_event.replace("off-", "")
            stop_event_hour = int(float(stop_event))
            stop_event_local = datetime.datetime.now().astimezone()
            stop_event_local = stop_event_local.replace(
                hour=stop_event_hour, minute=0, second=0, microsecond=0
            )
        # Adjust time.
        start_event_local += datetime.timedelta(minutes=int(float(start_event_adjust)))
        stop_event_local += datetime.timedelta(minutes=int(float(stop_event_adjust)))

        return (start_event_local, stop_event_local)

    async def get_solartime_data(self, print_new=True):
        """ """
        latitude, longitude = self.wurb_settings.get_valid_location()
        if (latitude == 0.0) or (longitude == 0.0):
            # No lat/long found.
            return None

        date_local = datetime.datetime.now().date()
        latitude_short = round(latitude, 2)
        longitude_short = round(longitude, 2)
        solartime_dict = {}
        lookup_key = (
            str(date_local) + "<->" + str(latitude_short) + "<->" + str(longitude_short)
        )
        if lookup_key in self.solartime_lookup_dict:
            solartime_dict = self.solartime_lookup_dict.get(lookup_key, {})
        else:
            solartime_dict = self.solartime.sun_utc(date_local, latitude, longitude)
            self.solartime_lookup_dict[lookup_key] = solartime_dict

        if lookup_key != self.solartime_last_used_key:
            self.solartime_last_used_key = lookup_key
            # Logging.
            sunset_utc = solartime_dict.get("sunset", None)
            dusk_utc = solartime_dict.get("dusk", None)
            dawn_utc = solartime_dict.get("dawn", None)
            sunrise_utc = solartime_dict.get("sunrise", None)
            if sunset_utc and dusk_utc and dawn_utc and sunrise_utc:
                if print_new:
                    sunset_local = sunset_utc.astimezone()
                    dusk_local = dusk_utc.astimezone()
                    dawn_local = dawn_utc.astimezone()
                    sunrise_local = sunrise_utc.astimezone()
                    message = "Solartime recalculated: "
                    message += " Sunset: " + sunset_local.strftime("%H:%M:%S")
                    message += " Dusk: " + dusk_local.strftime("%H:%M:%S")
                    message += " Dawn: " + dawn_local.strftime("%H:%M:%S")
                    message += " Sunrise: " + sunrise_local.strftime("%H:%M:%S")
                    self.wurb_manager.wurb_logging.info(message, short_message=message)
            else:
                return None

        return solartime_dict
