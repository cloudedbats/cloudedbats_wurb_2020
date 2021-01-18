#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import numpy
import scipy.signal
import scipy.interpolate
import sounddevice
import os
import sys
import pathlib


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
        self.audio_callback_active = False
        #
        self.clear()

    def clear(self):
        """ """
        self.device_name = None
        self.device_freq_hz = 48000
        self.resample_factor = None
        self.sampling_freq_in = None
        self.pitch_div_factor = 30
        self.volume = 1.0
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
        self.out_buffer = None
        # Params.
        self.filter_order = 10
        self.max_buffer_size_s = 2.5
        # self.min_adjust_buffer_s = 0.5

    async def set_sampling_freq(self, sampling_freq):
        """ """
        self.sampling_freq_in = int(sampling_freq)
        await self.setup()

    async def set_volume(self, volume):
        """ """
        print("AUDIO FEEDBACK VOLUME: ", volume)
        self.volume = (int(volume) / 100.0) * 2.0

    async def set_pitch(self, pitch_factor):
        """ """
        print("AUDIO FEEDBACK PITCH: ", pitch_factor)
        self.pitch_div_factor = int(pitch_factor)
        await self.setup()

    def is_audio_feedback_active(self):
        """ """
        return self.audio_callback_active

    async def setup(self):
        """ """
        try:
            # From settings.
            settings_dict = await self.wurb_settings.get_settings()
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
            self.out_buffer = numpy.array([], dtype=numpy.float32)

        except Exception as e:
            print("Exception: WurbPitchShifting: setup: ", e)

    async def startup(self):
        """ """
        # Shutdown if already running.
        await self.shutdown()
        feedback_on_off = self.wurb_settings.get_setting(key="feedback_on_off")
        if feedback_on_off == "feedback-on":
            # Start audio
            self.asyncio_loop = asyncio.get_event_loop()
            self.audio_task = asyncio.create_task(self.stream_audio())
            # self.audio_task = self.asyncio_loop.run_in_executor(None, self.stream_audio)

    async def shutdown(self):
        """ """
        try:
            if self.audio_task:
                self.audio_task.cancel()
                self.audio_task = None
                await asyncio.sleep(0.2)
        except Exception as e:
            print("Exception: WurbPitchShifting: shutdown: ", e)

    async def add_buffer(self, buffer_int16):
        """ """
        try:
            if (self.audio_task is None) or (not self.audio_callback_active):
                if self.in_buffer.size > 0:
                    self.in_buffer = numpy.array([], dtype=numpy.float32)
                if self.out_buffer.size > 0:
                    self.out_buffer = numpy.array([], dtype=numpy.float32)
                return
            # Reset before next check. Callback will set to true.
            self.audio_callback_active = False
            # Skip buffer to avoid too long delay before audio feedback.
            out_buffer_size_s = self.out_buffer.size / self.sampling_freq_out
            if out_buffer_size_s > self.max_buffer_size_s:
                # print("DEBUG: Out buffer too long: ", self.out_buffer.size)
                return
            # if out_buffer_size_s > self.min_adjust_buffer_s:
            #     frame_cut_nr  = int(buffer_int16.size / 20) # Cut 5%.
            #     buffer_int16 = buffer_int16[:-frame_cut_nr]
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
            except:
                pass
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
                    self.out_buffer = numpy.concatenate((self.out_buffer, new_part_2))
                    # self.out_buffer = numpy.concatenate(
                    #     (self.out_buffer, self.pitchshifting_buffer[:insert_pos])
                    # )
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
            self.out_buffer = numpy.concatenate((self.out_buffer, new_part_2))
            # self.out_buffer = numpy.concatenate(
            #     (self.out_buffer, self.pitchshifting_buffer[:insert_pos])
            # )
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

    async def stream_audio(self):
        """ """
        loop = asyncio.get_event_loop()
        audio_event = asyncio.Event()
        # From environment variables.
        # - Device "Headphones" is for RPi 3.5mm jack.
        self.device_name = os.getenv("WURB_REC_OUTPUT_DEVICE", "Headphones")
        self.device_freq_hz = int(os.getenv("WURB_REC_OUTPUT_DEVICE_FREQ_HZ", "48000"))

        # Locally defined callback.
        def audio_out_callback(outdata, frames, cffi_time, status):
            """ Locally defined callback. Called from another thread. """
            try:
                self.audio_callback_active = True
                if status:
                    pass
                    # print("DEBUG: STATUS: ", status)
                if (self.out_buffer is not None) and (self.out_buffer.size > frames):
                    data = self.out_buffer[:frames]
                    self.out_buffer = self.out_buffer[frames:]
                    data *= self.volume
                    data = data.reshape(-1, 1)
                    outdata[:] = data
                    # print("DEBUG: FRAMES: ", frames)
                else:
                    # Send zeroes if out buffer is empty.
                    outdata[:] = numpy.zeros((frames, 1), dtype=numpy.float32)
                    # print("DEBUG: FRAMES-ZEROS: ", frames)
            except Exception as e:
                print("Exception: WurbPitchShifting: stream_audio-callback: ", e)
                loop.call_soon_threadsafe(audio_event.set)

        # End of locally defined callback.

        try:
            # Start streaming of audio.
            # self.asyncio_loop = asyncio.get_event_loop()
            stream = sounddevice.OutputStream(
                device=self.device_name,
                samplerate=int(self.device_freq_hz),
                channels=1,
                blocksize=2048,  # 0 = Automatically by ALSA.
                callback=audio_out_callback,  # Locally defined above.
            )
            with stream:
                await audio_event.wait()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("Exception: WurbPitchShifting: stream_audio: ", e)


# === MAIN - for test ===
async def main():
    """ """
    # Run "pip install soundfile"
    # and maybe also "sudo apt install libsndfile1"
    # to execute this test.
    import soundfile

    pitchshifting = WurbPitchShifting(wurb_manager=None)
    #
    last_used_freq = 0
    for file_path in sorted(pathlib.Path("TEST_WAV").glob("*.wav")):
        print("\nFile: ", str(file_path))
        wav_data_in, fs = soundfile.read(file_path, dtype="int16")
        if fs != last_used_freq:
            last_used_freq = fs
            pitchshifting.sampling_freq_in = fs
            await pitchshifting.shutdown()
            await pitchshifting.setup(
                device_name="Headphones",  # RPi 3.5mm jacket.
                # device_name="Built-in Output",  # For test on Mac.
                # device_name="default",  # For test on Ubuntu/Parallels/Mac.
                # pitch_div_factor=10,
                # volume=1.0,
                # filter_low_limit_hz=15000,
                # filter_high_limit_hz=120000,
            )
            await pitchshifting.startup()
            await asyncio.sleep(1.0)
        #
        await pitchshifting.add_buffer(wav_data_in)
        await asyncio.sleep(6.0)
    #
    await asyncio.sleep(1.0)
    await pitchshifting.shutdown()


if __name__ == "__main__":
    """ """
    asyncio.run(main(), debug=True)