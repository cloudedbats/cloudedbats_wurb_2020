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

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        # Ultrasound microphones supported by default:
        # - Pettersson: M500-384, u384, u256.
        # - Dodotronic: UltraMic 192K, 200K, 250K, 384K.
        self.name_part_list = ["Pettersson", "UltraMic"]
        self.device_name = ""
        self.sampling_freq_hz = 0
        self.check_interval_s = 5.0
        self.notification_event = None

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
            print("Exception: Rec. check_devices: ", e)
            # Logging error.
            message = "Rec. check_devices: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def reset_devices(self):
        """ For asyncio events. """
        try:
            await self.set_connected_device("", 0)

        except Exception as e:
            print("Exception: ", e)
            # Logging error.
            message = "Recorder: reset_devices: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def get_notification_event(self):
        """ """
        try:
            if self.notification_event == None:
                self.notification_event = asyncio.Event()
            return self.notification_event
        except Exception as e:
            print("Exception: ", e)
            # Logging error.
            message = "Recorder: get_notification_event: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def get_connected_device(self):
        """ """
        try:
            return self.device_name, self.sampling_freq_hz
        except Exception as e:
            print("Exception: ", e)
            # Logging error.
            message = "Recorder: get_connected_device: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

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
            # Logging error.
            message = "Recorder: set_connected_device: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)


