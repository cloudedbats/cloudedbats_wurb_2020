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

            self.wurb_settings = None
            self.wurb_logging = None

        except Exception as e:
            print("Exception: ", e)

    async def startup(self):
        """ """
        try:
            self.ultrasound_devices = wurb_rec.UltrasoundDevices()
            self.wurb_recorder = wurb_rec.WurbRecorder()
            self.wurb_settings = wurb_rec.WurbSettings()
            self.wurb_logging = wurb_rec.WurbLogging()
            self.update_status_task = asyncio.create_task(self.update_status())

            # await self.ultrasound_devices.start_checking_devices()

        except Exception as e:
            print("Exception: ", e)

    async def shutdown(self):
        """ """
        try:
            if self.update_status_task:
                self.update_status_task.cancel()

            # await self.ultrasound_devices.stop_checking_devices()

            await self.wurb_recorder.stop_streaming(stop_immediate=True)
        except Exception as e:
            print("Exception: ", e)

    async def start_rec(self):
        """ """
        try:
            # await self.ultrasound_devices.stop_checking_devices()
            await self.ultrasound_devices.check_devices()

            device_name = self.ultrasound_devices.device_name
            sampling_freq_hz = self.ultrasound_devices.sampling_freq_hz
            if (len(device_name) > 1) and sampling_freq_hz > 180000:
                await self.wurb_recorder.set_device(device_name, sampling_freq_hz)
                await self.wurb_recorder.start_streaming()
            else:
                await self.wurb_recorder.set_rec_status(
                    "Failed: No valid microphone."
                )

                # await self.ultrasound_devices.start_checking_devices()

        except Exception as e:
            print("Exception: ", e)

    async def stop_rec(self):
        """ """
        try:
            await self.wurb_recorder.set_rec_status("")
            await self.wurb_recorder.stop_streaming(stop_immediate=True)
            await self.ultrasound_devices.reset_devices()

            # await self.ultrasound_devices.start_checking_devices()

        except Exception as e:
            print("Exception: ", e)

    async def get_notification_event(self):
        """ """
        try:
            if self.notification_event == None:
                self.notification_event = asyncio.Event()
            return self.notification_event
        except Exception as e:
            print("Exception: ", e)

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
            print("Exception: ", e)

    async def update_status(self):
        """ """
        print("DEBUG: update_status activated.")
        try:
            while True:
                device_notification = (
                    await self.ultrasound_devices.get_notification_event()
                )
                rec_notification = await self.wurb_recorder.get_notification_event()
                events = [
                    device_notification.wait(),
                    rec_notification.wait(),
                ]
                await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED)
                print("DEBUG: update_status released.")

                # Create a new event and release all from the old event.
                old_notification_event = self.notification_event
                self.notification_event = asyncio.Event()
                if old_notification_event:
                    old_notification_event.set()
        except Exception as e:
            print("DEBUG: update_status exception: ", e)
        finally:
            print("DEBUG: update_status terminated.")
