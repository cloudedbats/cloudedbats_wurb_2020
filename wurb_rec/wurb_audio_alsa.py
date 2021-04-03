#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2021-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import alsaaudio
import asyncio
import concurrent
import numpy
import time


class AlsaSoundCards:
    """ """

    def __init__(self):
        """ """
        self.clear()

    def clear(self):
        self.card_list = []
        self.input_card_index_list = []
        self.output_card_index_list = []

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
        # Check card devices for input and output.
        for device in alsaaudio.pcms(alsaaudio.PCM_CAPTURE):
            if device.startswith("sysdefault:CARD="):
                card_id = device.replace("sysdefault:CARD=", "").strip()
                for card_dict in self.card_list:
                    if card_dict.get("card_id", "") == card_id:
                        card_dict["device"] = device
                        card_index = card_dict.get("card_index", "")
                        if card_index:
                            self.input_card_index_list.append(card_index)
        for device in alsaaudio.pcms(alsaaudio.PCM_PLAYBACK):
            if device.startswith("sysdefault:CARD="):
                card_id = device.replace("sysdefault:CARD=", "").strip()
                for card_dict in self.card_list:
                    if card_dict.get("card_id", "") == card_id:
                        card_dict["device"] = device
                        card_index = card_dict.get("card_index", "")
                        if card_index:
                            self.output_card_index_list.append(card_index)

    def get_input_card_index_by_name(self, part_of_name):
        """ Returns fist found. """
        for card_index in self.input_card_index_list:
            card_dict = self.card_list[card_index]
            if part_of_name in card_dict.get("card_name", ""):
                card_index = card_dict.get("card_index", "")
                return card_index

    def get_output_card_index_by_name(self, part_of_name):
        """ Returns fist found. """
        for card_index in self.output_card_index_list:
            card_dict = self.card_list[card_index]
            if part_of_name in card_dict.get("card_name", ""):
                card_index = card_dict.get("card_index", "")
                return card_index

    def get_max_sampling_freq(self, card_index):
        """ Only for input devices. """
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
                print("Exception: ", e)
        finally:
            if inp:
                inp.close()
        return max_freq


class AlsaMixer:
    """ """

    def __init__(self):
        """ """

    def set_volume(self, card_index, volume_percent):
        """ """
        mixer = alsaaudio.Mixer(
            control="Master", id=0, device="sysdefault", cardindex=card_index
        )
        mixer.setvolume(volume_percent)
        # FOR DEBUG:
        print("DBUG: VOLUME: ", mixer.getvolume())


