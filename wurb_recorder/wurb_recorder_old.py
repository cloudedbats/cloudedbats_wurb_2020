#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2018 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import logging
import time
import wave
import pyaudio
import wurb_core

def default_settings():
    """ Available settings for the this module.
        This info is used to define default values and to 
        generate the wurb_settings_DEFAULT.txt file."""
    
    description = [
        '# Settings for the sound recorder.',
        ]
    default_settings = [
        {'key': 'rec_directory_path', 'value': '/media/usb0/wurb1_rec'}, 
        {'key': 'rec_filename_prefix', 'value': 'WURB1'},
        {'key': 'rec_format', 'value': 'FS'}, # "TE" (Time Expansion) ot "FS" (Full Scan).        
        {'key': 'rec_max_length_s', 'value': '20'},
        {'key': 'rec_buffers_s', 'value': 2.0}, # Pre- and post detected sound buffer size.
        # Hardware.
        {'key': 'rec_sampling_freq_khz', 'value': '384'}, 
        {'key': 'rec_microphone_type', 'value': 'USB'}, # "USB" or "M500".
        {'key': 'rec_part_of_device_name', 'value': 'Pettersson'}, 
        {'key': 'rec_device_index', 'value': 0}, # Not used if "rec_part_of_device_name" is found.
        ]
    developer_settings = [
        {'key': 'rec_source_debug', 'value': 'N'}, 
        {'key': 'rec_proc_debug', 'value': 'N'}, 
        {'key': 'rec_target_debug', 'value': 'N'}, 
        {'key': 'rec_source_adj_time_on_drift', 'value': 'Y'}, 
        ]
    #
    return description, default_settings, developer_settings

def get_device_list():
    """ Sound source util. Check connected sound cards. """
    py_audio = pyaudio.PyAudio()
    device_list = []
    device_count = py_audio.get_device_count()
    for index in range(device_count):
        info_dict = py_audio.get_device_info_by_index(index)
        # Sound card for input only.
        if info_dict['maxInputChannels'] != 0:
            device_list.append(info_dict['name'])
    #
    return device_list

def get_device_index(part_of_device_name):
    """ Sound source util. Lookup for device by name. """
    py_audio = pyaudio.PyAudio()
    device_count = py_audio.get_device_count()
    for index in range(device_count):
        info_dict = py_audio.get_device_info_by_index(index)
        if part_of_device_name in info_dict['name']:
            return index
    #
    return None


class WurbRecorder(object):
    """ """
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        self._sound_manager = None
#         self._is_recording = False
        
    def setup_sound_manager(self):
        """ """
        # Sound stream parts:
        # - Source
        self._sound_source = None
        if self._settings.text('rec_microphone_type') == 'M500':
            # The Pettersson M500 microphone is developed for Windows. Special code to handle M500.
            self._sound_source = wurb_core.SoundSourceM500(callback_function=self._callback_function)
        else:
            # Generic USB microphones, including Pettersson M500-384.
            self._sound_source = wurb_core.SoundSource(callback_function=self._callback_function)
        # - Process.
        self._sound_process = wurb_core.SoundProcess(callback_function=self._callback_function)
        # - Target.
        self._sound_target = wurb_core.SoundTarget(callback_function=self._callback_function)
        # - Manager.
        self._sound_manager = wurb_core.SoundStreamManager(
                                    self._sound_source, 
                                    self._sound_process, 
                                    self._sound_target)

    def start_recording(self):
        """ """
        if self._sound_manager:
            self._sound_manager.start_streaming()

    def stop_recording(self, stop_immediate=False):
        """ """
        if self._sound_manager:
            self._sound_manager.stop_streaming(stop_immediate)


