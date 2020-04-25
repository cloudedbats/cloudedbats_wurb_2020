#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import time
from collections import deque
import sounddevice

import os
import wave

# CloudedBats.
from wurb_rec.wurb_settings import WurbSettings
from wurb_rec.wurb_logging import WurbLogging
from wurb_rec.sound_stream_manager import SoundStreamManager
from wurb_rec.wurb_sound_detector import SoundDetector

class WurbRecManager(object):
    """ """

    def __init__(self):
        """ """
        try:
            self.rec_status = "Not started"
            self.notification_event = None
            self.ultrasound_devices = None
            self.wurb_recorder = None
            self.update_status_task = None

            self.wurb_settings = None
            self.wurb_logging = None

        except Exception as e:
            print("Exception: ", e)

    async def startup(self):
        """ """
        try:
            self.ultrasound_devices = UltrasoundDevices()
            self.wurb_recorder = WurbRecorder()
            self.wurb_settings = WurbSettings()
            self.wurb_logging = WurbLogging()
            self.update_status_task = asyncio.create_task(self.update_status())

            # await self.ultrasound_devices.start_checking_devices()

        except Exception as e:
            print("Exception: ", e)

    async def shutdown(self):
        """ """
        try:
            if self.update_status_task:
                self.update_status_task.cancel()

            # await self.ultrasound_devices.stop_checking_devices()

            await self.wurb_recorder.stop_streaming(stop_immediate=True)
        except Exception as e:
            print("Exception: ", e)

    async def start_rec(self):
        """ """
        try:
            # await self.ultrasound_devices.stop_checking_devices()
            await self.ultrasound_devices.check_devices()

            device_name = self.ultrasound_devices.device_name
            sampling_freq_hz = self.ultrasound_devices.sampling_freq_hz
            if (len(device_name) > 1) and sampling_freq_hz > 180000:
                await self.wurb_recorder.set_device(device_name, sampling_freq_hz)
                await self.wurb_recorder.start_streaming()
            else:
                await self.wurb_recorder.set_rec_status(
                    "Failed: No valid microphone available."
                )

                # await self.ultrasound_devices.start_checking_devices()

        except Exception as e:
            print("Exception: ", e)

    async def stop_rec(self):
        """ """
        try:
            await self.wurb_recorder.set_rec_status("")
            await self.wurb_recorder.stop_streaming(stop_immediate=True)
            await self.ultrasound_devices.reset_devices()

            # await self.ultrasound_devices.start_checking_devices()

        except Exception as e:
            print("Exception: ", e)

    async def get_notification_event(self):
        """ """
        try:
            if self.notification_event == None:
                self.notification_event = asyncio.Event()
            return self.notification_event
        except Exception as e:
            print("Exception: ", e)

    async def get_status_dict(self):
        """ """
        try:
            status_dict = {
                "rec_status": self.wurb_recorder.rec_status,
                "device_name": self.ultrasound_devices.device_name,
                "sample_rate": str(self.ultrasound_devices.sampling_freq_hz),
            }
            return status_dict
        except Exception as e:
            print("Exception: ", e)

    async def update_status(self):
        """ """
        print("DEBUG: update_status activated.")
        try:
            while True:
                device_notification = (
                    await self.ultrasound_devices.get_notification_event()
                )
                rec_notification = await self.wurb_recorder.get_notification_event()
                events = [
                    device_notification.wait(),
                    rec_notification.wait(),
                ]
                await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED)
                print("DEBUG: update_status released.")

                # Create a new event and release all from the old event.
                old_notification_event = self.notification_event
                self.notification_event = asyncio.Event()
                if old_notification_event:
                    old_notification_event.set()
        except Exception as e:
            print("DEBUG: update_status exception: ", e)
        finally:
            print("DEBUG: update_status terminated.")


