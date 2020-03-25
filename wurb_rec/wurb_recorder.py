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
        self.rec_status = "Not started"
        self.notification_event = None
        self.ultrasound_devices = None
        self.wurb_recorder = None

    def startup(self):
        """ """
        self.ultrasound_devices = UltrasoundDevices()
        self.wurb_recorder = WurbRecorder()

        self.update_status_task = asyncio.create_task(self.update_status())

        self.ultrasound_devices.start_checking_devices()

    def shutdown(self):
        """ """
        self.ultrasound_devices.stop_checking_devices()
        self.wurb_recorder.stop_streaming(stop_immediate=True)

    def start_rec(self):
        """ """
        self.ultrasound_devices.stop_checking_devices()
        self.wurb_recorder.start_streaming()

    def stop_rec(self):
        """ """
        self.wurb_recorder.stop_streaming(stop_immediate=True)
        self.ultrasound_devices.start_checking_devices()

    def get_notification_event(self):
        """ """
        if self.notification_event == None:
            self.notification_event = asyncio.Event()
        return self.notification_event

    def get_status_dict(self):
        """ """
        status_dict = {
            "rec_status": self.wurb_recorder.rec_status,
            "device_name": self.ultrasound_devices.device_name,
            "sample_rate": str(self.ultrasound_devices.sampling_freq_hz),
        }
        return status_dict

    async def update_status(self):
        """ """
        print("DEBUG: update_status activated.")
        try:
            while True:
                device_notification = self.ultrasound_devices.get_notification_event()
                # rec_notification = self.wurb_recorder.get_notification_event()
                events = [
                    device_notification.wait(),
                    # rec_notification.wait(),
                ]
                await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED) #, timeout=2.0)
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

    def start_checking_devices(self):
        """ For asyncio events. """
        self.device_checker_task = asyncio.create_task(self.check_connected_devices())

    def stop_checking_devices(self):
        """ For asyncio events. """
        self.device_checker_task.cancel()

    def get_notification_event(self):
        """ """
        if not self.notification_event:
            self.notification_event = asyncio.Event()
        return self.notification_event

    def get_connected_device(self):
        """ """
        return self.device_name, self.sampling_freq_hz

    def set_connected_device(self, device_name, sampling_freq_hz):
        """ """
        print("DEBUG: set_connected_device called.")
        self.device_name = device_name
        self.sampling_freq_hz = sampling_freq_hz
        # Create a new event and release all from the old event.
        old_notification_event = self.notification_event
        self.notification_event = asyncio.Event()
        if old_notification_event:
            old_notification_event.set()

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
                    self.set_connected_device(device_name, sampling_freq_hz)
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
        # self.notification_event = None
        self.rec_stat_time = None


    async def soundSourceWorker(self):
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
                    print("DEBUG: audio_callback Status:", status) # , file=sys.stderr)

                input_buffer_adc_time = cffi_time.inputBufferAdcTime
                if self.rec_stat_time == None:
                    input_buffer_adc_time = input_buffer_adc_time + 0.121 # Adjust first buffer.
                    self.rec_stat_time = time.time() - input_buffer_adc_time
                # buffer_time = float(int(self.rec_stat_time + input_buffer_adc_time)) # No decimals for sec.
                buffer_time = round(self.rec_stat_time + input_buffer_adc_time / 0.5) * 0.5 
                send_dict = {
                    "status": "", 
                    "time": buffer_time, 
                    "data": indata[:, 0], 
                }

                print("DEBUG: audio_callback Data:", len(indata[:, 0]), "  Time: ", buffer_time)

#                loop.call_soon_threadsafe(self.from_source_queue.put_nowait, send_dict)



            except Exception as e:
                print("EXCEPTION: audio_callback: ", e)
                loop.call_soon_threadsafe(sound_source_event.set)


        try:
            print("DEBUG-1")
            time_start = time.time()
            print("time_start: ", time_start)

            try: 
                stream = sounddevice.InputStream(
                    device="Pettersson", channels=1,
                    blocksize=192000, 
                    #blocksize=384000, 
                    #blocksize=256000, 
                    # latency="high", 
                    dtype='int16', 
                    samplerate=384000, 
                    callback=audio_callback,
                    )
            except:
                stream = sounddevice.InputStream(
                    device="UltraMic", channels=1,
                    blocksize=96000, 
                    # latency="high", 
                    dtype='int16', 
                    samplerate=192000, 
                    callback=audio_callback,
                    )

            print("DEBUG-2")

            with stream:
                await sound_source_event.wait()

            print("DEBUG-3")

        except asyncio.CancelledError:
            print("DEBUG: ", "soundSourceWorker cancelled.")
            # break
        except Exception as e:
            print("DEBUG: soundSourceWorker exception: ", e)

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
        #             print("DEBUG: ", "soundSourceWorker cancelled.")
        #             break
        #         except Exception as e:
        #             print("DEBUG: soundSourceWorker exception: ", e)
        # finally:
        #     print("DEBUG: ", "soundSourceWorker terminated.")

# === MAIN - for test ===
async def main():
    """ """
    print("Test started.")
    recorder = WurbRecorder()
    print("Test 1.")
    print("DEBUG: Check status: ", recorder.get_rec_status())
    await asyncio.sleep(0.1)
    print("Test 2.")
    recorder.start_streaming()
    await asyncio.sleep(10.5)
    print("Test 3.")
    await recorder.stop_streaming(stop_immediate=True)
    print("Test 4.")
    await recorder.wait_for_shutdown()
    print("Test finished.")


if __name__ == "__main__":
    """ """
    asyncio.run(main(), debug=True)