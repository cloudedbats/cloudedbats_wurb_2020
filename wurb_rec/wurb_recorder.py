#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import asyncio
import time
import wave
import pathlib
import psutil
from collections import deque

# CloudedBats.
import wurb_rec


class UltrasoundDevices(object):
    """ """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        # Ultrasound microphones supported by default:
        # - Pettersson: u256, u384, M500-384 and M500.
        # - Dodotronic: UltraMic 192K, 200K, 250K, 384K.
        self.default_name_part_list = ["Pettersson", "UltraMic", "EasyMic"]
        self.device_name = ""
        self.card_index = None
        self.sampling_freq_hz = 0
        self.check_interval_s = 5.0
        self.notification_event = None
        self.pettersson_m500 = wurb_rec.PetterssonM500()
        self.alsa_cards = wurb_rec.AlsaSoundCards()
        self.alsa_capture = None

    async def check_devices(self):
        """ For asyncio events. """
        try:
            # Check ALSA connected microphones.
            self.alsa_cards.update_card_lists()
            #
            await self.set_connected_device("", None, 0)
            device_name = ""
            card_index = None
            sampling_freq_hz = 0
            for device_name_part in self.default_name_part_list:
                try:
                    card_index = self.alsa_cards.get_capture_card_index_by_name(
                        device_name_part
                    )
                    if card_index != None:
                        card_dict = self.alsa_cards.get_card_dict_by_index(card_index)
                        device_name = card_dict.get("card_name", "")
                        sampling_freq_hz = self.alsa_cards.get_max_sampling_freq(
                            card_index
                        )
                        break
                except:
                    pass
            # Check if Pettersson M500.
            if not device_name:
                if self.pettersson_m500.is_m500_available():
                    device_name = self.pettersson_m500.get_device_name()
                    sampling_freq_hz = self.pettersson_m500.get_sampling_freq_hz()
            # Check if another ALSA mic. is specified in advanced settings.
            if not device_name:
                settings_device_name_part = os.getenv("WURB_REC_INPUT_DEVICE", "")
                settings_sampling_freq_hz = int(
                    os.getenv("WURB_REC_INPUT_DEVICE_FREQ_HZ", "0")
                )
                if settings_device_name_part:
                    device_name = ""
                    card_index = None
                    sampling_freq_hz = 0
                    try:
                        card_index = self.alsa_cards.get_capture_card_index_by_name(
                            settings_device_name_part
                        )
                        if card_index != None:
                            card_dict = self.alsa_cards.get_card_dict_by_index(
                                card_index
                            )
                            device_name = card_dict.get("card_name", "")
                            if settings_sampling_freq_hz > 0:
                                sampling_freq_hz = settings_sampling_freq_hz
                            else:
                                sampling_freq_hz = (
                                    self.alsa_cards.get_max_sampling_freq(card_index)
                                )
                    except Exception as e:
                        # Logging error.
                        message = "Recorder: check_devices: " + str(e)
                        self.wurb_manager.wurb_logging.error(
                            message, short_message=message
                        )
            # Done.
            await self.set_connected_device(device_name, card_index, sampling_freq_hz)

        except Exception as e:
            # Logging error.
            message = "Rec. check_devices: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def reset_devices(self):
        """ For asyncio events. """
        try:
            await self.set_connected_device("", None, 0)

        except Exception as e:
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
            # Logging error.
            message = "Recorder: get_notification_event: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def get_connected_device(self):
        """ """
        try:
            return self.device_name, self.sampling_freq_hz
        except Exception as e:
            # Logging error.
            message = "Recorder: get_connected_device: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def set_connected_device(self, device_name, card_index, sampling_freq_hz):
        """ """
        try:
            self.device_name = device_name
            self.card_index = card_index
            self.sampling_freq_hz = sampling_freq_hz
            # Create a new event and release all from the old event.
            old_notification_event = self.notification_event
            self.notification_event = asyncio.Event()
            if old_notification_event:
                old_notification_event.set()
        except Exception as e:
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
        self.wurb_audiofeedback = wurb_manager.wurb_audiofeedback
        self.rec_status = ""
        self.device_name = ""
        self.card_index = ""
        self.sampling_freq_hz = 0
        self.notification_event = None
        self.rec_start_time = None
        self.restart_activated = False
        # Config.
        self.max_adc_time_diff_s = 10  # Unit: sec.
        self.rec_length_s = 6  # Unit: sec.
        self.rec_timeout_before_restart_s = 30  # Unit: sec.

    async def get_notification_event(self):
        """ """
        try:
            if self.notification_event == None:
                self.notification_event = asyncio.Event()
            return self.notification_event
        except Exception as e:
            # Logging error.
            message = "Recorder: get_notification_event: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def get_rec_status(self):
        """ """
        try:
            return self.rec_status
        except Exception as e:
            # Logging error.
            message = "Recorder: get_rec_status: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def set_rec_status(self, rec_status):
        """ """
        try:
            self.rec_status = rec_status
            # Create a new event and release all from the old event.
            old_notification_event = self.notification_event
            self.notification_event = asyncio.Event()
            if old_notification_event:
                old_notification_event.set()
        except Exception as e:
            # Logging error.
            message = "Recorder: set_rec_status: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def set_device(self, device_name, card_index, sampling_freq_hz):
        """ """
        try:
            self.device_name = device_name
            self.card_index = card_index
            self.sampling_freq_hz = sampling_freq_hz
        except Exception as e:
            # Logging error.
            message = "Recorder: set_device: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def sound_source_worker(self):
        """ """
        self.rec_start_time = None
        loop = asyncio.get_event_loop()
        self.restart_activated = False

        # Pettersson M500, not compatible with ALSA.
        pettersson_m500 = wurb_rec.PetterssonM500(
            data_queue=self.from_source_queue,
            direct_target=self.wurb_audiofeedback,
        )
        if self.device_name == pettersson_m500.get_device_name():
            # Logging.
            await self.set_rec_status("Microphone is on.")
            try:
                buffer_size = int(self.sampling_freq_hz / 2)  # 0.5 sec.
                await pettersson_m500.initiate_capture(
                    card_index=self.card_index,
                    sampling_freq=self.sampling_freq_hz,
                    buffer_size=buffer_size,
                )
                await pettersson_m500.start_capture_in_executor()
            except asyncio.CancelledError:
                await pettersson_m500.stop_capture()
            except Exception as e:
                # Logging error.
                message = "Recorder: sound_source_worker: " + str(e)
                self.wurb_manager.wurb_logging.error(message, short_message=message)
            finally:
                await pettersson_m500.stop_capture()
                await self.set_rec_status("Recording finished.")
            return

        # Standard ASLA microphones.
        recorder_alsa = wurb_rec.AlsaSoundCapture(
            data_queue=self.from_source_queue,
            direct_target=self.wurb_audiofeedback,
        )
        # Logging.
        await self.set_rec_status("Microphone is on.")
        try:
            buffer_size = int(self.sampling_freq_hz / 2)  # 0.5 sec.
            await recorder_alsa.initiate_capture(
                card_index=self.card_index,
                sampling_freq=self.sampling_freq_hz,
                buffer_size=buffer_size,
            )
            await recorder_alsa.start_capture_in_executor()
        except asyncio.CancelledError:
            await recorder_alsa.stop_capture()
        except Exception as e:
            # Logging error.
            message = "Recorder: sound_source_worker: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)
        finally:
            await recorder_alsa.stop_capture()
            await self.set_rec_status("Recording finished.")
        return

    async def sound_process_worker(self):
        """ """

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
                        # item = await self.from_source_queue.get()
                        try:
                            item = await asyncio.wait_for(
                                self.from_source_queue.get(),
                                timeout=self.rec_timeout_before_restart_s,
                            )
                        except asyncio.TimeoutError:
                            # Check if restart already is requested.
                            if self.restart_activated:
                                return
                            # Logging.
                            message = (
                                "Lost connection with the microphone. Rec. restarted."
                            )
                            self.wurb_logging.warning(message, short_message=message)
                            # Restart recording.
                            self.restart_activated = True
                            loop = asyncio.get_event_loop()
                            asyncio.run_coroutine_threadsafe(
                                self.wurb_manager.restart_rec(),
                                loop,
                            )
                            await self.remove_items_from_queue(self.from_source_queue)
                            await self.from_source_queue.put(False)  # Flush.
                            return
                        #
                        try:
                            # print("REC PROCESS: ", item["adc_time"], item["data"][:5])
                            if item == None:
                                first_sound_detected == False
                                sound_detected_counter = 0
                                self.process_deque.clear()
                                await self.to_target_queue.put(None)  # Terminate.
                                break
                            elif item == False:
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
                                        self.wurb_manager.restart_rec(),
                                        loop,
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
                                    if max_peak_dbfs and peak_dbfs:
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
                    break
                except Exception as e:
                    # Logging error.
                    message = "Recorder: sound_process_worker(1): " + str(e)
                    self.wurb_manager.wurb_logging.error(message, short_message=message)

            # While end.

        except Exception as e:
            # Logging error.
            message = "Recorder: sound_process_worker(2): " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)
        finally:
            pass

    async def sound_target_worker(self):
        """Worker for sound targets. Mainly files or streams."""
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
                    break
                except Exception as e:
                    # Logging error.
                    message = "Recorder: sound_target_worker: " + str(e)
                    self.wurb_manager.wurb_logging.error(message, short_message=message)
        except Exception as e:
            # Logging error.
            message = "Recorder: sound_target_worker: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)
        finally:
            pass


class WaveFileWriter:
    """Each file is connected to a separate file writer object
    to avoid concurrency problems."""

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
        # Logging debug.
        message = "Filename: " + filename
        self.wurb_logging.debug(message=message)

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
                # Logging debug.
                self.wurb_logging.debug(message="File closed.")
        except Exception as e:
            # Logging error.
            message = "Recorder: Copy settings to wave file directory: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    def get_datetime(self, start_time):
        """ """
        datetime_str = time.strftime("%Y%m%dT%H%M%S%z", time.localtime(start_time))
        return datetime_str

    def get_location(self):
        """ """
        latlongstring = ""
        try:
            latitude_dd, longitude_dd = self.wurb_settings.get_valid_location()

            if latitude_dd >= 0.0:
                latlongstring += "N"
            else:
                latlongstring += "S"
            latlongstring += str(abs(latitude_dd))
            #
            if longitude_dd >= 0.0:
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
