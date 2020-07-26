#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import time
import wave
import pathlib
import psutil
from collections import deque
import sounddevice
import numpy

import threading

# CloudedBats.
import wurb_rec


class WurbRecorderM500(wurb_rec.WurbRecorder):
    """ """
    def __init__(self, wurb_manager=None, asyncio_loop=None, asyncio_queue=None):
        """ """
        self.wurb_manager = wurb_manager
        self.asyncio_loop = asyncio_loop
        self.asyncio_queue = asyncio_queue
        self.device_name = "Pettersson M500 (500kHz)" 
        self.sampling_freq_hz = 500000 
        self.active = False
        self.pettersson_m500 = wurb_rec.PetterssonM500BatMic()

    def is_m500_available(self):
        """ """
        return self.pettersson_m500.is_available()

    def get_device_name(self):
        """ """
        return self.device_name

    def get_sampling_freq_hz(self):
        """ """
        return self.sampling_freq_hz

    def stop_streaming(self):
        """ """
        # Start source in thread.
        self.active = False
        self.pettersson_m500.stop_stream()
        self.pettersson_m500.reset()

    def start_streaming(self):
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
            self.wurb_manager.wurb_logging.error(message, short_message=message)
            return
        # Main loop.
        try:
            # buffer_size = int(self.sampling_freq_hz / 2)
            buffer_size = int(self.sampling_freq_hz) # Size gives 0.5 sec. buffers.
            data = self.pettersson_m500.read_stream()
            data_array = data
            while self.active and (len(data) > 0):
                # Push 0.5 sec each time. M500 can't deliver that size directly.
                if len(data_array) >= buffer_size:
                    # Add time and check for time drift.
                    self.stream_time_s += 0.5 # One buffer is 0.5 sec.
                    # Push time and data buffer.
                    data_buffer = data_array[0:buffer_size]
                    data_int16 = numpy.fromstring(data_buffer.tostring(), dtype=numpy.int16) # To ndarray.
                    # Round to half seconds.
                    buffer_adc_time = (
                        int((self.stream_time_s) * 2) / 2
                    )
                    detector_time = time.time()
                    # Put together.
                    send_dict = {
                        "status": "data",
                        "adc_time": buffer_adc_time,
                        "detector_time": detector_time,
                        "data": data_int16,
                    }
                    # Add to queue in main event loop.
                    try:
                        if not self.asyncio_queue.full():
                            self.asyncio_loop.call_soon_threadsafe(
                                self.asyncio_queue.put_nowait, send_dict
                            )
                    except Exception as e:
                        # Logging error.
                        message = "Failed to put buffer on queue (M500): " + str(e)
                        self.wurb_manager.wurb_logging.error(message, short_message=message)
                        pass
                    # print("DEBUG M500 buffer: ", data_int16, "    Len: ", len(data_int16))
                    # Save remaining part.
                    data_array = data_array[buffer_size:]
                #
                # Add next buffer.
                data = self.pettersson_m500.read_stream()
                if data:
                    data_array += data

        except asyncio.CancelledError:
            pass
        except Exception as e:
            # Logging error.
            message = "Recorder: sound_source_worker (M500): " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)
        # finally:
        #     self.pettersson_m500.stop_stream()
        #     self.pettersson_m500.reset()

