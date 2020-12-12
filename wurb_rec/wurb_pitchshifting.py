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
import soundfile
import pathlib


class WurbPitchShifting(object):
    """ For audio feedback by using Pitch Shifting, PS. """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        # self.wurb_settings = wurb_manager.wurb_settings
        # self.wurb_logging = wurb_manager.wurb_logging
        self.asyncio_loop = None
        self.audio_task = None
        #
        self.clear()

    def clear(self):
        """ """
        self.device_name = None
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
        self.pitchshifting_buffer = None
        self.to_out_limit = None
        self.out_buffer = None

    async def setup(
        self,
        device_name="dmix",  # Raspberry Pi 3.5 mm earphone.
        sampling_freq=384000,
        pitch_div_factor=10,
        volume=1.0,
        filter_low_limit_hz=15000,
        filter_high_limit_hz=120000,
        filter_order=10,
        max_buffer_size_s=1.0,
    ):
        """ """
        try:
            self.device_name = device_name
            self.sampling_freq_in = sampling_freq
            self.pitch_div_factor = pitch_div_factor
            self.volume = volume
            self.filter_low_limit_hz = filter_low_limit_hz
            self.filter_high_limit_hz = filter_high_limit_hz
            self.filter_order = filter_order
            self.max_buffer_size_s = max_buffer_size_s
            # Calculated parameters.
            self.sampling_freq_out = int(self.sampling_freq_in / pitch_div_factor)
            self.hop_out_length = int(self.sampling_freq_in / 1000 / pitch_div_factor)
            self.hop_in_length = int(self.hop_out_length * pitch_div_factor)
            # Buffers.
            buffer_in_overlap_factor=1.5,
            kaiser_beta=int(self.pitch_div_factor * 0.8)
            self.window_size = int(self.hop_in_length * buffer_in_overlap_factor)
            self.window_function = numpy.kaiser(self.window_size, beta=kaiser_beta)
            self.in_buffer = numpy.array([], dtype=numpy.float64)
            self.pitchshifting_buffer = numpy.zeros(
                self.sampling_freq_out, dtype=numpy.float64
            )  # 1 sec.
            self.to_out_limit = int(
                self.sampling_freq_in / pitch_div_factor / 2
            )  # About 0.5 sec.
            self.out_buffer = numpy.array([], dtype=numpy.float64)

        except Exception as e:
            print("Exception: WurbPitchShifting: setup: ", e)

    async def startup(self):
        """ """
        # Start audio
        self.asyncio_loop = asyncio.get_event_loop()
        self.audio_task = asyncio.create_task(self.stream_audio())

    async def shutdown(self):
        """ """
        try:
            if self.audio_task:
                self.audio_task.cancel()
        except Exception as e:
            print("Exception: WurbPitchShifting: shutdown: ", e)

    async def add_buffer(self, buffer):
        """ """
        if (len(self.out_buffer) / self.sampling_freq_out) > self.max_buffer_size_s:
            print("DEBUG: Out buffer too long: ", len(self.out_buffer))
            return

        # Filter buffer. Butterworth bandpass.
        sos = scipy.signal.butter(
            self.filter_order,
            [self.filter_low_limit_hz, self.filter_high_limit_hz],
            btype="bandpass",
            fs=self.sampling_freq_in,
            output="sos",
        )
        filtered = scipy.signal.sosfilt(sos, buffer)
        # Concatenate with old buffer.
        self.in_buffer = numpy.concatenate((self.in_buffer, filtered))
        # Add overlaps on pitchshifting_buffer. Window function is applied on "part".
        insert_pos = 0
        while len(self.in_buffer) > self.window_size:
            part = self.in_buffer[: self.window_size] * self.window_function
            self.in_buffer = self.in_buffer[self.hop_in_length :]
            self.pitchshifting_buffer[
                insert_pos : insert_pos + self.window_size
            ] += part
            insert_pos += self.hop_out_length
            if insert_pos > self.to_out_limit:
                self.out_buffer = numpy.concatenate(
                    (self.out_buffer, self.pitchshifting_buffer[:insert_pos])
                )
                self.pitchshifting_buffer[
                    : self.window_size
                ] = self.pitchshifting_buffer[
                    insert_pos : insert_pos + self.window_size
                ]
                self.pitchshifting_buffer[self.window_size :] = 0.0
                insert_pos = 0
        # Flush.
        self.out_buffer = numpy.concatenate(
            (self.out_buffer, self.pitchshifting_buffer[:insert_pos])
        )
        self.pitchshifting_buffer[: self.window_size] = self.pitchshifting_buffer[
            insert_pos : insert_pos + self.window_size
        ]
        self.pitchshifting_buffer[self.window_size :] = 0.0
        insert_pos = 0

    async def stream_audio(self):
        """ """
        loop = asyncio.get_event_loop()
        audio_event = asyncio.Event()

        def audio_out_callback(outdata, frames, cffi_time, status):
            """ Locally defined callback. Called from another thread. """
            try:
                if status:
                    print(
                        "DEBUG: stream_audio/callback: Status: ",
                        status,
                        file=sys.stderr,
                    )
                #
                if (self.out_buffer is not None) and (len(self.out_buffer) > frames):
                    data = self.out_buffer[:frames]
                    self.out_buffer = self.out_buffer[frames:]
                    data *= self.volume
                    data = data.reshape(-1, 1)
                    outdata[:] = data
                else:
                    # Send zeroes if out buffer is empty.
                    outdata[:] = numpy.zeros((frames, 1), dtype=numpy.float64)

                    # loop.call_soon_threadsafe(audio_event.set)

            except Exception as e:
                print("Exception stream_audio-callback: ", e)
                loop.call_soon_threadsafe(audio_event.set)

        # End of locally defined callback.

        try:
            # Start streaming of audio.
            # self.asyncio_loop = asyncio.get_event_loop()
            stream = sounddevice.OutputStream(
                device=self.device_name,
                samplerate=int(self.sampling_freq_out),
                channels=1,
                blocksize=0,  # Automatically by ALSA.
                callback=audio_out_callback,  # Locally defined above.
            )
            with stream:
                await audio_event.wait()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("Exception stream_audio: ", e)


# === MAIN - for test ===
async def main():
    """ """
    pitchshifting = WurbPitchShifting(wurb_manager=None)
    #
    used_freq = 0
    for file_path in sorted(pathlib.Path("TEST_WAV").glob("*.wav")):
        print("\nFile: ", str(file_path))
        wav_data_in, fs = soundfile.read(file_path, dtype="float64")
        if fs != used_freq:
            used_freq = fs
            await pitchshifting.shutdown()
            await pitchshifting.setup(
                # device_name="dmix",  # Raspberry Pi 3.5 mm earphone.
                device_name="Built-in Output",  # For test on Mac.
                sampling_freq=fs,
                pitch_div_factor=30,
                volume=0.5,
                # filter_low_limit_hz=15000,
                # filter_high_limit_hz=120000,
            )
            await pitchshifting.startup()
        #
        await pitchshifting.add_buffer(wav_data_in)
        await asyncio.sleep(5.5)
    #
    await asyncio.sleep(2.0)
    await pitchshifting.shutdown()


if __name__ == "__main__":
    """ """
    asyncio.run(main(), debug=True)