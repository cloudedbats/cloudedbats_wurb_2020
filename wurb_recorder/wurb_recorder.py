#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import sounddevice


class UltrasoundDevices(object):
    """ """

    def __init__(self):
        """ """
        # Ultrasound microphones supported by default:
        # - Pettersson: M500-384, u384, u256.
        # - Dodotronic: UltraMic 192K, 200K, 250K, 384K.
        self.name_part_list = ["Pettersson", "UltraMic"]
        self.device_name = "-"
        self.sampling_freq_hz = 0
        self.check_interval_s = 1.0
        #

    def get_connected_device(self):
        """ """
        return self.device_name, self.sampling_freq_hz

    async def get_device_when_changed(self):
        device_name = self.device_name
        sampling_freq_hz = self.sampling_freq_hz
        print("DEBUG-3:", device_name)
        while True:
            if (self.device_name == device_name) and (
                self.sampling_freq_hz == sampling_freq_hz
            ):
                await asyncio.sleep(self.check_interval_s)
            else:
                print("DEBUG-4:", self.device_name)
                return self.device_name, self.sampling_freq_hz

    async def check_connected_devices(self):
        while True:
            # Refresh device list.
            sounddevice._terminate()
            sounddevice._initialize()
            device_dict = None
            device_name = "-"
            sampling_freq_hz = 0
            for device_name_part in self.name_part_list:
                try:
                    device_dict = sounddevice.query_devices(device=device_name_part)
                    if device_dict:
                        device_name = device_dict["name"]
                        sampling_freq_hz = int(device_dict["default_samplerate"])
                    break
                except:
                    pass
            if (self.device_name == device_name) and (
                self.sampling_freq_hz == sampling_freq_hz
            ):
                await asyncio.sleep(self.check_interval_s)
                # print('DEBUG-1:', device_name)
            else:
                self.device_name = device_name
                self.sampling_freq_hz = sampling_freq_hz
                # print('DEBUG-2:', device_name)
