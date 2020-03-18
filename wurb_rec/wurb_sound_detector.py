#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2018 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import logging
import numpy as np
import scipy.signal
import wurb_core
# # Check if librosa is available.
# librosa_available = False
# try:
#     import librosa
#     librosa_available = True
# except: pass

def default_settings():
    """ Available settings for the this module.
        This info is used to define default values and to 
        generate the wurb_settings_DEFAULT.txt file."""
    
    description = [
        '# Settings for sound detection algorithms.',
        '# Available detector algorithms:',
        '# - None: Records everything, silence included.',
        '# - Simple: Starts when sound above a specified frequency is detected.',
#         '# - (Test1: Under development.)',
        ]
    default_settings = [
        {'key': 'sound_detector', 'value': 'Simple'}, # None, Simple, Test1, ... 
        ]
    developer_settings = [
        {'key': 'sound_debug', 'value': 'N'}, 
        {'key': 'sound_simple_filter_min_hz', 'value': '15000'}, 
#         {'key': 'filter_max_hz', 'value': '150000'}, 
        {'key': 'sound_simple_threshold_dbfs', 'value': '-50'}, 
        {'key': 'sound_simple_window_size', 'value': '2048'}, 
        {'key': 'sound_simple_jump', 'value': '1000'}, 
        ]
    #
    return description, default_settings, developer_settings

class SoundDetector(object):
    """ """
    def __init__(self):
        """ """
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        
    def get_detector(self):
        """ Select detector depending in """
        sound_detector = self._settings.text('sound_detector')
        sound_detector = sound_detector.lower()
        #
        if sound_detector == 'none':
            return SoundDetectorNone()
        elif sound_detector == 'simple':
            return SoundDetectorSimple()
#         elif sound_detector == 'test1':
#             return SoundDetectorTest1()
        # Default.
        return SoundDetectorSimple()


class SoundDetectorBase():
    """ """
    def __init__(self):
        """ """
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        self._debug = self._settings.boolean('sound_debug')
        self.sampling_freq = self._settings.float('rec_sampling_freq_khz') * 1000
    
    def check_for_sound(self, time_and_data):
        """ Abstract. """
        
class SoundDetectorNone(SoundDetectorBase):
    """ Used for continous recordings, including silence. """
    def __init__(self):
        """ """
        super(SoundDetectorNone, self).__init__()
    
    def check_for_sound(self, _time_and_data):
        """ """
        # Always true. 
        return True
    
        
class SoundDetectorSimple(SoundDetectorBase):
    """ """
    def __init__(self):
        """ """
        super(SoundDetectorSimple, self).__init__()
        #
        self.filter_min_hz = self._settings.float('sound_simple_filter_min_hz')        