class UltrasoundDevices(object):
    """ """

    def __init__(self):
        """ """
        # Ultrasound microphones supported by default:
        # - Pettersson: M500-384, u384, u256.
        # - Dodotronic: UltraMic 192K, 200K, 250K, 384K.
        self.name_part_list = ["Pettersson", "UltraMic"]
        self.device_name = ""
        self.sampling_freq_hz = 0
        self.check_interval_s = 5.0
        self.notification_event = None
        # self.device_checker_task = None

    async def check_devices(self):
        """ For asyncio events. """
        try:

            lock = asyncio.Lock()
            async with lock:
                # Refresh device list.
                sounddevice._terminate()
                sounddevice._initialize()
                await asyncio.sleep(0.2)

            await self.set_connected_device("", 0)

            device_dict = None
            device_name = ""
            sampling_freq_hz = 0
            for device_name_part in self.name_part_list:
                try:
                    device_dict = sounddevice.query_devices(device=device_name_part)
                    if device_dict:
                        device_name = device_dict["name"]
                        if ":" in device_name:
                            device_name = device_name.split(":")[
                                0
                            ]  # Extract name only.
                        sampling_freq_hz = int(device_dict["default_samplerate"])
                    break
                except:
                    pass

            await self.set_connected_device(device_name, sampling_freq_hz)

        except Exception as e:
            print("Exception: ", e)

    async def reset_devices(self):
        """ For asyncio events. """
        try:
            await self.set_connected_device("", 0)

        except Exception as e:
            print("Exception: ", e)

    async def get_notification_event(self):
        """ """
        try:
            if self.notification_event == None:
                self.notification_event = asyncio.Event()
            return self.notification_event
        except Exception as e:
            print("Exception: ", e)

    async def get_connected_device(self):
        """ """
        try:
            return self.device_name, self.sampling_freq_hz
        except Exception as e:
            print("Exception: ", e)

    async def set_connected_device(self, device_name, sampling_freq_hz):
        """ """
        try:
            print("DEBUG: set_connected_device called.")
            self.device_name = device_name
            self.sampling_freq_hz = sampling_freq_hz
            # Create a new event and release all from the old event.
            old_notification_event = self.notification_event
            self.notification_event = asyncio.Event()
            if old_notification_event:
                old_notification_event.set()
        except Exception as e:
            print("Exception: ", e)

    # async def start_checking_devices(self):
    #     """ For asyncio events. """
    #     try:
    #         self.device_checker_task = asyncio.create_task(
    #             self.check_connected_devices()
    #         )
    #     except Exception as e:
    #         print("Exception: ", e)

    # async def stop_checking_devices(self):
    #     """ For asyncio events. """
    #     try:
    #         self.device_checker_task.cancel()
    #     except Exception as e:
    #         print("Exception: ", e)

    # async def get_notification_event(self):
    #     """ """
    #     try:
    #         if self.notification_event == None:
    #             self.notification_event = asyncio.Event()
    #         return self.notification_event
    #     except Exception as e:
    #         print("Exception: ", e)

    # async def get_connected_device(self):
    #     """ """
    #     try:
    #         return self.device_name, self.sampling_freq_hz
    #     except Exception as e:
    #         print("Exception: ", e)

    # async def set_connected_device(self, device_name, sampling_freq_hz):
    #     """ """
    #     try:
    #         print("DEBUG: set_connected_device called.")
    #         self.device_name = device_name
    #         self.sampling_freq_hz = sampling_freq_hz
    #         # Create a new event and release all from the old event.
    #         old_notification_event = self.notification_event
    #         self.notification_event = asyncio.Event()
    #         if old_notification_event:
    #             old_notification_event.set()
    #     except Exception as e:
    #         print("Exception: ", e)

    # async def check_connected_devices(self):
    #     """ """
    #     print("DEBUG: check_connected_devices activated.")
    #     try:
    #         lock = asyncio.Lock()
    #         while True:
    #             # async with lock:
    #             #     # Refresh device list.
    #             #     sounddevice._terminate()
    #             #     sounddevice._initialize()

    #             # await asyncio.sleep(0.2)

    #             device_dict = None
    #             device_name = ""
    #             sampling_freq_hz = 0
    #             for device_name_part in self.name_part_list:
    #                 try:
    #                     device_dict = sounddevice.query_devices(device=device_name_part)
    #                     if device_dict:
    #                         device_name = device_dict["name"]
    #                         if ":" in device_name:
    #                             device_name = device_name.split(":")[0] # Extract name only.
    #                         sampling_freq_hz = int(device_dict["default_samplerate"])
    #                     break
    #                 except:
    #                     pass
    #             if (self.device_name == device_name) and (
    #                 self.sampling_freq_hz == sampling_freq_hz
    #             ):
    #                 await asyncio.sleep(self.check_interval_s)
    #             else:
    #                 # Make the new values public.
    #                 await self.set_connected_device(device_name, sampling_freq_hz)
    #     except Exception as e:
    #         print("DEBUG: check_connected_devices exception: ", e)
    #     finally:
    #         print("DEBUG: check_connected_devices terminated.")