class WurbRecorder(wurb_rec.SoundStreamManager):
    """ """

    def __init__(self, wurb_manager, queue_max_size=1200):
        """ """
        super().__init__(queue_max_size)
        self.wurb_manager = wurb_manager
        self.wurb_settings = wurb_manager.wurb_settings
        self.wurb_logging = wurb_manager.wurb_logging
        self.rec_status = ""
        self.device_name = ""
        self.sampling_freq_hz = 0
        self.notification_event = None
        self.rec_start_time = None
        self.restart_activated = False
        # Config.
        self.max_adc_time_diff_s = 10  # Unit: sec.
        self.rec_length_s = 6  # Unit: sec.

    async def get_notification_event(self):
        """ """
        try:
            if self.notification_event == None:
                self.notification_event = asyncio.Event()
            return self.notification_event
        except Exception as e:
            print("Exception: ", e)
            # Logging error.
            message = "Recorder: get_notification_event: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def get_rec_status(self):
        """ """
        try:
            return self.rec_status
        except Exception as e:
            print("Exception: ", e)
            # Logging error.
            message = "Recorder: get_rec_status: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

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
            # Logging error.
            message = "Recorder: set_rec_status: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def set_device(self, device_name, sampling_freq_hz):
        """ """
        try:
            self.device_name = device_name
            self.sampling_freq_hz = sampling_freq_hz
        except Exception as e:
            print("Exception: ", e)
            # Logging error.
            message = "Recorder: set_device: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    # async def put_on_fromsourcequeue(self, send_dict):
    #     """ """
    #     # Compare real time and stream time.
    #     adc_time = send_dict["adc_time"]
    #     time_now = time.time()
    #     # Restart if it differ too much.
    #     if abs(adc_time - time_now) > self.max_adc_time_diff_s:
    #         # Check if restart already is requested.
    #         if self.restart_activated:
    #             return
    #         # Logging.
    #         message = "Warning: Time diff. detected. Rec. will be restarted."
    #         self.wurb_logging.info(message, short_message=message)
    #         # Restart recording.
    #         self.restart_activated = True
    #         loop = asyncio.get_event_loop()
    #         asyncio.run_coroutine_threadsafe(
    #             self.wurb_manager.restart_rec(), loop,
    #         )
    #         await self.remove_items_from_queue(self.from_source_queue)
    #         await self.from_source_queue.put(False)  # Flush.
    #         return
    #     # Put buffer on queue.
    #     try:
    #         if not self.from_source_queue.full():
    #             await self.from_source_queue.put_nowait(send_dict)
    #         else:
    #             await self.remove_items_from_queue(self.from_source_queue)
    #             await self.from_source_queue.put(False)  # Flush.
    #             print("DEBUG: from_source_queue id FULL. Queues are flushed.")
    #     except QueueFull:
    #         print("EXCEPTION: put_on_queue_from_source: QueueFull.")
    #     except Exception as e:
    #         print("EXCEPTION: put_on_queue_from_source: ", e)

    async def sound_source_worker(self):
        """ Abstract worker method for sound sources. Mainly files or streams.
            Test implementation to be used as template.
        """
        self.rec_start_time = None
        loop = asyncio.get_event_loop()
        sound_source_event = asyncio.Event()
        self.restart_activated = False

        def audio_callback(indata, frames, cffi_time, status):
            """ Locally defined callback.
                This is called (from a separate thread) for each audio block. """
            try:
                if status:
                    print("DEBUG: audio_callback Status:", status)

                input_buffer_adc_time = cffi_time.inputBufferAdcTime
                if self.rec_start_time == None:
                    # Adjust first buffer.
                    input_buffer_adc_time = input_buffer_adc_time + 0.121
                    self.rec_start_time = time.time() - input_buffer_adc_time
                # Round to half seconds.
                buffer_adc_time = (
                    int((self.rec_start_time + input_buffer_adc_time) * 2) / 2
                )
                # print(
                #     "DEBUG: adc_time: ",
                #     buffer_adc_time,
                #     "   ",
                #     time.strftime("%Y%m%dT%H%M%S%z", time.localtime(buffer_adc_time)),
                # )
                # Convert and copy buffer.
                indata_raw = indata[:, 0]  # Transform list of lists to list.
                indata_copy = indata_raw.copy()
                # Used to check time drift.
                detector_time = time.time()
                # Put together.
                send_dict = {
                    "status": "data",
                    "adc_time": buffer_adc_time,
                    "detector_time": detector_time,
                    "data": indata_copy,
                }
                # Add to queue.
                # Note: Maybe "call_soon_threadsafe" is faster than "run_coroutine_threadsafe".
                try:
                    if not self.from_source_queue.full():
                        loop.call_soon_threadsafe(
                            self.from_source_queue.put_nowait, send_dict
                        )
                except Exception as e:
                    print("DEBUG: Failed to put buffer on queue: ", e)

                # # Add to queue. Should be attached to the main async loop.
                # asyncio.run_coroutine_threadsafe(
                #     self.put_on_fromsourcequeue(send_dict), loop,
                # )

            except Exception as e:
                print("EXCEPTION: audio_callback: ", e)
                # Logging error.
                message = "Recorder: audio_callback: " + str(e)
                self.wurb_manager.wurb_logging.error(message, short_message=message)
                # Exit recording loop.
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
            # Get rec length from settings.
            self.rec_length_s = int(self.wurb_settings.get_setting("rec_length_s"))
            #
            self.process_deque = deque()  # Double ended queue.
            self.process_deque.clear()
            self.process_deque_length = self.rec_length_s * 2
            self.detection_counter_max = self.process_deque_length - 3  # 1.5 s before.
            #
            first_sound_detected = False
            sound_detected = False
            sound_detected_counter = 0
            sound_detector = wurb_rec.SoundDetection(self.wurb_manager).get_detection()
            max_peak_freq_hz = None
            max_peak_dbfs = None

            while True:
                try:
                    try:
                        item = await self.from_source_queue.get()
                        try:
                            # print("=== PROCESS: ", item["adc_time"], item["data"][:5])
                            if item == None:
                                first_sound_detected == False
                                sound_detected_counter = 0
                                self.process_deque.clear()
                                await self.to_target_queue.put(None)  # Terminate.
                                print("DEBUG-2: Terminated by source.")
                                break
                            elif item == False:
                                print("DEBUG-2: Flush.")
                                first_sound_detected == False
                                sound_detected_counter = 0
                                self.process_deque.clear()
                                await self.remove_items_from_queue(self.to_target_queue)
                                await self.to_target_queue.put(False)  # Flush.
                            else:
                                # Compare real time and stream time.
                                adc_time = item["adc_time"]
                                detector_time = item["detector_time"]
                                # Restart if it differ too much.
                                if (
                                    abs(adc_time - detector_time)
                                    > self.max_adc_time_diff_s
                                ):
                                    # Check if restart already is requested.
                                    if self.restart_activated:
                                        return
                                    # Logging.
                                    message = "Warning: Time diff. detected. Rec. will be restarted."
                                    self.wurb_logging.info(
                                        message, short_message=message
                                    )
                                    # Restart recording.
                                    self.restart_activated = True
                                    loop = asyncio.get_event_loop()
                                    asyncio.run_coroutine_threadsafe(
                                        self.wurb_manager.restart_rec(), loop,
                                    )
                                    await self.remove_items_from_queue(
                                        self.from_source_queue
                                    )
                                    await self.from_source_queue.put(False)  # Flush.
                                    return

                                # Store in list-
                                new_item = {}
                                new_item["status"] = "data-Counter-" + str(
                                    sound_detected_counter
                                )
                                new_item["adc_time"] = item["adc_time"]
                                new_item["data"] = item["data"]

                                self.process_deque.append(new_item)
                                # Remove oldest items if the list is too long.
                                while (
                                    len(self.process_deque) > self.process_deque_length
                                ):
                                    self.process_deque.popleft()

                                # Check for sound.
                                detection_result = sound_detector.check_for_sound(
                                    (item["adc_time"], item["data"])
                                )
                                (
                                    sound_detected,
                                    peak_freq_hz,
                                    peak_dbfs,
                                ) = detection_result

                                if (not first_sound_detected) and sound_detected:
                                    first_sound_detected = True
                                    sound_detected_counter = 0
                                    max_peak_freq_hz = peak_freq_hz
                                    max_peak_dbfs = peak_dbfs

                                    # Log first detected sound.
                                    if first_sound_detected:
                                        # Logging.
                                        message = (
                                            "Sound peak: "
                                            + str(round(peak_freq_hz / 1000.0, 1))
                                            + " kHz / "
                                            + str(round(peak_dbfs, 1))
                                            + " dBFS."
                                        )
                                        self.wurb_logging.info(
                                            message, short_message=message
                                        )

                                # Accumulate in file queue.
                                if first_sound_detected == True:
                                    sound_detected_counter += 1
                                    if max_peak_dbfs and peak_dbfs:
                                        if peak_dbfs > max_peak_dbfs:
                                            max_peak_freq_hz = peak_freq_hz
                                            max_peak_dbfs = peak_dbfs
                                    if (
                                        sound_detected_counter
                                        >= self.detection_counter_max
                                    ) and (
                                        len(self.process_deque)
                                        >= self.process_deque_length
                                    ):
                                        first_sound_detected = False
                                        sound_detected_counter = 0
                                        # Send to target.
                                        for index in range(
                                            0, self.process_deque_length
                                        ):
                                            to_file_item = self.process_deque.popleft()
                                            #
                                            if index == 0:
                                                to_file_item["status"] = "new_file"
                                                to_file_item[
                                                    "max_peak_freq_hz"
                                                ] = max_peak_freq_hz
                                                to_file_item[
                                                    "max_peak_dbfs"
                                                ] = max_peak_dbfs
                                            if index == (self.process_deque_length - 1):
                                                to_file_item["status"] = "close_file"
                                            #
                                            if not self.to_target_queue.full():
                                                await self.to_target_queue.put(
                                                    to_file_item
                                                )

                                            # await asyncio.sleep(0)

                            # status = item.get('status', '')
                            # adc_time = item.get('time', '')
                            # data = item.get('data', '')
                            # print("DEBUG: Process status:", status, " time:", adc_time, " data: ", len(data))
                        finally:
                            self.from_source_queue.task_done()
                            await asyncio.sleep(0)

                    except asyncio.QueueFull:
                        await self.remove_items_from_queue(self.to_target_queue)
                        self.process_deque.clear()
                        await self.to_target_queue.put(False)  # Flush.
                except asyncio.CancelledError:
                    print("DEBUG: ", "soundProcessWorker cancelled.")
                    break
                except Exception as e:
                    print("DEBUG: soundProcessWorker exception: ", e)
            # While end.

        except Exception as e:
            print("Exception: Recorder: sound_process_worker: ", e)
            # Logging error.
            message = "Recorder: sound_process_worker: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)
        finally:
            print("DEBUG: ", "soundProcessWorker terminated.")

    async def sound_target_worker(self):
        """ Worker for sound targets. Mainly files or streams.
         """
        wave_file_writer = None
        try:
            while True:
                try:
                    item = await self.to_target_queue.get()
                    try:
                        if item == None:
                            # Terminated by process.
                            break
                        elif item == False:
                            await self.remove_items_from_queue(self.to_target_queue)
                            if wave_file_writer:
                                wave_file_writer.close()
                        else:
                            # New.
                            if item["status"] == "new_file":
                                if wave_file_writer:
                                    wave_file_writer.close()

                                wave_file_writer = WaveFileWriter(self.wurb_manager)
                                max_peak_freq_hz = item.get("max_peak_freq_hz", None)
                                max_peak_dbfs = item.get("max_peak_dbfs", None)
                                wave_file_writer.create(
                                    item["adc_time"], max_peak_freq_hz, max_peak_dbfs
                                )
                            # Data.
                            if wave_file_writer:
                                data_array = item["data"]
                                wave_file_writer.write(data_array)
                            # File.
                            if item["status"] == "close_file":
                                if wave_file_writer:
                                    wave_file_writer.close()
                                    wave_file_writer = None
                    finally:
                        self.to_target_queue.task_done()
                        await asyncio.sleep(0)

                except asyncio.CancelledError:
                    print("DEBUG: ", "SoundTargetWorker cancelled.")
                    break
                except Exception as e:
                    print("DEBUG: SoundTargetWorker exception: ", e)
                    # Logging error.
                    message = "Recorder: sound_target_worker: " + str(e)
                    self.wurb_manager.wurb_logging.error(message, short_message=message)
        except Exception as e:
            print("Exception: Recorder: sound_target_worker: ", e)
            # Logging error.
            message = "Recorder: sound_target_worker: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)
        finally:
            print("DEBUG: SoundTargetWorker terminated.")


