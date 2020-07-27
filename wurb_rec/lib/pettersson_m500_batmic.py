#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2016-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import time
import datetime
import wave
import array
import usb.core


class PetterssonM500BatMic(object):
    """ Class used for control of the Pettersson M500 USB Ultrasound Microphone. 
        More info at http://batsound.com/
        
        Normally the M500 should be accessed from Windows systems, but this class 
        makes it possible to call it from Linux.
        
        Installation instructions for pyusb: https://github.com/walac/pyusb
        
        Since pyusb access hardware directly 'udev rules' must be created. 
        During test it is possible to run it as a 'sudo' user. Example for
        execution of the test case at the end of this file:
        > sudo python3 pettersson_m500_batmic.py 
        
        How to create an udev rule on a Raspberry Pi running Raspbian:
          Go to: /etc/udev/rules.d/
          and add a file called: pettersson_m500_batmic.rules
          containing the following row:
          SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", MODE="0664", GROUP="m500batmic"
         
          Then add the usergroup m500batmic to the user.
        
        More info about adding 'udev rules':
        http://stackoverflow.com/questions/3738173/why-does-pyusb-libusb-require-root-sudo-permissions-on-linux 
    """

    def __init__(self):
        """ """
        self.clear()

    def clear(self):
        """ """
        self.device = None
        self.endpoint_out = None
        self.endpoint_in = None

    def is_available(self):
        """ Returns True if available. """
        self.clear()
        self.device = usb.core.find(idVendor=0x287D, idProduct=0x0146)
        if self.device:
            return True
        else:
            self.clear()
            return False

    def reset(self):
        """ Returns True if available. """
        self.device = usb.core.find(idVendor=0x287D, idProduct=0x0146)
        if self.device:
            self.device.reset()
            self.clear()
            return True
        else:
            self.clear()
            return False

    def start_stream(self):
        """ Returns True if ok. """
        return self.send_command("01")

    def stop_stream(self):
        """ """
        self.send_command("04")

    def led_on(self):
        """ Returns True if ok. """
        return self.send_command("03")

    def led_flash(self):
        """ Returns True if ok. """
        return self.send_command("02")

    def init_sound_card(self):
        """ Returns True if ok. """
        self.clear()
        try:
            # Vendor and product number for Pettersson M500.
            self.device = usb.core.find(idVendor=0x287D, idProduct=0x0146)
            if self.device:
                # Use first configuration.
                self.device.set_configuration()
                configuration = self.device.get_active_configuration()
                interface = configuration[(0, 0)]
                # List all endpoints.
                #         decriptors = usb.util.find_descriptor(interface, find_all=True)
                #         for descr in decriptors:
                #             print(str(descr))
                # Find endpoint-OUT. For commands.
                self.endpoint_out = usb.util.find_descriptor(
                    interface,
                    custom_match=lambda e: usb.util.endpoint_direction(
                        e.bEndpointAddress
                    )
                    == usb.util.ENDPOINT_OUT,
                )
                # Find endpoint-IN. For sound stream.
                self.endpoint_in = usb.util.find_descriptor(
                    interface,
                    custom_match=lambda e: usb.util.endpoint_direction(
                        e.bEndpointAddress
                    )
                    == usb.util.ENDPOINT_IN,
                )
                return True
            else:
                return False
        except Exception as e:
            print("EXCEPTION: M500 init_sound_card: ", e)
            return False

    def read_stream(self):
        """ Returns empty list if not ok. """
        try:
            if not self.endpoint_in:
                self.init_sound_card()
            if self.endpoint_in:
                # Buffer must be an exponent of 2.
                # buffer = self.endpoint_in.read(0x10000, 2000) # Size = 65536, timeout = 2 sec.
                buffer = self.endpoint_in.read(
                    0x20000, 2000
                )  # Size = 131072, timeout = 2 sec.
                # buffer = self.endpoint_in.read(0x40000, 4000) # Size = 262144, timeout = 2 sec.
                return buffer
            else:
                return array.array("B")  # Empty array.
        except Exception as e:
            # print("EXCEPTION: M500 read_stream: ", e)
            return array.array("B")  # Empty array.

    def send_command(self, command):
        """ Commands: '01': Stream on, '02': LED flash, '03': LED on, '04': Stream off. 
            Returns True if ok. 
        """
        try:
            if not self.endpoint_in:
                self.init_sound_card()
            if self.endpoint_in:
                # Build command string.
                cmd_string = "4261744d6963"  # Signature: ASCII for 'BatMic'.
                cmd_string += command
                cmd_string += (
                    "20a10700"  # Sfreq. 500000 Hz = x07a120, reversed byte order.
                )
                cmd_string += "00400000"  # Ssize, reversed byte order.
                cmd_string += "00000000"  # Filter.
                cmd_string += "00"  # Stereo.
                cmd_string += "00"  # Trig.
                cmd_string += "ff" if command in ["02", "03"] else "00"  # Infinite.
                cmd_string += "00000000000000000000"  # Fill, 10 bytes.
                # Send command to M500.
                byte_list = bytes.fromhex(cmd_string)
                self.endpoint_out.write(
                    byte_list, 1000
                )  # Timeout = 1 sec. # For Python 3.
                return True
            else:
                return False
        except Exception as e:
            print("EXCEPTION: M500 send_command: ", e)
            return False


