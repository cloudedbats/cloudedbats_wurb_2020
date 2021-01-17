#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import logging
import numpy as np
import scipy.signal


class SoundDetection(object):
    """ """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.wurb_recorder = wurb_manager.wurb_recorder
        self.wurb_settings = wurb_manager.wurb_settings
        self.wurb_logging = wurb_manager.wurb_logging

    def get_detection(self):
        """ Select detection algorithm. """
        algorithm = self.wurb_settings.get_setting("detection_algorithm")
        if algorithm == "detection-none":
            detection_object = SoundDetectionNone(self.wurb_manager)
        elif algorithm == "detection-simple":
            detection_object = SoundDetectionSimple(self.wurb_manager)
        else:
            # Use the most common as default.
            detection_object = SoundDetectionSimple(self.wurb_manager)
        #
        detection_object.config()
        return detection_object


class SoundDetectionBase:
    """ """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.wurb_recorder = wurb_manager.wurb_recorder
        self.wurb_settings = wurb_manager.wurb_settings
        self.wurb_logging = wurb_manager.wurb_logging

    def config(self, _time_and_data):
        """ Abstract. """
        pass  # Should be overridden.

    def check_for_sound(self, time_and_data):
        """ Abstract. """
        # Returns "is sound", "freq. at peak", "dBFS at peak".
        return True, None, None  # Should be overridden.

    def manual_triggering_check(self, sound_detected):
        """ """
        rec_mode = self.wurb_settings.get_setting("rec_mode")
        # Check if "record everyting" mode.
        if rec_mode in ["mode-on", "mode-scheduler-on"]:
            return True
        # Check manual mode triggering.
        if rec_mode == "mode-manual":
            if self.wurb_manager.manual_trigger_activated:
                # Reset value.
                self.wurb_manager.manual_trigger_activated = False
                return True
            else:
                return False
        else:
            return sound_detected


class SoundDetectionNone(SoundDetectionBase):
    """ Used for continuous recordings, including silence. """

    def __init__(self, wurb_manager):
        """ """
        super(SoundDetectionNone, self).__init__(wurb_manager)

    def config(self):
        """ """
        pass  # Not needed.

    def check_for_sound(self, time_and_data):
        """ """
        # Always true, except when running in manual triggering mode.
        # Returns "is sound", "freq. at peak", "dBFS at peak".
        sound_detected = True
        sound_detected = self.manual_triggering_check(sound_detected)
        return (sound_detected, None, None)


class SoundDetectionSimple(SoundDetectionBase):
    """ """

    def __init__(self, wurb_manager):
        """ """
        super(SoundDetectionSimple, self).__init__(wurb_manager)
        # Config.
        self.sound_detected_counter_min = 3

    def config(self):
        """ """
        sampling_freq = self.wurb_recorder.sampling_freq_hz
        filter_min_khz = self.wurb_settings.get_setting("detection_limit_khz")
        threshold_dbfs = self.wurb_settings.get_setting("detection_sensitivity_dbfs")

        self.sampling_freq = float(sampling_freq)
        self.filter_min_hz = float(filter_min_khz) * 1000.0
        self.threshold_dbfs = float(threshold_dbfs)
        self.window_size = 2048
        self.jump_size = 1000

        # self.window_function = scipy.signal.blackmanharris(self.window_size)
        self.window_function = scipy.signal.windows.hann(self.window_size)
        # Max db value in window. dbFS = db full scale. Half spectrum used.
        self.window_function_dbfs_max = np.sum(self.window_function) / 2
        self.freq_bins_hz = np.arange((self.window_size / 2) + 1) / (
            self.window_size / self.sampling_freq
        )

        # print(
        #     "DEBUG: Detection: Freq: ",
        #     self.sampling_freq,
        #     " Filter: ",
        #     self.filter_min_hz,
        #     " Sens: ",
        #     self.threshold_dbfs,
        # )

    def check_for_sound(self, time_and_data):
        """ """
        _rec_time, raw_data = time_and_data
        # data_int16 = np.fromstring(raw_data, dtype=np.int16) # To ndarray.
        data_int16 = raw_data
        # self.work_buffer = np.concatenate([self._work_buffer, data_int16])
        self.work_buffer = data_int16
        #
        sound_detected = False
        sound_detected_counter = 0
        peak_frequency_hz = None
        peak_dbfs_at_max = None
        try:
            while len(self.work_buffer) >= self.window_size:
                # Get frame of window size.
                data_frame = self.work_buffer[: self.window_size]
                # Cut the first jumped size.
                self.work_buffer = self.work_buffer[self.jump_size :]
                # Transform to intervall -1 to 1 and apply window function.
                signal = data_frame / 32768.0 * self.window_function
                # From time domain to frequency domain.
                spectrum = np.fft.rfft(signal)
                # High pass filter. Unit Hz. Cut below 15 kHz.
                # log10 does not like zero.
                spectrum[self.freq_bins_hz < self.filter_min_hz] = 0.000000001
                # Convert spectrum to dBFS (bin values related to maximal possible value).
                if self.window_function_dbfs_max > 0.0:
                    dbfs_spectrum = 20 * np.log10(
                        np.abs(spectrum) / self.window_function_dbfs_max
                    )
                    # Find peak and dBFS value for the peak.
                    bin_peak_index = dbfs_spectrum.argmax()
                    peak_db = dbfs_spectrum[bin_peak_index]
                else:
                    peak_db = -500.0
                # Treshold.
                if peak_db > self.threshold_dbfs:
                    sound_detected_counter += 1
                    if sound_detected_counter >= self.sound_detected_counter_min:
                        sound_detected = True
                        if (peak_dbfs_at_max is None) or (peak_db > peak_dbfs_at_max):
                            peak_dbfs_at_max = peak_db
                            peak_frequency_hz = (
                                bin_peak_index * self.sampling_freq / self.window_size
                            )
                            # print(
                            #     "DEBUG: Peak freq hz: "
                            #     + str(peak_frequency_hz)
                            #     + "   dBFS: "
                            #     + str(peak_db)
                            # )
            # # Log if sound was detected.
            # if sound_detected:
            #     # Logging.
            #     message = (
            #         "Sound peak: "
            #         + str(round(peak_frequency_hz / 1000.0, 1))
            #         + " kHz / "
            #         + str(round(peak_dbfs_at_max, 1))
            #         + " dBFS."
            #     )
            #     self.wurb_logging.info(message, short_message=message)
            #
        except Exception as e:
            print("DEBUG: xception in check_for_sound: ", e)

        # Check if running in manual triggering mode.
        sound_detected = self.manual_triggering_check(sound_detected)

        return sound_detected, peak_frequency_hz, peak_dbfs_at_max
