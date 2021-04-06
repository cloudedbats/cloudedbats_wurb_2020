#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import numpy
import scipy.signal
import scipy.interpolate
import os
import sys
import pathlib

import wurb_rec


class WurbPitchShifting(object):
    """For audio feedback by using Pitch Shifting, PS.
    Simple time domain implementation by using overlapped
    windows and the Kaiser window function.
    """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.wurb_settings = wurb_manager.wurb_settings
        self.wurb_logging = wurb_manager.wurb_logging
        self.asyncio_loop = None
        self.audio_task = None
        # self.audio_callback_active = False
        self.alsa_playback = None
        #
        self.clear()

    def clear(self):
        """ """
        self.device_name = None
        self.device_freq_hz = 48000
        self.resample_factor = None
        self.sampling_freq_in = None
        self.pitch_div_factor = 30
        self.volume = 2.0
        self.filter_low_limit_hz = None
        self.filter_high_limit_hz = None
        self.filter_order = None
        self.sampling_freq_out = None
        self.hop_in_length = None
        self.hop_out_length = None
        self.window_size = None
        self.window_function = None
        self.in_buffer = None
        self.pitchshifting_buffer = None
        self.to_outbuffer_limit = None
        # self.out_buffer = None
        # Params.
        self.filter_order = 10
        self.max_buffer_size_s = 2.5
        # self.min_adjust_buffer_s = 0.5

    async def set_sampling_freq(self, sampling_freq):
        """ """
        self.sampling_freq_in = int(float(sampling_freq))
        await self.setup()

    async def set_volume(self, volume):
        """ """
        try:
            # print("AUDIO FEEDBACK VOLUME: ", volume)
            self.volume = float((float(volume) / 100.0) * 2.0)
        except Exception as e:
            print("EXCEPTION: set_volume: ", e)

    async def set_pitch(self, pitch_factor):
        """ """
        try:
            # print("AUDIO FEEDBACK PITCH: ", pitch_factor)
            self.pitch_div_factor = int(float(pitch_factor))
            await self.setup()
        except Exception as e:
            print("EXCEPTION: set_pitch: ", e)

    def is_active(self):
        """ """
        # return self.audio_callback_active
        if self.alsa_playback:
            return self.alsa_playback.is_active()
        return False

    async def setup(self):
        """ """
        try:
            # From settings.
            settings_dict = await self.wurb_settings.get_settings()
            # Volume and pitch.
            feedback_volume = settings_dict.get("feedback_volume", "100")
            self.volume = float((float(feedback_volume) / 100.0) * 2.0)
            feedback_pitch = settings_dict.get("feedback_pitch", "30")
            self.pitch_div_factor = int(float(feedback_pitch))
            # Filter.
            filter_low_khz = settings_dict.get("feedback_filter_low_khz", "15.0")
            filter_high_khz = settings_dict.get("feedback_filter_high_khz", "150.0")
            self.filter_low_limit_hz = int(float(filter_low_khz) * 1000.0)
            self.filter_high_limit_hz = int(float(filter_high_khz) * 1000.0)
            # Calculated parameters.
            self.sampling_freq_out = int(self.sampling_freq_in / self.pitch_div_factor)
            self.hop_out_length = int(
                self.sampling_freq_in / 1000 / self.pitch_div_factor
            )
            self.hop_in_length = int(self.hop_out_length * self.pitch_div_factor)
            self.resample_factor = self.sampling_freq_out / self.device_freq_hz
            # Buffers.
            buffer_in_overlap_factor = 1.5
            kaiser_beta = int(self.pitch_div_factor * 0.8)
            self.window_size = int(self.hop_in_length * buffer_in_overlap_factor)
            self.window_function = numpy.kaiser(self.window_size, beta=kaiser_beta)
            self.in_buffer = numpy.array([], dtype=numpy.float32)
            pitchshifting_buffer_length = int(self.sampling_freq_out * 3)
            self.pitchshifting_buffer = numpy.zeros(
                pitchshifting_buffer_length, dtype=numpy.float32
            )  # 3 sec buffer length.
            self.to_outbuffer_limit = int(
                pitchshifting_buffer_length / 2
            )  # Half buffer used.
            # self.out_buffer = numpy.array([], dtype=numpy.float32)

        except Exception as e:
            print("Exception: WurbPitchShifting: setup: ", e)

    async def startup(self):
        """ """
        self.asyncio_loop = asyncio.get_event_loop()
        part_of_name = os.getenv("WURB_REC_OUTPUT_DEVICE", "Headphones")
        # part_of_name = os.getenv("WURB_REC_OUTPUT_DEVICE", "iMic")
        sampling_freq_hz = int(os.getenv("WURB_REC_OUTPUT_DEVICE_FREQ_HZ", "48000"))
        # # ALSA volume.
        # wurb_rec.AlsaMixer().set_volume(volume_percent=100, card_index=-1)
        # ALSA cards.
        cards = wurb_rec.AlsaSoundCards()
        cards.update_card_lists()
        card_index = cards.get_playback_card_index_by_name(part_of_name)
        if card_index != None:
            self.alsa_playback = wurb_rec.AlsaSoundPlayback()
            buffer_size = 1000
            await self.alsa_playback.start_playback(
                card_index=card_index, sampling_freq=sampling_freq_hz, buffer_size=buffer_size
            )
        else:
            print("FAILED TO FIND CARD: ", part_of_name)

    async def shutdown(self):
        """ """
        if self.alsa_playback:
            await self.alsa_playback.stop_playback()
            self.alsa_playback = None

    def add_data(self, buffer_int16):
        """ """
        if self.is_active():
            self.asyncio_loop.run_in_executor(None, self.add_buffer, buffer_int16)

    def add_buffer(self, buffer_int16):
        """ """
        try:
            if (self.alsa_playback is None) or (not self.is_active()):
                if self.in_buffer.size > 0:
                    self.in_buffer = numpy.array([], dtype=numpy.float32)
                # if self.out_buffer.size > 0:
                #     self.out_buffer = numpy.array([], dtype=numpy.float32)
                return

            # Buffer delivered as int16. Transform to intervall -1 to 1.
            buffer = buffer_int16 / 32768.0
            # Filter buffer. Butterworth bandpass.
            filtered = buffer
            try:
                low_limit_hz = self.filter_low_limit_hz
                high_limit_hz = self.filter_high_limit_hz
                if (high_limit_hz + 100) >= (self.sampling_freq_in / 2):
                    high_limit_hz = self.sampling_freq_in / 2 - 100
                if low_limit_hz < 0 or (low_limit_hz + 100 >= high_limit_hz):
                    low_limit_hz = 0
                sos = scipy.signal.butter(
                    self.filter_order,
                    [low_limit_hz, high_limit_hz],
                    btype="bandpass",
                    fs=self.sampling_freq_in,
                    output="sos",
                )
                filtered = scipy.signal.sosfilt(sos, buffer)
            except Exception as e:
                pass
                print("EXCEPTION: Butterworth: ", e)
            # Concatenate with old buffer.
            self.in_buffer = numpy.concatenate((self.in_buffer, filtered))
            # Add overlaps on pitchshifting_buffer. Window function is applied on "part".
            insert_pos = 0
            while self.in_buffer.size > self.window_size:
                part = self.in_buffer[: self.window_size] * self.window_function
                self.in_buffer = self.in_buffer[self.hop_in_length :]
                self.pitchshifting_buffer[
                    insert_pos : insert_pos + self.window_size
                ] += part
                insert_pos += self.hop_out_length
                if insert_pos > self.to_outbuffer_limit:
                    new_part = self.pitchshifting_buffer[:insert_pos]
                    new_part_2 = self.resample(new_part)

                    new_buffer_int16 = numpy.array(new_part_2 * 32768.0 * self.volume, dtype=numpy.int16)
                    self.alsa_playback.add_data(new_buffer_int16)

                    self.pitchshifting_buffer[
                        : self.window_size
                    ] = self.pitchshifting_buffer[
                        insert_pos : insert_pos + self.window_size
                    ]
                    self.pitchshifting_buffer[self.window_size :] = 0.0
                    insert_pos = 0
            # Flush.
            new_part = self.pitchshifting_buffer[:insert_pos]
            new_part_2 = self.resample(new_part)

            new_buffer_int16 = numpy.array(new_part_2 * 32768.0 * self.volume, dtype=numpy.int16)
            self.alsa_playback.add_data(new_buffer_int16)

            self.pitchshifting_buffer[: self.window_size] = self.pitchshifting_buffer[
                insert_pos : insert_pos + self.window_size
            ]
            self.pitchshifting_buffer[self.window_size :] = 0.0
            insert_pos = 0
            # print("DEBUG: Max/min amp: ", max(self.out_buffer), "   ", min(self.out_buffer))
        except Exception as e:
            print("Exception: WurbPitchShifting: add_buffer: ", e)

    def resample(self, x, kind="linear"):
        """ Resample to 48000 Hz, in most cases, to match output devices. """
        if x.size > 0:
            n = int(numpy.ceil(x.size / self.resample_factor))
            f = scipy.interpolate.interp1d(numpy.linspace(0, 1, x.size), x, kind)
            return f(numpy.linspace(0, 1, n))
        else:
            return x