class SoundSource(wurb_core.SoundSourceBase):
    """ Subclass of SoundSourceBase. """
    
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        super(SoundSource, self).__init__()
        #
        self._debug = self._settings.boolean('rec_source_debug')
        self._rec_source_adj_time_on_drift = self._settings.boolean('rec_source_adj_time_on_drift')
        #
        self._pyaudio = pyaudio.PyAudio()
        self._stream = None
        #
        self.read_settings()
        
    def read_settings(self):
        """ Called from base class. """
        if self._settings.text('rec_microphone_type') == 'M500': 
            # For Pettersson M500. Overrides settings.
            self._sampling_freq_hz = 500000
        else:
            # From settings. Defaults for Pettersson M500-384.
            self._sampling_freq_hz = self._settings.integer('rec_sampling_freq_khz') * 1000
        # Sound card.
        in_device_name = self._settings.text('rec_part_of_device_name')
        in_device_index = self._settings.integer('rec_device_index') # Default=0. First recognized sound card.
        if in_device_name:
            self._in_device_index = wurb_core.get_device_index(in_device_name)
        else:
            self._in_device_index = in_device_index

        self._logger.info('Recorder: Sampling frequency (hz): ' + str(self._sampling_freq_hz))
         
    def _setup_pyaudio(self):
        """ """
        # Initiate PyAudio.
        try:
            self._stream = self._pyaudio.open(
                format = self._pyaudio.get_format_from_width(2), # 2=16 bits.
                channels = 1, # 1=Mono.
                rate = self._sampling_freq_hz,
                frames_per_buffer = self._sampling_freq_hz, # Buffer 1 sec.
                input = True,
                output = False,
                input_device_index = self._in_device_index,
                start = False,
            )
        except Exception as e:
            self._stream = None
            self._logger.error('Recorder: Failed to create stream: ' + str(e))
            # Report to state machine.
            if self._callback_function:
                self._callback_function('rec_source_error')
            return

    def source_exec(self):
        """ Called from base class. """
        
        if self._stream is None:
            self._setup_pyaudio()
        #
        if self._stream: 
            self._active = True
            self._stream_active = True
            self._stream_time_s = time.time()
            self._stream.start_stream()
        else:
            self._logger.error('Recorder: Failed to read stream.')
            return
        # 
        buffer_size = int(self._sampling_freq_hz / 2)
        
        # Main source loop.
        try:
            data = self._stream.read(buffer_size) #, exception_on_overflow=False)
            while self._active and data:
                # Add time and check for time drift.
                self._stream_time_s += 0.5 # One buffer is 0.5 sec.
                if (self._stream_time_s > (time.time() + 10)) or \
                   (self._stream_time_s < (time.time() - 10)):
                    #
                    time_diff_s = int(time.time() - self._stream_time_s)
                    if self._rec_source_adj_time_on_drift:
                        self._logger.warning('Recorder: Rec. time adjusted. Diff: ' + str(time_diff_s) + ' sec.')
                        self._stream_time_s = time.time()
                    else:
                        self._logger.debug('Recorder: Rec. time drift. Diff: ' + str(time_diff_s) + ' sec.')                    
                # Push time and data buffer.
                self.push_item((self._stream_time_s, data)) 
                #
                data = self._stream.read(buffer_size) #, exception_on_overflow=False)
        except Exception as e:
            self._logger.error('Recorder: Failed to read stream: ' + str(e))

        # Main loop terminated.
        self._logger.debug('Source: Source terminated.')
        self.push_item(None)
        #
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except: 
                self._logger.error('Recorder: Pyaudio stream stop/close failed.')
            self._stream = None

