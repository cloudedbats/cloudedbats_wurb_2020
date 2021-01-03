#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import time
from collections import deque
import sounddevice

import os
import wave

# CloudedBats.
import wurb_rec


class WurbRecManager(object):
    """ """

    def __init__(self):
        """ """
        try:
            self.rec_status = "Not started"
            self.notification_event = None
            self.ultrasound_devices = None
            self.wurb_recorder = None
            self.update_status_task = None

            self.wurb_rpi = None
            self.wurb_logging = None
            self.wurb_settings = None
            self.wurb_gps = None
            self.wurb_scheduler = None
            self.wurb_audiofeedback = None

        except Exception as e:
            print("Exception: ", e)

    async def startup(self):
        """ """
        try:
            self.wurb_logging = wurb_rec.WurbLogging(self)
            self.wurb_rpi = wurb_rec.WurbRaspberryPi(self)
            self.wurb_settings = wurb_rec.WurbSettings(self)
            self.wurb_audiofeedback = wurb_rec.WurbPitchShifting(self)
            self.ultrasound_devices = wurb_rec.UltrasoundDevices(self)
            self.wurb_recorder = wurb_rec.WurbRecorder(self)
            self.wurb_gps = wurb_rec.WurbGps(self)
            self.wurb_scheduler = wurb_rec.WurbScheduler(self)
            self.update_status_task = asyncio.create_task(self.update_status())
            await self.wurb_logging.startup()
            await self.wurb_settings.startup()
            # await self.wurb_scheduler.startup()
            # await self.wurb_audiofeedback.startup()
            # Logging.
            message = "Detector started."
            self.wurb_logging.info(message, short_message=message)
        except Exception as e:
            # Logging error.
            message = "Manager: startup: " + str(e)
            self.wurb_logging.error(message, short_message=message)

    async def shutdown(self):
        """ """
        try:
            await self.wurb_recorder.stop_streaming(stop_immediate=True)

            if self.wurb_audiofeedback:
                await self.wurb_audiofeedback.shutdown()
                self.wurb_audiofeedback = None
            if self.wurb_gps:
                await self.wurb_gps.shutdown()
                self.wurb_gps = None
            if self.wurb_scheduler:
                await self.wurb_scheduler.shutdown()
                self.wurb_scheduler = None
            if self.wurb_settings:
                await self.wurb_settings.shutdown()
                self.wurb_settings = None
            if self.update_status_task:
                self.update_status_task.cancel()
                self.update_status_task = None
            if self.wurb_logging:
                await self.wurb_logging.shutdown()
                self.wurb_logging = None
        except Exception as e:
            # Logging error.
            message = "Manager: shutdown:" + str(e)
            self.wurb_logging.error(message, short_message=message)

    async def start_rec(self):
        """ """
        try:
            rec_status = await self.wurb_recorder.get_rec_status()
            if rec_status == "Recording.":
                return  # Already running.

            # await self.ultrasound_devices.stop_checking_devices()
            await self.ultrasound_devices.check_devices()

            device_name = self.ultrasound_devices.device_name
            sampling_freq_hz = self.ultrasound_devices.sampling_freq_hz
            if (len(device_name) > 1) and sampling_freq_hz > 0:
                # Audio feedback.
                await self.wurb_audiofeedback.startup()
                await self.wurb_audiofeedback.setup(sampling_freq=sampling_freq_hz)
                # Rec.
                await self.wurb_recorder.set_device(device_name, sampling_freq_hz)
                await self.wurb_recorder.start_streaming()
                # Logging.
                message = "Rec. started."
                self.wurb_logging.info(message, short_message=message)
            else:
                await self.wurb_recorder.set_rec_status("Failed: No valid microphone.")
                # Logging.
                message = "Failed: No valid microphone."
                self.wurb_logging.info(message, short_message=message)
        except Exception as e:
            # Logging error.
            message = "Manager: start_rec: " + str(e)
            self.wurb_logging.error(message, short_message=message)

    async def stop_rec(self):
        """ """
        try:
            rec_status = await self.wurb_recorder.get_rec_status()
            if rec_status == "Recording.":
                # Logging.
                message = "Rec. stopped."
                self.wurb_logging.info(message, short_message=message)

            # Audio feedback.
            await self.wurb_audiofeedback.shutdown()
            # Rec.
            await self.wurb_recorder.set_rec_status("")
            await self.wurb_recorder.stop_streaming(stop_immediate=True)
            await self.ultrasound_devices.reset_devices()
        except Exception as e:
            # Logging error.
            message = "Manager: start_rec: " + str(e)
            self.wurb_logging.error(message, short_message=message)

    async def restart_rec(self):
        """ """
        try:
            rec_status = await self.wurb_recorder.get_rec_status()
            if rec_status == "Recording.":
                # Logging.
                message = "Rec. restart initiated."
                self.wurb_logging.info(message, short_message=message)
                await self.stop_rec()
                await asyncio.sleep(1.0)
                await self.start_rec()
        except Exception as e:
            # Logging error.
            message = "Manager: start_rec: " + str(e)
            self.wurb_logging.error(message, short_message=message)

    async def get_notification_event(self):
        """ """
        try:
            if self.notification_event == None:
                self.notification_event = asyncio.Event()
            return self.notification_event
        except Exception as e:
            # Logging error.
            message = "Manager: start_rec: " + str(e)
            self.wurb_logging.error(message, short_message=message)

    async def get_status_dict(self):
        """ """
        try:
            status_dict = {
                "rec_status": self.wurb_recorder.rec_status,
                "device_name": self.ultrasound_devices.device_name,
                "sample_rate": str(self.ultrasound_devices.sampling_freq_hz),
            }
            return status_dict
        except Exception as e:
            # Logging error.
            message = "Manager: start_rec: " + str(e)
            self.wurb_logging.error(message, short_message=message)

    async def update_status(self):
        """ """
        try:
            while True:
                try:
                    device_notification = (
                        await self.ultrasound_devices.get_notification_event()
                    )
                    rec_notification = await self.wurb_recorder.get_notification_event()
                    events = [
                        device_notification.wait(),
                        rec_notification.wait(),
                    ]
                    await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED)

                    # Create a new event and release all from the old event.
                    old_notification_event = self.notification_event
                    self.notification_event = asyncio.Event()
                    if old_notification_event:
                        old_notification_event.set()
                except asyncio.CancelledError:
                    exit
        except Exception as e:
            # Logging error.
            message = "Manager: start_rec: " + str(e)
            self.wurb_logging.error(message, short_message=message)
        finally:
            # Logging error.
            message = "Manager update status terminated."
            self.wurb_logging.debug(message=message)

    async def manual_trigger(self):
        """ """
        print("TODO: manual_trigger")