### FOR TEST. ###
if __name__ == "__main__":
    """ """
    # Set record length for this test.
    rec_length_in_minutes = 0.1
    try:
        batmic = PetterssonM500BatMic()
        try:
            print("M500 rec. started (1).")
            # Create wave outfile.
            wave_file = wave.open("pettersson-m500(1).wav", "w")
            wave_file.setnchannels(1)  # 1 = Mono.
            wave_file.setsampwidth(2)  # 2 = 16 bits.
            wave_file.setframerate(
                50000
            )  # TE, Time Expansion 10x (sampling freq. 50kHz instead of 500kHz).
            # Start M500 stream and LED.
            batmic.start_stream()
            batmic.led_on()  # Alternative: batmic.led_flash()
            # Calculate end time.
            end_time = datetime.datetime.now() + datetime.timedelta(
                minutes=rec_length_in_minutes
            )
            print(
                "M500 rec. started at: "
                + str(datetime.datetime.now())
                + ", end time: "
                + str(end_time)
            )
            # Write to wave file.
            while datetime.datetime.now() < end_time:
                data = batmic.read_stream()
                wave_file.writeframes(data.tostring())
            # Stop M500 and wave file.
            batmic.stop_stream()
            wave_file.close()
            print("M500 rec. finished (1).")

            time.sleep(5)

            # batmic = PetterssonM500BatMic()
            batmic.stop_stream()

            print("M500 rec. started (2).")
            # Create wave outfile.
            wave_file = wave.open("pettersson-m500(2).wav", "w")
            wave_file.setnchannels(1)  # 1 = Mono.
            wave_file.setsampwidth(2)  # 2 = 16 bits.
            wave_file.setframerate(500000)  # FS, full Scan.
            # Start M500 stream and LED.
            batmic.start_stream()
            batmic.led_on()  # Alternative: batmic.led_flash()
            # Calculate end time.
            end_time = datetime.datetime.now() + datetime.timedelta(
                minutes=rec_length_in_minutes
            )
            print(
                "M500 rec. started at: "
                + str(datetime.datetime.now())
                + ", end time: "
                + str(end_time)
            )
            # Write to wave file.
            while datetime.datetime.now() < end_time:
                data = batmic.read_stream()
                wave_file.writeframes(data.tostring())
            # Stop M500 and wave file.
            batmic.stop_stream()
            wave_file.close()
            print("M500 rec. finished (2).")
        finally:
            batmic.stop_stream()
    except Exception as e:
        print("M500 test failed: " + str(e))
        raise  # Raise exception again to show traceback.