class SoundSourceM500(SoundSource):
    """ Subclass of SoundSource for the Pettersson M500 microphone. """
    def __init__(self, callback_function=None):
        """ """
        super(SoundSourceM500, self).__init__(callback_function)
        #
        self._debug = self._settings.boolean('rec_source_debug')
        self._rec_source_adj_time_on_drift = self._settings.boolean('rec_source_adj_time_on_drift')
        #
        self._m500batmic = None
        
    def source_exec(self):
        """ For the Pettersson M500 microphone. """
        self._active = True
        #
        try:
            if not self._m500batmic:
                self._m500batmic = wurb_core.PetterssonM500BatMic()
            #
            self._stream_active = True
            #
            self._stream_time_s = time.time()
            self._m500batmic.start_stream()
            self._m500batmic.led_on()

        except Exception as e:
            self._logger.error('Recorder: Failed to create stream: ' + str(e))
            # Report to state machine.
            if self._callback_function:
                self._callback_function('rec_source_error')
            return
        # 
        # buffer_size = int(self._sampling_freq_hz / 2)
        buffer_size = int(self._sampling_freq_hz)
        
        # Main source loop.
        data = self._m500batmic.read_stream().tostring()
        data_array = data
        while self._active and (len(data) > 0):
            # Push 0.5 sec each time. M500 can't deliver that size directly.
            if len(data_array) >= buffer_size:
                # Add time and check for time drift.
                self._stream_time_s += 0.5 # One buffer is 0.5 sec.
                if (self._stream_time_s > (time.time() + 10)) or \
                   (self._stream_time_s < (time.time() - 10)):
                    #
                    time_diff_s = int(time.time() - self._stream_time_s)
                    if self._rec_source_adj_time_on_drift:
                        self._logger.warning('Recorder: Rec. time adjusted. Diff: ' + str(time_diff_s) + ' sec.')                    
                        self._stream_time_s = time.time()
                    else:
                        self._logger.debug('Recorder: Rec. time drift. Diff: ' + str(time_diff_s) + ' sec.')                    
                # Push time and data buffer.
                self.push_item((self._stream_time_s, data_array[0:buffer_size])) 
                data_array = data_array[buffer_size:]
            #
            data = self._m500batmic.read_stream().tostring()
            data_array += data
        #
        self._logger.debug('Source M500: Source terminated.')
        self.push_item(None)
        #
        self._m500batmic.stop_stream()


class SoundProcess(wurb_core.SoundProcessBase):
    """ Subclass of SoundProcessBase. """
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        super(SoundProcess, self).__init__()
        #
        self._debug = self._settings.boolean('rec_proc_debug')
        self._rec_buffers_s = self._settings.float('rec_buffers_s')

    def process_exec(self):
        """ Called from base class. """
        self._active = True
        # Get sound detector based on user settings.
        sound_detector = None
        try:
            sound_detector = wurb_core.SoundDetector().get_detector()
        except Exception as e:
            sound_detector = None
            self._logger.error('Recorder: SoundDetector exception: ', str(e))

        sound_detected = False
        #
        buffer_size = int(self._rec_buffers_s * 2.0) # Buffers are of 0.5 sec length.
        #
        silent_buffer = []
        silent_counter = 9999 # Don't send before sound detected.
        
        try:
            while self._active:
                time_and_data = self.pull_item()
    
                if time_and_data is None:
                    self._logger.debug('Rec-process terminated.')
                    self._active = False
                    # Terminated by previous step.
                    self.push_item(None)
                else:
    #                 self.process_buffer(raw_data)
                    try:
                        sound_detected = sound_detector.check_for_sound(time_and_data)
                    except Exception as e:
                        sound_detected = True
                    #
                    if sound_detected:
                        
                        if self._debug:
                            print('DEBUG: Sound detected.')
                        
                        # Send pre buffer if this is the first one.
                        if len(silent_buffer) > 0:
                            for silent_time_and_data in silent_buffer:
                                self.push_item(silent_time_and_data)
                            #
                            silent_buffer = []
                        # Send buffer.    
                        self.push_item(time_and_data)
                        silent_counter = 0
                    else:
                        
                        if self._debug:
                            print('DEBUG: Sound not detected. Counter: ', silent_counter)
                        
                        if silent_counter < buffer_size: # Unit 0.5 sec.
                            # Send after sound detected.
                            self.push_item(time_and_data)
                            silent_counter += 1
                        elif silent_counter < (buffer_size * 2): # Unit 0.5 sec.
                            # Accept longer silent part between pulses.
                            silent_buffer.append(time_and_data)
                            silent_counter += 1
                        else:
                            # Silent, but store in pre buffer.
                            self.push_item(False)
                            silent_buffer.append(time_and_data)
                            while len(silent_buffer) > buffer_size: # Unit 0.5sec.
                                silent_buffer.pop(0)
        except Exception as e:
            self._logger.error('Recorder: Sound process_exec exception: ', str(e))
                    


