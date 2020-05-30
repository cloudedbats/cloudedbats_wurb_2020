#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import concurrent.futures
import time
import datetime
from dateutil import parser
from gps3 import gps3


class WurbGps(object):
    """ GPS reader for USB GPS Receiver. """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.gps_datetime_utc = None
        self.gps_latitude = None
        self.gps_longitude = None
        self.gps_loop_task = None
        self.first_gps_time_received = False
        self.last_used_lat_dd = 0.0
        self.last_used_long_dd = 0.0
        self.gpsd_reader_executor = None
        self.gpsd_reader_future = None
        self.gpsd_reader_active = False
        self.gpsd_time = None
        self.gpsd_latitude = None
        self.gpsd_longitude = None

    async def startup(self):
        """ """

    async def shutdown(self):
        """ """
        if self.gpsd_reader_future:
            print("DEBUG: Shutdown GPSD Reader.")
            self.gpsd_reader_active = False
            is_done = self.gpsd_reader_future.result(timeout=7.0)
            if is_done:
                self.gpsd_reader_executor = None
                self.gpsd_reader_future = None

    async def start(self):
        """ """
        self.last_used_lat_dd = 0.0
        self.last_used_long_dd = 0.0
        if self.gpsd_reader_executor == None:
            print("DEBUG: Start GPSD Reader.")
            self.gpsd_reader_executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=1
            )
            self.gpsd_reader_future = self.gpsd_reader_executor.submit(
                self.gpsd_thread_loop
            )
        if self.gps_loop_task is None:
            self.gps_loop_task = asyncio.create_task(self.gps_loop())

    async def stop(self):
        """ """
        if self.gps_loop_task:
            self.gps_loop_task.cancel()
            self.gps_loop_task = None

    async def get_datetime_utc(self):
        """ """
        if self.gps_datetime_utc:
            utc_datetime = self.gps_datetime_utc.replace(tzinfo=datetime.timezone.utc)
            return utc_datetime
        #
        return None

    async def get_datetime_local(self):
        """ """
        if self.gps_datetime_utc:
            local_datetime = self.gps_datetime_utc.replace(
                tzinfo=datetime.timezone.utc
            ).astimezone(tz=None)
            return local_datetime
        #
        return None

    async def get_latitude_longitude(self):
        """ """
        return (self.gps_latitude, self.gps_longitude)

    def gpsd_connect(self):
        """ """
        try:
            return gpsd.connect()
        except Exception as e:
            print("DEBUG: Exception: ", e)

    def gpsd_get_current(self):
        """ """
        return gpsd_copy.get_current()

    async def gps_loop(self):
        """ """
        print("DEBUG: gps_loop started.")
        try:
            self.last_used_lat_dd = 0.0
            self.last_used_long_dd = 0.0
            await self.wurb_manager.wurb_settings.save_latlong(0.0, 0.0)

            while True:
                try:
                    # Time.
                    try:
                        if not self.first_gps_time_received:
                            if self.gpsd_time:
                                self.gps_datetime_utc = self.gpsd_time
                                if self.is_time_valid(self.gpsd_time):
                                    self.first_gps_time_received = True
                                    # Set detector unit time.
                                    gps_local_time = self.gpsd_time.replace(
                                        tzinfo=datetime.timezone.utc
                                    ).astimezone()
                                    gps_local_timestamp = gps_local_time.timestamp()
                                    await self.wurb_manager.wurb_settings.set_detector_time(
                                        gps_local_timestamp
                                    )
                    except Exception as e:
                        print("Exception: GPS time: ", e)
                    # Lat/long.
                    try:
                        if self.gpsd_latitude and self.gpsd_longitude:
                            self.gps_latitude = float(self.gpsd_latitude)
                            self.gps_longitude = float(self.gpsd_longitude)
                        else:
                            self.gps_latitude = 0.0
                            self.gps_longitude = 0.0
                        # Check if changed.
                        lat_dd = round(self.gps_latitude, 4)
                        long_dd = round(self.gps_longitude, 4)
                        if (self.last_used_lat_dd != lat_dd) or (
                            self.last_used_long_dd != long_dd
                        ):
                            # Changed.
                            self.last_used_lat_dd = lat_dd
                            self.last_used_long_dd = long_dd
                            await self.wurb_manager.wurb_settings.save_latlong(
                                lat_dd, long_dd
                            )
                            # print("DEBUG: GPS lat/long: ", gps_lat, "  ", gps_long)
                    except Exception as e:
                        print("Exception: GPS lat/long: ", e)
                except Exception as e:
                    pass
                    print("DEBUG: No GPSD data:", e)
                #
                await asyncio.sleep(1.0)
        #
        except Exception as e:
            print("Exception: gps_loop exception: ", e)
            if self.gps_loop_task:
                self.gps_loop_task.cancel()
            self.gps_loop_task = None
        finally:
            print("DEBUG: gps_loop terminated.")

    def is_time_valid(self, gps_time):
        """ To avoid strange datetime (like 1970-01-01 or 2038-01-19) from some GPS units. """
        try:
            gps_utc = gps_time.astimezone(tz=datetime.timezone.utc)
            # gps_utc = parser.parse(gps_time)
            datetime_now = datetime.datetime.now(datetime.timezone.utc)
            if gps_utc < (datetime_now - datetime.timedelta(days=2)):
                return False
            elif gps_utc > (datetime_now + datetime.timedelta(days=(365 * 5))):
                return False
            else:
                return True
        except Exception as e:
            print("Exception: GPS is_time_valid: ", e)
            return False

    def gpsd_thread_loop(self):
        """ Thread not in asyncio main loop. 
            Executed by "concurrent.futures.Executor". """
        gpsd_socket = None
        self.gpsd_reader_active = True
        try:
            print("DEBUG: GPSD-thread: Started.")
            gpsd_socket = gps3.GPSDSocket()
            data_stream = gps3.DataStream()
            gpsd_socket.connect()
            gpsd_socket.watch(True)
            while self.gpsd_reader_active:
                time.sleep(1.0)
                new_data = gpsd_socket.next(timeout=5)
                if new_data:
                    data_stream.unpack(new_data)
                    gpsd_time = data_stream.TPV["time"]
                    gpsd_latitude = data_stream.TPV["lat"]
                    gpsd_longitude = data_stream.TPV["lon"]

                    print(
                        "DEBUG: GPSD-thread: ",
                        gpsd_time,
                        "   ",
                        gpsd_latitude,
                        "   ",
                        gpsd_longitude,
                    )

                    # Time.
                    if gpsd_time and (gpsd_time != "n/a"):
                        self.gpsd_time = parser.parse(gpsd_time)
                    else:
                        self.gpsd_time = None
                    # Lat/long.
                    if (
                        gpsd_latitude
                        and (gpsd_latitude != "n/a")
                        and gpsd_longitude
                        and (gpsd_longitude != "n/a")
                    ):
                        self.gpsd_latitude = gpsd_latitude
                        self.gpsd_longitude = gpsd_longitude
                    else:
                        self.gpsd_latitude = None
                        self.gpsd_longitude = None
                else:

                    print("DEBUG: GPSD-thread: No data.")

                    self.gpsd_time = None
                    self.gpsd_latitude = None
                    self.gpsd_longitude = None
        #
        except Exception as e:
            print("Exception: GPS gpsd_thread_loop: ", e)
        finally:
            print("DEBUG: GPSD-thread: Ended.")
            if gpsd_socket:
                gpsd_socket.watch(False)
        #
        return True  # Done.