class WaveFileWriter:
    """ Each file is connected to a separate file writer object 
        to avoid concurrency problems. """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.wurb_recorder = wurb_manager.wurb_recorder
        self.wurb_settings = wurb_manager.wurb_settings
        self.wurb_logging = wurb_manager.wurb_logging
        self.wurb_rpi = wurb_manager.wurb_rpi
        self.rec_target_dir_path = None
        self.wave_file = None
        # self.size_counter = 0

    def create(self, start_time, max_peak_freq_hz, max_peak_dbfs):
        """ """
        rec_file_prefix = self.wurb_settings.get_setting("filename_prefix")
        rec_type = self.wurb_settings.get_setting("rec_type")
        sampling_freq_hz = self.wurb_recorder.sampling_freq_hz
        if rec_type == "TE":
            sampling_freq_hz = int(sampling_freq_hz / 10.0)
        self.rec_target_dir_path = self.wurb_rpi.get_wavefile_target_dir_path()
        rec_datetime = self.get_datetime(start_time)
        rec_location = self.get_location()
        rec_type_str = self.create_rec_type_str(
            self.wurb_recorder.sampling_freq_hz, rec_type
        )

        # Peak info to filename.
        peak_info_str = ""
        if max_peak_freq_hz and max_peak_dbfs:
            peak_info_str += "_"  # "_Peak"
            peak_info_str += str(int(round(max_peak_freq_hz / 1000.0, 0)))
            peak_info_str += "kHz"
            peak_info_str += str(int(round(max_peak_dbfs, 0)))
            peak_info_str += "dB"

        if self.rec_target_dir_path is None:
            self.wave_file = None
            return

        # Filename example: "WURB1_20180420T205942+0200_N00.00E00.00_TE384.wav"
        filename = rec_file_prefix
        filename += "_"
        filename += rec_datetime
        filename += "_"
        filename += rec_location
        filename += "_"
        filename += rec_type_str
        filename += peak_info_str
        filename += ".wav"

        # Create directories.
        if not self.rec_target_dir_path.exists():
            self.rec_target_dir_path.mkdir(parents=True)
        # Open wave file for writing.
        filenamepath = pathlib.Path(self.rec_target_dir_path, filename)
        self.wave_file = wave.open(str(filenamepath), "wb")
        self.wave_file.setnchannels(1)  # 1=Mono.
        self.wave_file.setsampwidth(2)  # 2=16 bits.
        self.wave_file.setframerate(sampling_freq_hz)
        # Logging.
        target_path_str = str(self.rec_target_dir_path)
        target_path_str = target_path_str.replace("/media/pi/", "USB:")
        target_path_str = target_path_str.replace("/home/pi/", "SD-card:/home/pi/")
        message_rec_type = ""
        if rec_type == "TE":
            message_rec_type = "(TE) "
        message = "Sound file " + message_rec_type + "to: " + target_path_str
        self.wurb_logging.info(message, short_message=message)

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
        # Copy settings to target directory.
        try:
            if self.rec_target_dir_path is not None:
                from_dir = self.wurb_settings.settings_dir_path
                log_file_name = self.wurb_settings.settings_file_name
                from_file_path = pathlib.Path(from_dir, log_file_name)
                to_file_path = pathlib.Path(self.rec_target_dir_path, log_file_name)
                to_file_path.write_text(from_file_path.read_text())
        except Exception as e:
            print("Exception: Copy settings to wave file directory: ", e)

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

    def create_rec_type_str(self, sampling_freq_hz, rec_type):
        """ """
        try:
            sampling_freq_khz = sampling_freq_hz / 1000.0
            sampling_freq_khz = int(round(sampling_freq_khz, 0))
        except:
            sampling_freq_khz = "FS000"

        return rec_type + str(sampling_freq_khz)