class SoundTarget(wurb_core.SoundTargetBase):
    """ Subclass of SoundTargetBase. """
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        super(SoundTarget, self).__init__()
        # From settings. 
        self._dir_path = self._settings.text('rec_directory_path')
        self._filename_prefix = self._settings.text('rec_filename_prefix')
        rec_max_length_s = self._settings.integer('rec_max_length_s')
        self._rec_max_length = rec_max_length_s * 2
        # Default for latitude/longitude in the decimal degree format.
        self._latitude = float(self._settings.float('default_latitude'))
        self._longitude = float(self._settings.float('default_longitude'))
        # Different microphone types.
        if self._settings.text('rec_microphone_type') == 'M500':
            # For M500 only.
            if self._settings.text('rec_format') == 'TE':
                self._filename_rec_type = 'TE500'
                self._out_sampling_rate_hz = 50000
            else:
                self._filename_rec_type = 'FS500'
                self._out_sampling_rate_hz = 500000
        else:
            # For standard USB, inclusive M500-384.
            if self._settings.text('rec_format') == 'TE':
                self._filename_rec_type = 'TE' + self._settings.text('rec_sampling_freq_khz')
                self._out_sampling_rate_hz = self._settings.integer('rec_sampling_freq_khz') * 100
            else:
                self._filename_rec_type = 'FS' + self._settings.text('rec_sampling_freq_khz')
                self._out_sampling_rate_hz = self._settings.integer('rec_sampling_freq_khz') * 1000
        #
        self._total_start_time = None
        self._internal_buffer_list = []
        self._write_thread_active = False
        self._active = False
    
    def target_exec(self):
        """ Called from base class. """
        self._active = True
        wave_file_writer = None
        # Use buffer to increase write speed.
        item_list = []
        item_list_max = 5 # Unit 0.5 sec. Before flush to file.
        item_counter = 0
        #
        try:
            while self._active:
                item = self.pull_item()
                
                # "None" indicates terminate by previous part in chain.
                if item is None:
                    self._active = False # Terminated by previous step.
                    continue              

                # "False" indicates silent part. Close file until not silent. 
                elif item is False:
                    if wave_file_writer:
                        # Flush buffer.
                        joined_items = b''.join(item_list)
                        item_list = []
                        wave_file_writer.write(joined_items)
                        # Close.
                        wave_file_writer.close()
                        wave_file_writer = None
                        item_counter = 0
                    #
                    continue
                
                # Normal case, write frames.
                else:
                    _rec_time, data = item # "rec_time" not used.

                    # Open file if first after silent part.
                    if not wave_file_writer:
                        wave_file_writer = WaveFileWriter(self)
                        
                    # Check if max rec length was reached.
                    if item_counter >= self._rec_max_length: 
                        if wave_file_writer:
                            # Flush buffer.
                            joined_items = b''.join(item_list)
                            item_list = []
                            wave_file_writer.write(joined_items)
                            # Close the old one.
                            wave_file_writer.close()
                            wave_file_writer = None
                            item_counter = 0
                            # Open a new file.
                            wave_file_writer = WaveFileWriter(self)
                                
                    # Append data to buffer
                    item_list.append(data)
                    item_counter += 1
                    
                    # Flush buffer when needed.
                    if len(item_list) >= item_list_max:
                        if wave_file_writer:
                            joined_items = b''.join(item_list)
                            item_list = []
                            wave_file_writer.write(joined_items)
            
            # Thread terminated.
            if wave_file_writer:
                if len(item_list) > 0:
                    # Flush buffer.
                    joined_items = b''.join(item_list)
                    item_list = []
                    wave_file_writer.write(joined_items)
                #
                wave_file_writer.close()
                wave_file_writer = None
        #
        except Exception as e:
            self._logger.error('Recorder: Sound target exception: ' + str(e))
            self._active = False # Terminate
            if self._callback_function:
                self._callback_function('rec_target_error')


