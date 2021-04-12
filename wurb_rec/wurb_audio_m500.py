#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import time
import numpy
import array
import logging

# CloudedBats.
import wurb_rec


class PetterssonM500():
    """ """

    def __init__(self, data_queue=None, direct_target=None):
        """ """
        self.data_queue = data_queue
        self.direct_target = direct_target
        self.card_index = None
        self.buffer_size = None
        # M500.
        self.device_name = "Pettersson M500 (500kHz)"
        self.sampling_freq_hz = 500000
        self.pettersson_m500 = wurb_rec.PetterssonM500BatMic()

        # Internal.
        self.logger = logging.getLogger("CloudedBats-WURB")
        self.capture_active = False

    def is_m500_available(self):
        """ """
        return self.pettersson_m500.is_available()

    def get_device_name(self):
        """ """
        return self.device_name

    def get_sampling_freq_hz(self):
        """ """
        return self.sampling_freq_hz

    def is_capture_active(self):
        """ """
        return self.capture_active

    async def initiate_capture(self, card_index, sampling_freq, buffer_size):
        """ """
        self.main_loop = asyncio.get_running_loop()
        self.card_index = card_index
        self.sampling_freq = sampling_freq
        self.buffer_size = buffer_size

    async def start_capture_in_executor(self):
        """ Use executor for IO-blocking function. """
        # self.logger.debug("CAPTURE-EXECUTOR STARTING.")
        if self.is_capture_active():
            self.logger.debug("ERROR: CAPTURE already running: ")
            return
        #
        await self.main_loop.run_in_executor(None, self.start_capture)

    async def stop_capture(self):
        """ """
        # Use traditional thread termination.
        self.capture_active = False
        self.pettersson_m500.stop_stream()
        self.pettersson_m500.reset()

    def start_capture(self):
        """ For the Pettersson M500 microphone. """
        self.active = True
        #
        try:
            self.stream_time_s = time.time()
            self.pettersson_m500.start_stream()
            self.pettersson_m500.led_on()
        except Exception as e:
            # Logging error.
            message = "Failed to create stream (M500): " + str(e)
            self.logger.debug(message)
            return
        # Main loop.
        try:
            # buffer_size = int(self.sampling_freq_hz / 2)
            buffer_size = int(self.sampling_freq_hz)  # Size gives 0.5 sec. buffers.
            data_array = array.array("B")
            data = self.pettersson_m500.read_stream()
            data_array += data
            while self.active and (len(data) > 0):
                # Push 0.5 sec each time. M500 can't deliver that size directly.
                if len(data_array) >= buffer_size:
                    # Add time and check for time drift.
                    self.stream_time_s += 0.5  # One buffer is 0.5 sec.
                    # Push time and data buffer.
                    data_buffer = data_array[0:buffer_size]
                    data_int16 = numpy.fromstring(
                        data_buffer.tostring(), dtype=numpy.int16
                    )  # To ndarray.

                    # Use data queue.
                    if self.data_queue:
                        # Round to half seconds.
                        buffer_adc_time = int((self.stream_time_s) * 2) / 2
                        detector_time = time.time()
                        # Copy data.
                        data_int16_copy = data_int16.copy()
                        # Put together.
                        send_dict = {
                            "status": "data",
                            "adc_time": buffer_adc_time,
                            "detector_time": detector_time,
                            "data": data_int16_copy,
                        }
                        # Add to queue in main event loop.
                        try:
                            if not self.data_queue.full():
                                self.main_loop.call_soon_threadsafe(
                                    self.data_queue.put_nowait, send_dict
                                )
                        except Exception as e:
                            # Logging error.
                            message = "Failed to put buffer on queue (M500): " + str(e)
                            self.logger.debug(message)
                            pass

                    # Use data buffer.
                    if self.direct_target:
                        # The target object must contain the methods is_active() and add_data().
                        try:
                            if self.direct_target.is_active():
                                data_int16_copy = data_int16.copy()
                                self.main_loop.call_soon_threadsafe(
                                    self.direct_target.add_data, data_int16_copy
                                )
                        except Exception as e:
                            # Logging error.
                            message = "Failed to add data to direct_target: " + str(e)
                            self.logger.debug(message)

                    # print("DEBUG M500 buffer: ", data_int16, "    Len: ", len(data_int16))
                    # Save remaining part.
                    data_array = data_array[buffer_size:]
                # Add next buffer from M500.
                data = self.pettersson_m500.read_stream()
                data_array += data

        except asyncio.CancelledError:
            pass
        except Exception as e:
            # Logging error.
            message = "Recorder: sound_source_worker (M500): " + str(e)
            self.logger.debug(message)