class AlsaSoundCapture:
    """ """

    def __init__(self, out_queue):
        """ """
        self.out_queue = out_queue
        self.card_index = None
        self.sampling_freq = None
        self.buffer_size = None
        #
        self.capture_task = None
        self.executor = None
        self.capture_active = False

    def is_active(self):
        """ """
        return self.capture_active

    async def start_capture(self, card_index, sampling_freq, buffer_size):
        """ """
        print("CAPTURE-TASK.")
        self.main_loop = asyncio.get_running_loop()
        self.card_index = card_index
        self.sampling_freq = sampling_freq
        self.buffer_size = buffer_size
        # If already started.
        if self.capture_task:
            await self.stop_capture()
        # Run executor as task.
        self.capture_task = asyncio.create_task(self.capture_executor())

    async def capture_executor(self):
        """ Use executor for IO-blocking function. """
        print("CAPTURE-EXECUTOR STARTED.")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await self.main_loop.run_in_executor(executor, self.alsa_capture)

    async def stop_capture(self):
        """ """
        self.capture_active = False
        if self.capture_task:
            self.capture_task.cancel()
            self.capture_task = None

    def alsa_capture(self):
        """ """
        print("CAPTURE STARTED.")
        calculated_time_s = time.time()
        time_increment_s = self.buffer_size / self.sampling_freq
        try:
            self.capture_active = True
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
            #
            while self.capture_active:
                length, data = pmc_capture.read()
                if length < 0:
                    print("SOUND CAPTURE OVERRUN: ", length)
                if len(data) > 0:
                    print("LENGTH: ", length)
                    data_int16 = numpy.frombuffer(data, dtype="int16")
                    # Time rounded to half sec.
                    calculated_time_s += time_increment_s
                    adc_time = int((calculated_time_s) * 2) / 2
                    detector_time = time.time()
                    # Put together.
                    send_dict = {
                        "status": "data",
                        "adc_time": adc_time,
                        "detector_time": detector_time,
                        "data": data_int16,
                    }
                    try:
                        if not self.out_queue.full():
                            self.main_loop.call_soon_threadsafe(
                                self.out_queue.put_nowait, send_dict
                            )
                    #
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        # Logging error.
                        message = "Failed to put buffer on queue: " + str(e)
                        print(message)
        #
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("EXCEPTION CAPTURE-2: ", e)
        finally:
            self.capture_active = False
            print("CAPTURE ENDED.")


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
        self.out_buffer_int16 = None

    def is_active(self):
        """ """
        return self.playback_active

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
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await self.main_loop.run_in_executor(executor, self.alsa_playback)

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
                    send_dict = await self.data_queue.get()
                    if "data" in send_dict:
                        self.add_data(send_dict["data"])
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # Logging error.
                    message = "Failed to read data queue: " + str(e)
                    print(message)
        except Exception as e:
            print("EXCEPTION from queue: ", e)

    def add_data(self, data):
        """ """
        print("DEBUG DATA ADDED: ")
        if self.out_buffer_int16 is None:
            self.out_buffer_int16 = numpy.array([], dtype=numpy.int16)
        self.out_buffer_int16 = numpy.concatenate((self.out_buffer_int16, data))

    def alsa_playback(self):
        """ """
        try:
            self.playback_active = True
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
                    #     print("SILENCE")
                    # Convert to byte buffer and write.
                    out_buffer = data_int16.tobytes()
                    pmc_play.write(out_buffer)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print("EXCEPTION PLAYBACK-1: ", e)
        #
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("EXCEPTION PLAYBACK-2: ", e)
        finally:
            self.playback_active = False
            print("PLAYBACK ENDED.")


# === MAIN - for test ===
async def main():
    """ """
    part_of_capture_card_name = "Pettersson"
    part_of_playback_card_name = "iMic"

    amixer = AlsaMixer()
    amixer.set_volume(0, 90)

    sound_queue = asyncio.Queue(maxsize=4)
    cards = AlsaSoundCards()
    cards.update_card_lists()
    #
    alsa_capture = AlsaSoundCapture(out_queue=sound_queue)
    alsa_playback = AlsaSoundPlayback(data_queue=sound_queue)
    #
    card_index = cards.get_input_card_index_by_name(part_of_capture_card_name)
    if card_index != None:
        rate = cards.get_max_sampling_freq(card_index)
        buffer_size = int(rate / 2)  # 0.5 sec.
        await alsa_capture.start_capture(
            card_index=card_index, sampling_freq=rate, buffer_size=buffer_size
        )
    else:
        print("FAILED TO FIND CARD: ", part_of_capture_card_name)
    #
    card_index = cards.get_output_card_index_by_name(part_of_playback_card_name)
    if card_index != None:
        rate = 48000
        buffer_size = 1000
        await alsa_playback.start_playback(
            card_index=card_index, sampling_freq=rate, buffer_size=buffer_size
        )
    else:
        print("FAILED TO FIND CARD: ", part_of_playback_card_name)

    await asyncio.sleep(2.0)
    await alsa_capture.stop_capture()
    await asyncio.sleep(10.0)
    await alsa_playback.stop_playback()


if __name__ == "__main__":
    """ """
    asyncio.run(main(), debug=True)