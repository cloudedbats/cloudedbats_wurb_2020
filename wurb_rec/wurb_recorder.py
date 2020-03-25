#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import time
import asyncio
import sounddevice

# CloudedBats.
try:
    from wurb_rec.sound_stream_manager import SoundStreamManager
except:
    from sound_stream_manager import SoundStreamManager


class WurbRecManager(object):
    """ """

    def __init__(self):
        """ """
        try:
            self.rec_status = "Not started"
            self.notification_event = None
            self.ultrasound_devices = None
            self.wurb_recorder = None
        except Exception as e:
            print("Exception: ", e)

    async def startup(self):
        """ """
        try:
            self.ultrasound_devices = UltrasoundDevices()
            self.wurb_recorder = WurbRecorder()
            self.update_status_task = asyncio.create_task(self.update_status())
            await self.ultrasound_devices.start_checking_devices()
        except Exception as e:
            print("Exception: ", e)

    async def shutdown(self):
        """ """
        try:
            await self.ultrasound_devices.stop_checking_devices()
            await self.wurb_recorder.stop_streaming(stop_immediate=True)
        except Exception as e:
            print("Exception: ", e)

    async def start_rec(self):
        """ """
        try:
            await self.ultrasound_devices.stop_checking_devices()

            (
                device_name,
                sampling_freq_hz,
            ) = await self.ultrasound_devices.get_connected_device()
            if (len(device_name) > 1) and sampling_freq_hz > 180000:
                await self.wurb_recorder.set_device(device_name, sampling_freq_hz)
                await self.wurb_recorder.start_streaming()
            else:
                await self.wurb_recorder.set_rec_status(
                    "Not started, no valid microphone available."
                )
                await self.ultrasound_devices.start_checking_devices()
        except Exception as e:
            print("Exception: ", e)

    async def stop_rec(self):
        """ """
        try:
            await self.wurb_recorder.stop_streaming(stop_immediate=True)
            await self.ultrasound_devices.start_checking_devices()
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
        self.device_name = "-"
        self.sampling_freq_hz = 0
        self.check_interval_s = 1.0
        self.notification_event = None
        self.device_checker_task = None

    async def start_checking_devices(self):
        """ For asyncio events. """
        try:
            self.device_checker_task = asyncio.create_task(
                self.check_connected_devices()
            )
        except Exception as e:
            print("Exception: ", e)

    async def stop_checking_devices(self):
        """ For asyncio events. """
        try:
            self.device_checker_task.cancel()
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

    async def check_connected_devices(self):
        """ """
        print("DEBUG: check_connected_devices activated.")
        try:
            lock = asyncio.Lock()
            while True:
                async with lock:
                    # Refresh device list.
                    sounddevice._terminate()
                    sounddevice._initialize()

                await asyncio.sleep(0.2)

                device_dict = None
                device_name = "-"
                sampling_freq_hz = 0
                for device_name_part in self.name_part_list:
                    try:
                        device_dict = sounddevice.query_devices(device=device_name_part)
                        if device_dict:
                            device_name = device_dict["name"]
                            sampling_freq_hz = int(device_dict["default_samplerate"])
                        break
                    except:
                        pass
                if (self.device_name == device_name) and (
                    self.sampling_freq_hz == sampling_freq_hz
                ):
                    await asyncio.sleep(self.check_interval_s)
                else:
                    # Make the new values public.
                    await self.set_connected_device(device_name, sampling_freq_hz)
        except Exception as e:
            print("DEBUG: check_connected_devices exception: ", e)
        finally:
            print("DEBUG: check_connected_devices terminated.")


class WurbRecorder(SoundStreamManager):
    """ """

    def __init__(self):
        """ """
        super().__init__()
        self.rec_status = "Not started"
        self.device_name = "-"
        self.sampling_freq_hz = 0
        self.notification_event = None
        self.rec_stat_time = None

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
        self.rec_stat_time = None
        loop = asyncio.get_event_loop()
        sound_source_event = asyncio.Event()

        def audio_callback(indata, frames, cffi_time, status):
            """ This is called (from a separate thread) for each audio block. """
            try:
                if status:
                    print("DEBUG: audio_callback Status:", status)  # , file=sys.stderr)

                input_buffer_adc_time = cffi_time.inputBufferAdcTime
                if self.rec_stat_time == None:
                    input_buffer_adc_time = (
                        input_buffer_adc_time + 0.121
                    )  # Adjust first buffer.
                    self.rec_stat_time = time.time() - input_buffer_adc_time
                # buffer_time = float(int(self.rec_stat_time + input_buffer_adc_time)) # No decimals for sec.
                buffer_time = (
                    round(self.rec_stat_time + input_buffer_adc_time / 0.5) * 0.5
                )
                send_dict = {
                    "status": "",
                    "time": buffer_time,
                    "data": indata[:, 0],
                }
                print(
                    "DEBUG: audio_callback Data:",
                    len(indata[:, 0]),
                    "  Time: ",
                    buffer_time,
                )
            except Exception as e:
                print("EXCEPTION: audio_callback: ", e)
                loop.call_soon_threadsafe(sound_source_event.set)

        try:
            print(
                "DEBUG: Rec started: ", self.device_name, "   ", self.sampling_freq_hz
            )
            time_start = time.time()
            print("DEBUG: Rec start: ", time_start)

            blocksize = int(self.sampling_freq_hz / 2)

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

        # try:
        #     counter = 0
        #     while True:
        #         try:
        #             await asyncio.sleep(0.01)
        #             counter += 1
        #             print("DEBUG-1: Item: ", "A-" + str(counter))
        #             try:
        #                 self.from_source_queue.put_nowait(" A-" + str(counter))
        #             except asyncio.QueueFull:
        #                 self.removeItemsFromQueue(self.from_source_queue)
        #                 await self.from_source_queue.put(False)  # Flush.
        #         except asyncio.CancelledError:
        #             print("DEBUG: ", "sound_source_worker cancelled.")
        #             break
        #         except Exception as e:
        #             print("DEBUG: sound_source_worker exception: ", e)
        # finally:
        #     print("DEBUG: ", "sound_source_worker terminated.")


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