class WurbRecorder(SoundStreamManager):
    """ """

    def __init__(self, queue_max_size=120):
        """ """
        super().__init__(queue_max_size)
        self.rec_status = ""
        self.device_name = ""
        self.sampling_freq_hz = 0
        self.notification_event = None
        self.rec_start_time = None

    async def get_notification_event(self):
        """ """
        try:
            if self.notification_event == None:
                self.notification_event = asyncio.Event()
            return self.notification_event
        except Exception as e:
            print("Exception: ", e)

    async def get_rec_status(self):
        """ """
        try:
            return self.rec_status
        except Exception as e:
            print("Exception: ", e)

    async def set_rec_status(self, rec_status):
        """ """
        try:
            print("DEBUG: set_rec_status called.")
            self.rec_status = rec_status
            # Create a new event and release all from the old event.
            old_notification_event = self.notification_event
            self.notification_event = asyncio.Event()
            if old_notification_event:
                old_notification_event.set()
        except Exception as e:
            print("Exception: ", e)

    async def set_device(self, device_name, sampling_freq_hz):
        """ """
        try:
            self.device_name = device_name
            self.sampling_freq_hz = sampling_freq_hz
        except Exception as e:
            print("Exception: ", e)

    async def sound_source_worker(self):
        """ Abstract worker method for sound sources. Mainly files or streams.
            Test implementation to be used as template.
        """
        self.rec_start_time = None
        loop = asyncio.get_event_loop()
        sound_source_event = asyncio.Event()

        def audio_callback(indata, frames, cffi_time, status):
            """ Locally defined callback.
                This is called (from a separate thread) for each audio block. """
            try:
                if status:
                    print("DEBUG: audio_callback Status:", status)  # , file=sys.stderr)

                input_buffer_adc_time = cffi_time.inputBufferAdcTime
                if self.rec_start_time == None:
                    # Adjust first buffer.
                    input_buffer_adc_time = input_buffer_adc_time + 0.121
                    self.rec_start_time = time.time() - input_buffer_adc_time
                # Round to half seconds.
                buffer_dac_time = (
                    int((self.rec_start_time + input_buffer_adc_time) * 2) / 2
                )
                # print("DEBUG: buffer_dac_time: ", buffer_dac_time, "   ",
                #     time.strftime("%Y%m%dT%H%M%S%z", time.localtime(buffer_dac_time)))

                send_dict = {
                    "status": "data",
                    "time": buffer_dac_time,
                    "data": indata[:, 0],  # Transform list of lists to list.
                }
                # Add to queue. Should be attached to the main async loop.
                loop.call_soon_threadsafe(self.from_source_queue.put_nowait, send_dict)

            except Exception as e:
                print("EXCEPTION: audio_callback: ", e)
                loop.call_soon_threadsafe(sound_source_event.set)

            """ End of locally defined callback. """

        try:
            print(
                "DEBUG: Rec started: ", self.device_name, "   ", self.sampling_freq_hz
            )
            time_start = time.time()
            print(
                "DEBUG: Rec start: ",
                time_start,
                "   ",
                time.strftime("%Y%m%dT%H%M%S%z", time.localtime(time_start)),
            )

            blocksize = int(self.sampling_freq_hz / 2)

            # Start streaming from the microphone.
            stream = sounddevice.InputStream(
                device=self.device_name,
                samplerate=self.sampling_freq_hz,
                channels=1,
                dtype="int16",
                blocksize=blocksize,
                callback=audio_callback,
            )

            await self.set_rec_status("Recording.")

            with stream:
                await sound_source_event.wait()

        except asyncio.CancelledError:
            print("DEBUG: ", "sound_source_worker cancelled.")
            # break
        except Exception as e:
            print("DEBUG: sound_source_worker exception: ", e)
        finally:
            await self.set_rec_status("Recording finished.")

    async def sound_process_worker(self):
        """ Abstract worker for sound processing algorithms.
            Test implementation to be used as template.
        """

        self.process_deque = deque()  # Double ended queue. TODO: Move this.
        self.process_deque.clear()

        sound_detected = False
        sound_detected_counter = 0
        sound_detector = SoundDetector().get_detector()

        try:
            while True:
                try:
                    try:
                        item = await self.from_source_queue.get()
                        self.from_source_queue.task_done()
                        if item == None:
                            await self.to_target_queue.put(None)  # Terminate.
                            print("DEBUG-2: Terminated by source.")
                            break
                        elif item == False:
                            print("DEBUG-2: Flush.")
                            await self.remove_items_from_queue(self.to_target_queue)
                            await self.to_target_queue.put(False)  # Flush.
                        else:
                            # Store in 6 sec. long list
                            new_item = {}
                            new_item["status"] = "data-Counter-" + str(
                                sound_detected_counter
                            )
                            new_item["time"] = item["time"]
                            new_item["data"] = item["data"].copy()

                            self.process_deque.append(new_item)
                            # Remove oldest item if the list is too long.
                            if len(self.process_deque) > 12:
                                self.process_deque.popleft()

                            if sound_detected == False:
                                sound_detected_counter = 0
                                # Check for sound.
                                sound_detected = sound_detector.check_for_sound(
                                    (item["time"], item["data"])
                                )
                                # sound_detected = True

                            if sound_detected == True:
                                sound_detected_counter += 1
                                # print("DEBUG-2: counter: ", sound_detected_counter,
                                #       "   deque length: ", len(self.process_deque))
                                if (sound_detected_counter >= 9) and (
                                    len(self.process_deque) >= 12
                                ):
                                    sound_detected = False
                                    sound_detected_counter = 0
                                    # Send to target.
                                    for index in range(0, 12):
                                        to_file_item = self.process_deque.popleft()
                                        if index == 0:
                                            to_file_item["status"] = "new_file"
                                        if index == 11:
                                            to_file_item["status"] = "close_file"
                                        await self.to_target_queue.put(to_file_item)
                                        await asyncio.sleep(0)

                            await asyncio.sleep(0)

                            # status = item.get('status', '')
                            # buffer_dac_time = item.get('time', '')
                            # data = item.get('data', '')
                            # print("DEBUG: Process status:", status, " time:", buffer_dac_time, " data: ", len(data))

                    except asyncio.QueueFull:
                        await self.remove_items_from_queue(self.to_target_queue)
                        self.process_deque.clear()
                        await self.to_target_queue.put(False)  # Flush.
                except asyncio.CancelledError:
                    print("DEBUG: ", "soundProcessWorker cancelled.")
                    break
                except Exception as e:
                    print("DEBUG: soundProcessWorker exception: ", e)
        except Exception as e:
            print("Exception: ", e)
        finally:
            print("DEBUG: ", "soundProcessWorker terminated.")

    async def sound_target_worker(self):
        """ Abstract worker for sound targets. Mainly files or streams.
            Test implementation to be used as template.
        """

        self._latitude = 0
        self._longitude = 0
        self._filename_prefix = "ASYNC"
        # self._out_sampling_rate_hz = 384000
        self._filename_rec_type = "FS384"
        self._dir_path = "recorded_files"

        wave_file_writer = None

        try:
            while True:
                try:
                    item = await self.to_target_queue.get()
                    self.to_target_queue.task_done()
                    if item == None:
                        print("DEBUG-3: Terminated by process.")
                        break
                    elif item == False:
                        print("DEBUG-3: Flush.")
                        await self.remove_items_from_queue(self.to_target_queue)
                        if wave_file_writer:
                            wave_file_writer.close()
                        pass  # TODO.
                    else:

                        print("DEBUG-3: Item: ", item["status"])

                        if item["status"] == "new_file":
                            #
                            if wave_file_writer:
                                wave_file_writer.close()

                            wave_file_writer = WaveFileWriter(self)

                        if wave_file_writer:
                            wave_file_writer.write(item["data"])

                            print("DEBUG-3 Time: ", item["time"])
                            print("DEBUG-3 Max: ", max(item["data"]))

                        if item["status"] == "close_file":
                            if wave_file_writer:
                                wave_file_writer.close()
                                wave_file_writer = None

                    await asyncio.sleep(0)

                except asyncio.CancelledError:
                    print("DEBUG: ", "soundTargetWorker cancelled.")
                    break
                except Exception as e:
                    print("DEBUG: soundTargetWorker exception: ", e)
        except Exception as e:
            print("Exception: ", e)
        finally:
            print("DEBUG: soundTargetWorker terminated.")


