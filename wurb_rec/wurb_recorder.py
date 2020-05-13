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


# CloudedBats.
import wurb_rec


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


class WurbRecorder(wurb_rec.SoundStreamManager):
    """ """

    def __init__(self, wurb_manager, queue_max_size=120):
        """ """
        super().__init__(queue_max_size)
        self.wurb_manager = wurb_manager
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
                try:
                    loop.call_soon_threadsafe(
                        self.from_source_queue.put_nowait, send_dict
                    )
                except QueueFull:
                    print("EXCEPTION: from_source_queue: QueueFull.")
            except Exception as e:
                print("EXCEPTION: audio_callback: ", e)
                loop.call_soon_threadsafe(sound_source_event.set())

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

        try:
            self.process_deque = deque()  # Double ended queue. TODO: Move this.
            self.process_deque.clear()

            sound_detected = False
            sound_detected_counter = 0
            sound_detector = wurb_rec.SoundDetection(self.wurb_manager).get_detection()

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

                            wave_file_writer = WaveFileWriter(self.wurb_manager)
                            wave_file_writer.create(item["time"])

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
    """ Each file is connected to a separate file writer object 
        to avoid concurrency problems. """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.wurb_recorder = wurb_manager.wurb_recorder
        self.wurb_settings = wurb_manager.wurb_settings
        self.wurb_logging = wurb_manager.wurb_logging
        self.wave_file = None
        # self.size_counter = 0

    def create(self, start_time):
        """ Abstract. """

        sampling_freq_hz = self.wurb_recorder.sampling_freq_hz
        rec_file_prefix = self.wurb_settings.get_setting("filename_prefix")
        rec_target_dir_path = self.get_target_dir_path()
        rec_datetime = self.get_datetime(start_time)
        rec_location = self.get_location()
        rec_type = self.get_type(sampling_freq_hz)

        if rec_target_dir_path is None:
            self.wave_file = None
            return

        # Filename example: "WURB1_20180420T205942+0200_N00.00E00.00_TE384.wav"
        filename = (
            rec_file_prefix
            + "_"
            + rec_datetime
            + "_"
            + rec_location
            + "_"
            + rec_type
            + ".wav"
        )

        # Create directories.
        if not rec_target_dir_path.exists():
            rec_target_dir_path.mkdir(parents=True)
        # Open wave file for writing.
        filenamepath = pathlib.Path(rec_target_dir_path, filename)
        self.wave_file = wave.open(str(filenamepath), "wb")
        self.wave_file.setnchannels(1)  # 1=Mono.
        self.wave_file.setsampwidth(2)  # 2=16 bits.
        self.wave_file.setframerate(sampling_freq_hz)
        # #
        # sound_target_obj._logger.info('Recorder: New sound file: ' + filename)

    def write(self, buffer):
        """ """
        if self.wave_file is not None:
            self.wave_file.writeframes(buffer)
            # self.size_counter += len(buffer) / 2  # Count frames.

    def close(self):
        """ """
        if self.wave_file is not None:
            self.wave_file.close()
            self.wave_file = None

    def get_target_dir_path(self):
        """ """
        file_directory = self.wurb_settings.get_setting("file_directory")

        target_rpi_media_path = "/media/pi/"  # For RPi USB.
        target_rpi_internal_path = "/home/pi/"  # For RPi SD card with user 'pi'.

        dir_path = None

        # hdd = psutil.disk_usage(str(dir_path))
        # total_disk = hdd.total / (2**20)
        # used_disk = hdd.used / (2**20)
        # free_disk = hdd.free / (2**20)
        # percent_disk = hdd.percent
        # print("Total disk: ", total_disk, "MB")
        # print("Used disk: ", used_disk, "MB")
        # print("Free disk: ", free_disk, "MB")
        # print("Percent: ", percent_disk, "%")

        # Check mounted USB memory sticks. At least 20 MB left.
        rpi_media_path = pathlib.Path(target_rpi_media_path)
        if rpi_media_path.exists():
            for usb_stick_name in sorted(list(rpi_media_path.iterdir())):
                usb_stick_path = pathlib.Path(rpi_media_path, usb_stick_name)
                hdd = psutil.disk_usage(str(usb_stick_path))
                free_disk = hdd.free / (2**20) # To MB.
                if free_disk >= 20.0:
                    return pathlib.Path(usb_stick_path, file_directory)

        # Check internal SD card. At least 500 MB left.
        rpi_internal_path = pathlib.Path(target_rpi_internal_path)
        if rpi_internal_path.exists():
            hdd = psutil.disk_usage(str(rpi_internal_path))
            free_disk = hdd.free / (2**20) # To MB.
            if free_disk >= 500.0:
                return pathlib.Path(rpi_internal_path, "wurb_files", file_directory)
            else:
                print("ERROR: Not enough space left on RPi SD card.")
                return None # Not enough space left on RPi SD card.

        # Default for not Raspberry Pi.
        dir_path = pathlib.Path("wurb_files", file_directory)
        return dir_path

    def get_datetime(self, start_time):
        """ """
        datetime_str = time.strftime("%Y%m%dT%H%M%S%z", time.localtime(start_time))
        return datetime_str

    def get_location(self):
        """ """
        latlongstring = ""
        try:
            location_dict = self.wurb_settings.get_location_dict()
            latitude_dd = float(location_dict.get("latitude_dd", "0.0"))
            longitude_dd = float(location_dict.get("longitude_dd", "0.0"))
            if latitude_dd >= 0:
                latlongstring += "N"
            else:
                latlongstring += "S"
            latlongstring += str(abs(latitude_dd))
            #
            if longitude_dd >= 0:
                latlongstring += "E"
            else:
                latlongstring += "W"
            latlongstring += str(abs(longitude_dd))
        except:
            latlongstring = "N00.00E00.00"

        return latlongstring

    def get_type(self, sampling_freq_hz):
        """ """
        try:
            sampling_freq_khz = sampling_freq_hz / 1000.0
            sampling_freq_khz = int(round(sampling_freq_khz, 0))
        except:
            sampling_freq_khz = "000"

        return "FS" + str(sampling_freq_khz)
