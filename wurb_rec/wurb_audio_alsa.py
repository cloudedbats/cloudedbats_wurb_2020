#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2021-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import alsaaudio
import asyncio
import numpy
import array
import time
import logging


class AlsaSoundCards:
    """ """

    def __init__(self):
        """ """
        self.logger = logging.getLogger("CloudedBats-WURB")
        self.clear()

    def clear(self):
        self.card_list = []
        self.capture_card_index_list = []
        self.playback_card_index_list = []

    def update_card_lists(self):
        """ """
        self.clear()
        # List cards and names.
        # Note: Results from card_indexes() and cards() must be mapped.
        card_ids = alsaaudio.cards()
        for id_index, card_index in enumerate(alsaaudio.card_indexes()):
            card_dict = {}
            card_dict["card_index"] = card_index
            card_dict["card_id"] = card_ids[id_index]
            card_name, long_name = alsaaudio.card_name(card_index)
            card_dict["card_name"] = card_name.strip()
            card_dict["card_long_name"] = long_name.strip()
            self.card_list.append(card_dict)
        # Check card devices for capture.
        for device in alsaaudio.pcms(alsaaudio.PCM_CAPTURE):
            if device.startswith("sysdefault:CARD="):
                card_id = device.replace("sysdefault:CARD=", "").strip()
                for card_dict in self.card_list:
                    if card_dict.get("card_id", "") == card_id:
                        card_dict["device"] = device
                        card_index = card_dict.get("card_index", "")
                        if card_index != "":
                            self.capture_card_index_list.append(card_index)
        # Check card devices for playback.
        for device in alsaaudio.pcms(alsaaudio.PCM_PLAYBACK):
            if device.startswith("sysdefault:CARD="):
                card_id = device.replace("sysdefault:CARD=", "").strip()
                for card_dict in self.card_list:
                    if card_dict.get("card_id", "") == card_id:
                        card_dict["device"] = device
                        card_index = card_dict.get("card_index", "")
                        if card_index != "":
                            self.playback_card_index_list.append(card_index)
        # For debug.
        for card_dict in self.card_list:
            card_name = card_dict.get("card_name", "")
            card_index = card_dict.get("card_index", "")
            self.logger.debug("Sound card: " + card_name + "   Index: " + str(card_index))
        self.logger.debug("Sound cards capture: " + str(self.capture_card_index_list))
        self.logger.debug("Sound cards playback: " + str(self.playback_card_index_list))


    def get_capture_card_index_by_name(self, part_of_name):
        """ Returns first found. """
        for card_dict in self.card_list:
            card_name = card_dict.get("card_name", "")
            card_index = card_dict.get("card_index", "")
            if card_index in self.capture_card_index_list:
                if part_of_name in card_name:
                    return card_index
        return None

    def get_playback_card_index_by_name(self, part_of_name):
        """ Returns first found. """
        for card_dict in self.card_list:
            card_name = card_dict.get("card_name", "")
            card_index = card_dict.get("card_index", "")
            if card_index in self.playback_card_index_list:
                if part_of_name in card_name:
                    return card_index
        return None

    def get_card_dict_by_index(self, card_index):
        """ Returns first found. """
        for card_dict in self.card_list:
            if card_index == card_dict.get("card_index", ""):
                return card_dict
        return {}

    def get_max_sampling_freq(self, card_index):
        """ Only for capture devices. """
        max_freq = -99
        inp = None
        try:
            try:
                inp = alsaaudio.PCM(
                    alsaaudio.PCM_CAPTURE,
                    alsaaudio.PCM_NORMAL,
                    channels=1,
                    format=alsaaudio.PCM_FORMAT_S16_LE,
                    device="sysdefault",
                    cardindex=card_index,
                )
                # Rates may be list, tuple or a single value.
                rates = inp.getrates()
                if type(rates) in [list, tuple]:
                    max_freq = inp.getrates()[-1]
                else:
                    max_freq = inp.getrates()
            except Exception as e:
                self.logger.debug("Exception: " + str(e))
        finally:
            if inp:
                inp.close()
        return max_freq


class AlsaMixer:
    """ """

    def __init__(self):
        """ """
        self.logger = logging.getLogger("CloudedBats-WURB")

    def set_volume(self, volume_percent=100, card_index=-1):
        """ """
        try:
            mixer = alsaaudio.Mixer(
                control="Master", id=0, device="sysdefault", cardindex=card_index
            )
            mixer.setvolume(int(volume_percent))
        except Exception as e:
            self.logger.debug("EXCEPTION: Mixer volume: " + str(e))