class WaveFileWriter():
    """ Each file is connected to a separate object to avoid concurrency problems. """
    def __init__(self, sound_target_obj):
        """ """
        self._wave_file = None
        self._sound_target_obj = sound_target_obj
        self._size_counter = 0 
        
        # Create file name.
        # Default time and position.
        datetimestring = time.strftime("%Y%m%dT%H%M%S%z")
        latlongstring = '' # Format: 'N56.78E12.34'
        try:
            if sound_target_obj._latitude >= 0: 
                latlongstring += 'N' 
            else: 
                latlongstring += 'S'
            latlongstring += str(abs(sound_target_obj._latitude))
            #
            if sound_target_obj._longitude >= 0: 
                latlongstring += 'E' 
            else: 
                latlongstring += 'W'
            latlongstring += str(abs(sound_target_obj._longitude))
        except:
            latlongstring = 'N00.00E00.00'
        
        # Use GPS time if available.
        datetime_local_gps = wurb_core.WurbGpsReader().get_time_local_string()
        if datetime_local_gps:
            datetimestring = datetime_local_gps
        # Use GPS position if available.
        latlong = wurb_core.WurbGpsReader().get_latlong_string()
        if latlong:
            latlongstring = latlong
            
        # Filename example: "WURB1_20180420T205942+0200_N00.00E00.00_TE384.wav"
        filename =  sound_target_obj._filename_prefix + \
                    '_' + \
                    datetimestring + \
                    '_' + \
                    latlongstring + \
                    '_' + \
                    sound_target_obj._filename_rec_type + \
                    '.wav'
        filenamepath = os.path.join(sound_target_obj._dir_path, filename)
        #
        if not os.path.exists(sound_target_obj._dir_path):
            os.makedirs(sound_target_obj._dir_path) # For data, full access.
        # Open wave file for writing.
        self._wave_file = wave.open(filenamepath, 'wb')
        self._wave_file.setnchannels(1) # 1=Mono.
        self._wave_file.setsampwidth(2) # 2=16 bits.
        self._wave_file.setframerate(sound_target_obj._out_sampling_rate_hz)
        #
        sound_target_obj._logger.info('Recorder: New sound file: ' + filename)
        
    def write(self, buffer):
        """ """
        self._wave_file.writeframes(buffer)
        self._size_counter += len(buffer) / 2 # Count frames.

    def close(self):
        """ """
        if self._wave_file is not None:
            self._wave_file.close()
            self._wave_file = None 

            length_in_sec = self._size_counter / self._sound_target_obj._out_sampling_rate_hz
            self._sound_target_obj._logger.info('Recorder: Sound file closed. Length:' + str(length_in_sec) + ' sec.')

    

# === TEST ===    
if __name__ == "__main__":
    """ """
    import sys
    import pathlib
    path = ".."
    sys.path.append(path)
    
    # Logging to standard output.
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    
    #
    settings = wurb_core.WurbSettings()
    (desc, default, dev) = wurb_core.wurb_recorder.default_settings()
    settings.set_default_values(desc, default, dev)
    (desc, default, dev) = wurb_core.wurb_gps_reader.default_settings()
    settings.set_default_values(desc, default, dev)
    #
    internal_setting_path = pathlib.Path('../wurb_settings/user_settings.txt')
    settings.load_settings(internal_setting_path)
    #
    recorder = wurb_core.WurbRecorder()
    recorder.setup_sound_manager()
    #
    print('TEST - started.')
    recorder.start_recording()
    time.sleep(5.5)
    recorder.stop_recording()
    print('TEST - ended.')