class WaveFileWriter:
    """ Each file is connected to a separate object to avoid concurrency problems. """

    def __init__(self, sound_target_obj):
        """ """
        self._wave_file = None
        self._sound_target_obj = sound_target_obj
        self._size_counter = 0

        import pathlib

        target_dir_1st_path = "/mount/usb0/"
        target_dir_2nd_path = "/user/pi/"
        target_dir_3rd_path = "./"

        if pathlib.Path(target_dir_1st_path).exists():
            print("DEBUG: exists: target_dir_1st_path")
        if pathlib.Path(target_dir_2nd_path).exists():
            print("DEBUG: exists: target_dir_2nd_path")
        if pathlib.Path(target_dir_3rd_path).exists():
            print("DEBUG: exists: target_dir_3rd_path")

        if pathlib.Path(target_dir_1st_path).is_mount():
            print("DEBUG: is_mount: target_dir_1st_path")
        if pathlib.Path(target_dir_2nd_path).is_mount():
            print("DEBUG: is_mount: target_dir_2nd_path")
        if pathlib.Path(target_dir_3rd_path).is_mount():
            print("DEBUG: is_mount: target_dir_3rd_path")



        # Create file name.
        # Default time and location.
        datetimestring = time.strftime("%Y%m%dT%H%M%S%z")
        latlongstring = ""  # Format: 'N56.78E12.34'
        try:
            if sound_target_obj._latitude >= 0:
                latlongstring += "N"
            else:
                latlongstring += "S"
            latlongstring += str(abs(sound_target_obj._latitude))
            #
            if sound_target_obj._longitude >= 0:
                latlongstring += "E"
            else:
                latlongstring += "W"
            latlongstring += str(abs(sound_target_obj._longitude))
        except:
            latlongstring = "N00.00E00.00"

        # # Use GPS time if available.
        # datetime_local_gps = wurb_core.WurbGpsReader().get_time_local_string()
        # if datetime_local_gps:
        #     datetimestring = datetime_local_gps
        # # Use GPS location if available.
        # latlong = wurb_core.WurbGpsReader().get_latlong_string()
        # if latlong:
        #     latlongstring = latlong

        # Filename example: "WURB1_20180420T205942+0200_N00.00E00.00_TE384.wav"
        filename = (
            sound_target_obj._filename_prefix
            + "_"
            + datetimestring
            + "_"
            + latlongstring
            + "_"
            + sound_target_obj._filename_rec_type
            + ".wav"
        )
        filenamepath = os.path.join(sound_target_obj._dir_path, filename)
        #
        if not os.path.exists(sound_target_obj._dir_path):
            os.makedirs(sound_target_obj._dir_path)  # For data, full access.
        # Open wave file for writing.
        self._wave_file = wave.open(filenamepath, "wb")
        self._wave_file.setnchannels(1)  # 1=Mono.
        self._wave_file.setsampwidth(2)  # 2=16 bits.
        self._wave_file.setframerate(sound_target_obj.sampling_freq_hz)
        # #
        # sound_target_obj._logger.info('Recorder: New sound file: ' + filename)

    def write(self, buffer):
        """ """
        self._wave_file.writeframes(buffer)
        self._size_counter += len(buffer) / 2  # Count frames.

    def close(self):
        """ """
        if self._wave_file is not None:
            self._wave_file.close()
            self._wave_file = None

            # length_in_sec = self._size_counter / self._sound_target_obj.sampling_freq_hz
            # self._sound_target_obj._logger.info('Recorder: Sound file closed. Length:' + str(length_in_sec) + ' sec.')


# === MAIN - for test ===
async def main():
    """ """
    try:
        print("Test started.")
        recorder = WurbRecorder()
        print("Test 1.")
        print("DEBUG: Check status: ", await recorder.get_rec_status())
        await asyncio.sleep(0.1)
        print("Test 2.")
        await recorder.start_streaming()
        await asyncio.sleep(10.5)
        print("Test 3.")
        await recorder.stop_streaming(stop_immediate=True)
        print("Test 4.")
        await recorder.wait_for_shutdown()
        print("Test finished.")
    except Exception as e:
        print("Exception: ", e)


if __name__ == "__main__":
    """ """
    asyncio.run(main(), debug=True)
