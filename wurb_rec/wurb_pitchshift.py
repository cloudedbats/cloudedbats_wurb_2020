#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import numpy
import scipy.signal
import sounddevice

import sys
import time
import soundfile
import pathlib
<<<<<<< HEAD

=======
>>>>>>> f6049a7bc19d5c7f89b28675f6a8c91d92ff4701
# import threading


class WurbPitchShift(object):
    """ For sound feedback by using Pitch Shift, PS. """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        # self.wurb_settings = wurb_manager.wurb_settings
        # self.wurb_logging = wurb_manager.wurb_logging
        self.asyncio_loop = None
        self.clear()

    def clear(self):
        """ """
        self.sampling_freq_in = None
        self.pitch_div_factor = None
        self.volume = None
        self.filter_low_limit_hz = None
        self.filter_high_limit_hz = None
        self.filter_order = None
        self.sampling_freq_out = None
        self.hop_in_length = None
        self.hop_out_length = None
        self.window_size = None
        self.window_function = None
        self.in_buffer = None
        self.pitchshift_buffer = None
        self.to_out_limit = None
        self.out_buffer = None

<<<<<<< HEAD
    def startup(
        self,
        sampling_freq=384000,
        pitch_div_factor=10,
        volume=1.0,
        filter_low_limit_hz=15000,
        filter_high_limit_hz=120000,
        filter_order=10,
        overlap_in_factor=1.5,
        kaiser_beta=14):
=======
    def setup(self, sampling_freq = 384000, 
                    pitch_div_factor = 10, 
                    volume = 1.0, 
                    filter_low_limit_hz = 15000, 
                    filter_high_limit_hz = 120000, 
                    filter_order = 10, 
                    overlap_in_factor = 1.5, 
                    kaiser_beta = 14):
>>>>>>> f6049a7bc19d5c7f89b28675f6a8c91d92ff4701
        """ """
        try:
            self.sampling_freq_in = sampling_freq
            self.pitch_div_factor = pitch_div_factor
            self.volume = volume
            self.filter_low_limit_hz = filter_low_limit_hz
            self.filter_high_limit_hz = filter_high_limit_hz
            self.filter_order = filter_order
            # Calculated parameters.
            self.sampling_freq_out = int(self.sampling_freq_in / pitch_div_factor)
            self.hop_out_length = int(self.sampling_freq_in / 1000 / pitch_div_factor)
            self.hop_in_length = int(self.hop_out_length * pitch_div_factor)
            self.window_size = int(self.hop_in_length * overlap_in_factor)
            # Buffers.
            self.window_function = numpy.kaiser(self.window_size, beta=kaiser_beta)
            self.in_buffer = numpy.array([], dtype=numpy.float64)
<<<<<<< HEAD
            self.pitchshift_buffer = numpy.zeros(
                self.sampling_freq_out, dtype=numpy.float64
            )  # 1 sec.
            self.to_out_limit = int(
                self.sampling_freq_in / pitch_div_factor / 2
            )  # About 0.5 sec.
=======
            self.pitchshift_buffer = numpy.zeros(self.sampling_freq_out, dtype=numpy.float64) # 1 sec.
            self.to_out_limit = int(self.sampling_freq_in / pitch_div_factor / 2) # About 0.5 sec.
>>>>>>> f6049a7bc19d5c7f89b28675f6a8c91d92ff4701
            self.out_buffer = numpy.array([], dtype=numpy.float64)
        except Exception as e:
            print("Exception: WurbPitchShift: setup:", e)

<<<<<<< HEAD
    def shutdown(self):
        """ """
        # await self.stop()
        # if self.gps_control_task:
        #     self.gps_control_task.cancel()
        #     self.gps_control_task = None

    def add_buffer(self, buffer):
        """ """
        # Filter buffer. Butterworth bandpass.
        sos = scipy.signal.butter(
            self.filter_order,
            [self.filter_low_limit_hz, self.filter_high_limit_hz],
            btype="bandpass",
            fs=self.sampling_freq_in,
            output="sos",
        )
=======
    def add_buffer(self, buffer):
        """ """
        # Filter buffer. Butterworth bandpass.
        sos = scipy.signal.butter(self.filter_order, 
                                  [self.filter_low_limit_hz, self.filter_high_limit_hz], 
                                  btype='bandpass', 
                                  fs=self.sampling_freq_in, 
                                  output="sos")
>>>>>>> f6049a7bc19d5c7f89b28675f6a8c91d92ff4701
        filtered = scipy.signal.sosfilt(sos, buffer)
        # Concatenate with old buffer.
        self.in_buffer = numpy.concatenate((self.in_buffer, filtered))
        # Add overlaps on pitchshift_buffer. Window function is applied on "part".
        insert_pos = 0
        while len(self.in_buffer) > self.window_size:
<<<<<<< HEAD
            part = self.in_buffer[: self.window_size] * self.window_function
            self.in_buffer = self.in_buffer[self.hop_in_length :]
            self.pitchshift_buffer[insert_pos : insert_pos + self.window_size] += part
            insert_pos += self.hop_out_length
            if insert_pos > self.to_out_limit:
                self.out_buffer = numpy.concatenate(
                    (self.out_buffer, self.pitchshift_buffer[:insert_pos])
                )
                self.pitchshift_buffer[: self.window_size] = self.pitchshift_buffer[
                    insert_pos : insert_pos + self.window_size
                ]
                self.pitchshift_buffer[self.window_size :] = 0.0
                insert_pos = 0
        # Flush.
        self.out_buffer = numpy.concatenate(
            (self.out_buffer, self.pitchshift_buffer[:insert_pos])
        )
        self.pitchshift_buffer[: self.window_size] = self.pitchshift_buffer[
            insert_pos : insert_pos + self.window_size
        ]
        self.pitchshift_buffer[self.window_size :] = 0.0
=======
            part = self.in_buffer[:self.window_size] * self.window_function
            self.in_buffer = self.in_buffer[self.hop_in_length:]
            self.pitchshift_buffer[insert_pos:insert_pos+self.window_size] += part
            insert_pos += self.hop_out_length
            if insert_pos > self.to_out_limit:
                self.out_buffer = numpy.concatenate((self.out_buffer, self.pitchshift_buffer[:insert_pos]))
                self.pitchshift_buffer[:self.window_size] = self.pitchshift_buffer[insert_pos:insert_pos+self.window_size]
                self.pitchshift_buffer[self.window_size:] = 0.0
                insert_pos = 0
        # Flush.
        self.out_buffer = numpy.concatenate((self.out_buffer, self.pitchshift_buffer[:insert_pos]))
        self.pitchshift_buffer[:self.window_size] = self.pitchshift_buffer[insert_pos:insert_pos+self.window_size]
        self.pitchshift_buffer[self.window_size:] = 0.0
>>>>>>> f6049a7bc19d5c7f89b28675f6a8c91d92ff4701
        insert_pos = 0

    def stream_sound(self):
        """ """
<<<<<<< HEAD

=======
>>>>>>> f6049a7bc19d5c7f89b28675f6a8c91d92ff4701
        def audio_out_callback(outdata, frames, cffi_time, status):
            """ Locally defined callback. Called from another thread. """
            if status:
                print("DEBUG: stream_sound/callback: ", status, file=sys.stderr)
<<<<<<< HEAD
            #
=======
            # 
>>>>>>> f6049a7bc19d5c7f89b28675f6a8c91d92ff4701
            if len(self.out_buffer) > frames:
                data = self.out_buffer[:frames]
                self.out_buffer = self.out_buffer[frames:]
                data *= self.volume
                data = data.reshape(-1, 1)
                outdata[:] = data
<<<<<<< HEAD
            else:
=======
            else: 
>>>>>>> f6049a7bc19d5c7f89b28675f6a8c91d92ff4701
                # Send zeroes if out buffer is empty.
                outdata[:] = numpy.zeros((frames, 1), dtype=numpy.float64)

                # raise sounddevice.CallbackStop

        # End of locally defined callback.

        try:
            # event = threading.Event()

            # Start streaming of sound.
            # self.asyncio_loop = asyncio.get_event_loop()
            stream = sounddevice.OutputStream(
<<<<<<< HEAD
                device="Built-in Output",  # self.device_name,
                samplerate=int(self.sampling_freq_out),
                channels=1,
                blocksize=0,  # Automatically by ALSA.
                callback=audio_out_callback,  # Locally defined above.
=======
                device= "Built-in Output", # self.device_name,
                samplerate=int(self.sampling_freq_out),
                channels=1,
                blocksize=0, # Automatically by ALSA.
                callback=audio_out_callback, # Locally defined above.

>>>>>>> f6049a7bc19d5c7f89b28675f6a8c91d92ff4701
                # finished_callback=event.set,
            )
            with stream:
                time.sleep(6.0)
                # event.wait()

        except Exception as e:
            print("Exception stream_sound: ", e)


<<<<<<< HEAD
=======

>>>>>>> f6049a7bc19d5c7f89b28675f6a8c91d92ff4701
if __name__ == "__main__":
    """ """
    pitchshift = WurbPitchShift(wurb_manager=None)
    #
    for file_path in sorted(pathlib.Path("TEST_PITCHSHIFT").glob("*.wav")):
        print("\nFile: ", str(file_path))
        wav_data_in, fs = soundfile.read(file_path, dtype="float64")
<<<<<<< HEAD
        pitchshift.startup(
            sampling_freq=fs,
            pitch_div_factor=10,
            volume=0.5,
            filter_low_limit_hz=15000,
            filter_high_limit_hz=90000,
        )
=======
        pitchshift.setup(sampling_freq = fs, 
                         pitch_div_factor = 10, 
                         volume = 0.5,
                         filter_low_limit_hz = 15000, 
                         filter_high_limit_hz = 90000, 
                         )
>>>>>>> f6049a7bc19d5c7f89b28675f6a8c91d92ff4701
        pitchshift.add_buffer(wav_data_in)
        pitchshift.stream_sound()
