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
import pathlib


class WurbPitchShifting(object):
    """For audio feedback by using Pitch Shifting, PS.
    Simple time domain implementation by using overlapped
    windows and the Kaiser window function.
    """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        # self.wurb_settings = wurb_manager.wurb_settings
        # self.wurb_logging = wurb_manager.wurb_logging
        self.asyncio_loop = None
        self.audio_task = None
        self.audio_callback_active = False
        #
        self.clear()

    def clear(self):
        """ """
        self.device_name = None
        self.sampling_freq_in = None
        self.pitch_div_factor = 25
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

    async def set_volume(self, volume):
        """ """
        self.volume = (int(volume) / 100.0) * 2.0

    async def set_pitch_factor(self, pitch_factor):
        """ """
        self.pitch_div_factor = int(pitch_factor)
        await self.shutdown()
        await self.setup()
        await self.startup()

    def is_audio_feedback_active(self):
        """ """
        return self.audio_callback_active

    async def setup(
        self,
        device_name="Headphones",  # RPi 3.5mm connection when using rhythmbox.
        sampling_freq=384000,
        # pitch_div_factor=10,
        # volume=1.0,
        filter_low_limit_hz=15000,
        filter_high_limit_hz=150000,
        filter_order=10,
        max_buffer_size_s=0.5,
    ):
        """ """
        try:
            self.device_name = device_name
            self.sampling_freq_in = sampling_freq
            # self.pitch_div_factor = pitch_div_factor
            # self.volume = volume
            self.filter_low_limit_hz = filter_low_limit_hz
            self.filter_high_limit_hz = filter_high_limit_hz
            self.filter_order = filter_order
            self.max_buffer_size_s = max_buffer_size_s
            # Calculated parameters.
            self.sampling_freq_out = int(self.sampling_freq_in / self.pitch_div_factor)
            self.hop_out_length = int(self.sampling_freq_in / 1000 / self.pitch_div_factor)
            self.hop_in_length = int(self.hop_out_length * self.pitch_div_factor)
            # Buffers.
            buffer_in_overlap_factor = 1.5
            kaiser_beta = int(self.pitch_div_factor * 0.8)
            self.window_size = int(self.hop_in_length * buffer_in_overlap_factor)
            self.window_function = numpy.kaiser(self.window_size, beta=kaiser_beta)
            self.in_buffer = numpy.array([], dtype=numpy.float32)
            pitchshifting_buffer_length = int(self.sampling_freq_out)
            self.pitchshifting_buffer = numpy.zeros(
                pitchshifting_buffer_length, dtype=numpy.float32
            )  # 1 sec buffer length.
            self.to_outbuffer_limit = int(
                pitchshifting_buffer_length / 2
            )  # Half buffer used.
            self.out_buffer = numpy.array([], dtype=numpy.float32)

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
            self.audio_task = None
        except Exception as e:
            print("Exception: WurbPitchShifting: shutdown: ", e)

    async def add_buffer(self, buffer_int16):
        """ """
        if self.audio_task is None:
            return
        if self.audio_callback_active == False:
            return
        # Reset before next check. Callback will set to true.
        self.audio_callback_active = False
        # Skip buffer to avoid too long delay before audio feedback.
        if (len(self.out_buffer) / self.sampling_freq_out) > self.max_buffer_size_s:
            print("DEBUG: Out buffer too long: ", len(self.out_buffer))
            return
        # Buffer delivered as int16. Transform to intervall -1 to 1.
        buffer = buffer_int16 / 32768.0
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
            if insert_pos > self.to_outbuffer_limit:
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

        # print("DEBUG: Max/min amp: ", max(self.out_buffer), "   ", min(self.out_buffer))

    async def stream_audio(self):
        """ """
        loop = asyncio.get_event_loop()
        audio_event = asyncio.Event()

        def audio_out_callback(outdata, frames, cffi_time, status):
            """ Locally defined callback. Called from another thread. """
            try:
                self.audio_callback_active = True
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
                    # print("DEBUG: FRAMES: ", frames)
                else:
                    # Send zeroes if out buffer is empty.
                    outdata[:] = numpy.zeros((frames, 1), dtype=numpy.float32)

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
            await pitchshifting.shutdown()
            await pitchshifting.setup(
                # device_name="Headphones",  # RPi 3.5mm connection when using rhythmbox.
                device_name="Built-in Output",  # For test on Mac.
                sampling_freq=fs,
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