#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import datetime
from dateutil import parser
from gps3 import agps3

# HOST = '127.0.0.1'  # gpsd
# GPSD_PORT = 2947  # gpsd
# PROTOCOL = 'json'  # gpsd

class WurbGps(object):
    """ GPS reader for GPS USB dongle. """

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

    async def start(self):
        """ """
        self.last_used_lat_dd = 0.0
        self.last_used_long_dd = 0.0
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
            if self.gps_datetime_utc != "n/a":
                utc_datetime = parser.parse(self.gps_datetime_utc)
                utc_datetime = utc_datetime.replace(tzinfo=datetime.timezone.utc)
                return utc_datetime
        #
        return None

    async def get_datetime_local(self):
        """ """
        if self.gps_datetime_utc:
            if self.gps_datetime_utc != "n/a":
                utc_datetime = parser.parse(self.gps_datetime_utc)
                local_datetime = utc_datetime.replace(tzinfo=datetime.timezone.utc).astimezone(
                    tz=None
                )
                # time_string = local_datetime.strftime("%Y-%m-%d %H:%M:%S")
                return local_datetime
        #
        return None

    async def get_latitude_longitude(self):
        """ """
        return (self.gps_latitude, self.gps_longitude)

    async def gps_loop(self):
        """ """
        print("DEBUG: gps_loop started.")
        gps_socket = None
        try:
            gps_socket = agps3.GPSDSocket()
            gps_data_stream = agps3.DataStream()
            gps_socket.connect()
            gps_socket.watch(enable=True)
            # For new_data in socket:
            while True:
                new_data = gps_socket.next(timeout=5)
                if new_data:
                    gps_data_stream.unpack(new_data)
                    # Time.
                    try:
                        gps_time = gps_data_stream.time
                        if gps_time != "n/a":
                            self.gps_datetime_utc = gps_time
                            if not self.first_gps_time_received:
                                if self.is_time_valid(gps_time):
                                    self.first_gps_time_received = True
                                    # Set detector unit time.
                                    gps_utc_posix = parser.parse(gps_time).timestamp()
                                    await self.wurb_manager.wurb_settings.set_detector_time(gps_utc_posix)
                    except Exception as e:
                        print("Exception: GPS time: ", e)
                    # Lat/long.
                    try:
                        if gps_data_stream.lat !=  "n/a":
                            gps_lat = float(gps_data_stream.lat)
                            gps_long = float(gps_data_stream.lon)
                            self.gps_latitude = gps_lat
                            self.gps_longitude = gps_long
                            # Check if changed.
                            lat_dd = round(self.gps_latitude, 4)
                            long_dd = round(self.gps_longitude, 4)
                            if (self.last_used_lat_dd != lat_dd) or \
                               (self.last_used_long_dd != long_dd):
                                # Changed.
                                self.last_used_lat_dd = lat_dd
                                self.last_used_long_dd = long_dd
                                await self.wurb_manager.wurb_settings.save_latlong(lat_dd, long_dd)
                                # print("DEBUG: GPS lat/long: ", gps_lat, "  ", gps_long)
                    except Exception as e:
                        print("Exception: GPS lat/long: ", e)
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
            if gps_socket:
                gps_socket.watch(enable=False)

    def is_time_valid(self, gps_time):
        """ To avoid strange datetime (like 1970-01-01 or 2038-01-19) from some GPS units. """
        try:
            gps_utc = parser.parse(gps_time)
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


##### MAIN - for test #####
# async def main():
#     """ """
#     try:
#         gps_reader = WurbGps()
#         await gps_reader.start()
#         for _index in range(50):
#             await asyncio.sleep(1)
#             time_utc = await gps_reader.get_datetime_utc()
#             time_local = await gps_reader.get_datetime_local()
#             lat, long = await gps_reader.get_latitude_longitude()
#             print("")
#             print("TIME UTC: ", str(time_utc))
#             print("TIME Local: ", str(time_local))
#             print("LATLONG-STRING: ", lat, "   ", long)
#             print("")
#     except Exception as e:
#         print("Exception: ", e)
#     finally:
#         await gps_reader.stop()

# if __name__ == "__main__":
#     """ """
#     asyncio.run(main(), debug=True)