class AlsaSoundCapture:
    """ """

    def __init__(self, data_queue=None, direct_target=None):
        """ """
        self.data_queue = data_queue
        self.direct_target = direct_target
        self.card_index = None
        self.sampling_freq = None
        self.buffer_size = None
        # Internal.
        self.logger = logging.getLogger("CloudedBats-WURB")
        self.capture_active = False

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

    def start_capture(self):
        """ """
        self.logger.debug("CAPTURE STARTED.")
        pmc_capture = None
        self.capture_active = True
        try:
            calculated_time_s = time.time()
            time_increment_s = self.buffer_size / self.sampling_freq

            pmc_capture = alsaaudio.PCM(
                alsaaudio.PCM_CAPTURE,
                alsaaudio.PCM_NORMAL,
                # alsaaudio.PCM_NONBLOCK,
                channels=1,
                rate=self.sampling_freq,
                format=alsaaudio.PCM_FORMAT_S16_LE,
                periodsize=self.buffer_size,
                device="sysdefault",
                cardindex=self.card_index,
            )

            in_buffer_int16 = numpy.array([], dtype=numpy.int16)
            while self.capture_active:
                # Read from capture device.
                length, data = pmc_capture.read()
                if length < 0:
                    self.logger.debug("SOUND CAPTURE OVERRUN: " + str(length))
                elif len(data) > 0:
                    # Convert from string-byte array to int16 array.
                    in_data_int16 = numpy.frombuffer(data, dtype=numpy.int16)

                    # Temporary solution for stereo sound cards that can't 
                    # run in mono mode (or maybe related to a bug in alsaaudio).
                    # Extract one channel if the data array is doubled in size.
                    if (length * 2) == in_data_int16.size:
                        in_data_int16 = in_data_int16[1::2].copy()

                    # Concatenate
                    in_buffer_int16 = numpy.concatenate((in_buffer_int16, in_data_int16))

                    while len(in_buffer_int16) >= self.buffer_size:
                        # Copy "buffer_size" part and save remaining part.
                        data_int16 = in_buffer_int16[0:self.buffer_size]
                        in_buffer_int16 = in_buffer_int16[self.buffer_size:]

                        # Use data queue.
                        if self.data_queue:
                            # Time rounded to half sec.
                            calculated_time_s += time_increment_s
                            device_time = int((calculated_time_s) * 2) / 2
                            # Used to detect time drift.
                            detector_time = time.time()
                            # Copy data.
                            data_int16_copy = data_int16.copy()
                            # Put together.
                            data_dict = {
                                "status": "data",
                                "adc_time": device_time,
                                "detector_time": detector_time,
                                "data": data_int16_copy,
                            }
                            try:
                                if not self.data_queue.full():
                                    self.main_loop.call_soon_threadsafe(
                                        self.data_queue.put_nowait, data_dict
                                    )
                            #
                            except Exception as e:
                                # Logging error.
                                message = "Failed to put data on queue: " + str(e)
                                self.logger.debug(message)

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
        #
        except Exception as e:
            self.logger.debug("EXCEPTION CAPTURE: " + str(e))
        finally:
            self.capture_active = False
            if pmc_capture:
                pmc_capture.close()
            self.logger.debug("CAPTURE ENDED.")