#         self.filter_max_hz = self._settings.float('sound_simple_filter_max_hz')        
        self.threshold_dbfs = self._settings.float('sound_simple_threshold_dbfs')        
        self.window_size = self._settings.integer('sound_simple_window_size')        
        self.jump_size = self._settings.integer('sound_simple_jump')        
        # self.window_size = 2048
        # self.jump_size = 1000

        # self.window_function = scipy.signal.blackmanharris(self.window_size)        
        self.window_function = scipy.signal.hann(self.window_size)        
        # Max db value in window. dbFS = db full scale. Half spectrum used.
        self.window_function_dbfs_max = np.sum(self.window_function) / 2 
        self.freq_bins_hz = np.arange((self.window_size / 2) + 1) / (self.window_size / self.sampling_freq)
    
    def check_for_sound(self, time_and_data):
        """ This is the old algorithm used during 2017. """
        _rec_time, raw_data = time_and_data
        #
        data_int16 = np.fromstring(raw_data, dtype=np.int16) # To ndarray.
        # self._work_buffer = np.concatenate([self._work_buffer, data_int16])
        self._work_buffer = data_int16
        #
        while len(self._work_buffer) >= self.window_size:
            # Get frame of window size.
            data_frame = self._work_buffer[:self.window_size] # Copy frame.
            self._work_buffer = self._work_buffer[self.jump_size:] # Cut the first jumped size.            
            # Transform to intervall -1 to 1 and apply window function.
            signal = data_frame / 32768.0 * self.window_function
            # From time domain to frequeny domain.
            spectrum = np.fft.rfft(signal)
            # High pass filter. Unit Hz. Cut below 15 kHz.
            spectrum[ self.freq_bins_hz < self.filter_min_hz ] = 0.000000001 # log10 does not like zero.
            # Convert spectrum to dBFS (bin values related to maximal possible value).
            dbfs_spectrum = 20 * np.log10(np.abs(spectrum) / self.window_function_dbfs_max)
            # Find peak and dBFS value for the peak.
            bin_peak_index = dbfs_spectrum.argmax()
            peak_db = dbfs_spectrum[bin_peak_index]
            # Treshold.
            if peak_db > self.threshold_dbfs:
                if self._debug:
                    peak_frequency_hz = bin_peak_index * self.sampling_freq / self.window_size
                    print('DEBUG: Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
                #
                return True
        #
        if self._debug:
            print('DEBUG: Silent.')
        #
        return False
        
# class SoundDetectorTest1(SoundDetectorBase):
#     """ """
#     def __init__(self):
#         """ """
#         super(SoundDetectorTest1, self).__init__()
#         #
#         # Create dsp4bats utils.
#         self.window_size = 1024
#         self.signal_util = wurb_core.SignalUtil(self.sampling_freq)
#         self.spectrum_util = wurb_core.DbfsSpectrumUtil(window_size=self.window_size,
#                                                    window_function='kaiser',
#                                                    kaiser_beta=14,
#                                                    sampling_freq=self.sampling_freq)
# 
#     def check_for_sound(self, time_and_data):
#         """ """
#         
#         test_time = time.time()
#         
#         _rec_time, raw_data = time_and_data
#         
#         time_filter_low_limit_hz = 15000
#         time_filter_high_limit_hz = None
#         scanning_results_dir = '/home/arnold/Desktop/WURB_REC_TEST'
#         scanning_results_file_name = 'detected_peks'
# 
#         # localmax_noise_threshold_factor = 1.2
#         localmax_noise_threshold_factor = 3.0
#         
#         localmax_jump_factor = 1000
#         localmax_frame_length = 1024
#         freq_jump_factor = 1000
#         freq_filter_low_hz = 15000
#         freq_threshold_dbfs = -50.0
#         freq_threshold_below_peak_db = 20.0
#         freq_max_frames_to_check = 200
#         freq_max_silent_slots = 8
#         samp_width = 2
#         self.debug=True
# 
#         
#         # Prepare output file for metrics. Create on demand.
#         metrics_file_name = pathlib.Path(scanning_results_file_name).stem + '_Metrics.txt'
#         out_header = self.spectrum_util.chirp_metrics_header()
#         out_file = None
#         # Read file.
#         checked_peaks_counter = 0
#         found_peak_counter = 0
#         acc_checked_peaks_counter = 0
#         acc_found_peak_counter = 0
#         
#         # Iterate over buffers.
#         if len(raw_data) > 0:
#             
#             if librosa_available:
#                 signal = librosa.util.buf_to_float(raw_data, n_bytes=samp_width)
#             else:
#                 # Error in find_localmax. Librosa not installed.
#                 return True
#             
#             # Get noise level for 1 sec buffer.
#             signal_noise_level = self.signal_util.noise_level(signal)
#             signal_noise_level_db = self.signal_util.noise_level_in_db(signal)
#             #
#             signal_filtered = self.signal_util.butterworth_filter(signal, 
#                                                          low_freq_hz=time_filter_low_limit_hz,
#                                                          high_freq_hz=time_filter_high_limit_hz)
#             # Get noise level for 1 sec buffer after filtering.
#             noise_level = self.signal_util.noise_level(signal_filtered)
#             noise_level_db = self.signal_util.noise_level_in_db(signal_filtered)
#             if self.debug:
#                 print('Noise level (before filter):', np.round(noise_level, 5), 
#                       '(', np.round(signal_noise_level, 5), ')', 
#                       ' Noise (db):', np.round(noise_level_db, 2), 
#                       '(', np.round(signal_noise_level_db, 5), ')'
#                       )
#             # Find peaks in time domain.
#             peaks = self.signal_util.find_localmax(signal=signal_filtered,
#                                               noise_threshold=noise_level * localmax_noise_threshold_factor, 
#                                               jump=int(self.sampling_freq/localmax_jump_factor), 
#                                               frame_length=localmax_frame_length) # Window size.
# 
#             checked_peaks_counter = len(peaks)
#             acc_checked_peaks_counter += len(peaks)
#             found_peak_counter = 0
#             
#             for peak_position in peaks:
#     
#                 # Extract metrics.
#                 result = self.spectrum_util.chirp_metrics(
#                                             signal=signal_filtered, 
#                                             peak_position=peak_position, 
#                                             jump_factor=freq_jump_factor, 
#                                             high_pass_filter_freq_hz=freq_filter_low_hz, 
#                                             threshold_dbfs = freq_threshold_dbfs, 
#                                             threshold_dbfs_below_peak = freq_threshold_below_peak_db, 
#                                             max_frames_to_check=freq_max_frames_to_check, 
#                                             max_silent_slots=freq_max_silent_slots, 
#                                             debug=False)
# 
#                 if result is False:
#                     continue # 
#                 else:
#                     result_dict = dict(zip(out_header, result))
#                     ## out_row = [result_dict.get(x, '') for x in out_header]
#                     # Add buffer steps to peak_signal_index, start_signal_index and end_signal_index.
#                     out_row = []
#                     for key in out_header:
#                         if '_signal_index' in key:
#                             # Adjust index if more than one buffer was read.
#                             index = int(result_dict.get(key, 0))
# ###                            index += buffer_number * signal_util.sampling_freq
#                             out_row.append(index)
#                         else:
#                             out_row.append(result_dict.get(key, ''))
#                     # Write to file.
#                     if out_file is None:
#                         ###out_file = pathlib.Path(scanning_results_dir, metrics_file_name).open('w')
#                         out_file = pathlib.Path(scanning_results_dir, metrics_file_name).open('a')
#                         out_file.write('\t'.join(map(str, out_header)) + '\n')# Read until end of file.
#                     #
#                     out_file.write('\t'.join(map(str, out_row)) + '\n')
#                     #
#                     found_peak_counter += 1
#                     acc_found_peak_counter += 1
# 
#             if self.debug:
#                 print('Buffer: Detected peak counter: ', str(found_peak_counter),
#                       '  of ', checked_peaks_counter, ' checked peaks.') 
#             
#         # Done.
#         if self.debug:
#             print('Summary: Detected peak counter: ', str(acc_found_peak_counter),
#                   '  of ', acc_checked_peaks_counter, ' checked peaks.') 
# 
#         if out_file is None:
#             print('\n', 'Warning: No detected peaks found. No metrics produced.', '\n') 
#         else: 
#             out_file.close()
# 
# 
#         print('DEBUG: Sound analysis time: ', time.time() - test_time)
# 
# 
#         if acc_found_peak_counter > 0:
#             sound_detected = True
#         else:
#             sound_detected = False
#         #
#         if sound_detected:
# #             peak_frequency_hz = bin_peak_index * 384000 / self_window_size
# #             self._logger.debug('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
# #             print('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
#             return True
#         #
#         print('DEBUG: Silent.')
#         return False