class AlsaSoundPlayback:
    """ """

    def __init__(self, data_queue=None):
        """ """
        self.data_queue = data_queue
        self.card_index = None
        self.sampling_freq = None
        self.buffer_size = None
        #
        self.playback_task = None
        self.executor = None
        self.playback_active = False
        self.data_queue_task = None
        #
        self.logger = logging.getLogger("CloudedBats-WURB")
        self.out_buffer_int16 = None

    def is_active(self):
        """ """
        return self.playback_active

    def get_out_buffer_size_s(self):
        """ """
        size_in_sec = 0
        try:
            size_in_sec = len(self.out_buffer_int16) / self.sampling_freq
        except:
            pass
        return size_in_sec

    async def start_playback(self, card_index, sampling_freq, buffer_size):
        """ """
        self.card_index = card_index
        self.sampling_freq = sampling_freq
        self.buffer_size = buffer_size
        self.main_loop = asyncio.get_running_loop()
        # If already started.
        if self.playback_task:
            self.stop_playback()
        # Run executor as task.
        self.playback_task = asyncio.create_task(self.playback_executor())
        # Listen to data from queue.
        if self.data_queue:
            self.data_queue_task = asyncio.create_task(self.add_data_from_queue())

    async def playback_executor(self):
        """ Use executor for IO-blocking function. """
        await self.main_loop.run_in_executor(None, self.alsa_playback)

    async def stop_playback(self):
        """ """
        # Data queue.
        if self.data_queue_task:
            self.data_queue_task.cancel()
            self.data_queue_task = None
        # Playback.
        self.playback_active = False
        if self.playback_task:
            self.playback_task.cancel()
            self.playback_task = None

    async def add_data_from_queue(self):
        """ """
        try:
            # Clear queue.
            while not self.data_queue.empty():
                self.data_queue.get_nowait()
                self.data_queue.task_done()
            while True:
                try:
                    data_dict = await self.data_queue.get()
                    if "data" in data_dict:
                        self.add_data(data_dict["data"])
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # Logging error.
                    message = "Failed to read data queue: " + str(e)
                    self.logger.debug(message)
        except Exception as e:
            self.logger.debug("EXCEPTION from queue: " + str(e))

    def add_data(self, data):
        """ """
        # self.logger.debug("DEBUG DATA ADDED. Length: ", len(data))
        if self.out_buffer_int16 is None:
            self.out_buffer_int16 = numpy.array([], dtype=numpy.int16)
        self.out_buffer_int16 = numpy.concatenate((self.out_buffer_int16, data))

    def alsa_playback(self):
        """ """
        pmc_play = None
        self.playback_active = True
        try:
            pmc_play = alsaaudio.PCM(
                alsaaudio.PCM_PLAYBACK,
                alsaaudio.PCM_NORMAL,
                channels=1,
                rate=self.sampling_freq,
                format=alsaaudio.PCM_FORMAT_S16_LE,
                periodsize=self.buffer_size,
                device="sysdefault",
                cardindex=self.card_index,
            )
            #
            silent_buffer = numpy.zeros((self.buffer_size, 1), dtype=numpy.float32)
            while self.playback_active:
                try:
                    data_int16 = silent_buffer
                    #
                    if (self.out_buffer_int16 is not None) and (
                        self.out_buffer_int16.size > self.buffer_size
                    ):
                        data_int16 = self.out_buffer_int16[: self.buffer_size]
                        self.out_buffer_int16 = self.out_buffer_int16[
                            self.buffer_size :
                        ]
                    # else:
                    #     self.logger.debug("SILENCE")
                    # Convert to byte buffer and write.
                    out_buffer = data_int16.tobytes()
                    pmc_play.write(out_buffer)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.debug("EXCEPTION PLAYBACK-1: " + str(e))
        #
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.debug("EXCEPTION PLAYBACK-2: " + str(e))
        finally:
            self.playback_active = False
            if pmc_play:
                pmc_play.close()
            # self.logger.debug("PLAYBACK ENDED.")


# === MAIN - for test ===
async def main():
    """ """
    part_of_capture_card_name = "Pettersson"
    part_of_playback_card_name = "Headphones"
    # part_of_playback_card_name = "iMic"

    amixer = AlsaMixer()
    amixer.set_volume(volume_percent=100, card_index=-1)

    cards = AlsaSoundCards()
    cards.update_card_lists()

    # TEST 1: Use queue.
    sound_queue = asyncio.Queue(maxsize=4)
    alsa_capture = AlsaSoundCapture(data_queue=sound_queue)
    alsa_playback = AlsaSoundPlayback(data_queue=sound_queue)

    # # TEST 2: Used direct target.
    # alsa_playback = AlsaSoundPlayback(data_queue=None)
    # alsa_capture = AlsaSoundCapture(data_queue=None, direct_target=alsa_playback)

    #
    card_index = cards.get_capture_card_index_by_name(part_of_capture_card_name)
    if card_index != None:
        rate = cards.get_max_sampling_freq(card_index)
        buffer_size = int(rate / 2)  # 0.5 sec.
        await alsa_capture.initiate_capture(
            card_index=card_index, sampling_freq=rate, buffer_size=buffer_size
        )
        asyncio.create_task(alsa_capture.start_capture_in_executor())
    else:
        print("FAILED TO FIND CARD: ", part_of_capture_card_name)
    #
    card_index = cards.get_playback_card_index_by_name(part_of_playback_card_name)
    if card_index != None:
        rate = 48000
        buffer_size = 1000
        await alsa_playback.start_playback(
            card_index=card_index, sampling_freq=rate, buffer_size=buffer_size
        )
    else:
        print("FAILED TO FIND CARD: ", part_of_playback_card_name)

    await asyncio.sleep(4.0)
    await alsa_capture.stop_capture()
    await asyncio.sleep(10.0)
    await alsa_playback.stop_playback()


if __name__ == "__main__":
    """ """
    asyncio.run(main(), debug=True)