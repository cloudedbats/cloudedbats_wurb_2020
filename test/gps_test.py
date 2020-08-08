#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import serial_asyncio
import pathlib
import datetime

"""
    Python script for testing GPS receivers. 

    Note: Deselect "Geographic location - Source: USB GPS Receiver"
    before starting this test.
    > cd /home/pi/cloudedbats_wurb_2020
    > source venv/bin/activate
    > python test/gps_test.py

    Alternative to use if the WURB detector software is not installed.
    > python3 -m venv venv
    > source venv/bin/activate
    > pip install pyserial pyserial-asyncio
    > python gps_test.py

    Example output when it works as expected. Received rows may differ but
    the NMEA sentences GGA and RMC must be present and number of satellites > 3:

        Received row:  $GPVTG,13.15,T,,M,0.22,N,0.4,K,A*3F
        Received row:  $GPGGA,231743.000,5739.7161,N,01238.3412,E,1,04,3.7,152.8,M,37.1,M,,0000*52
        Used NMEA:  $GPGGA,231743.000,5739.7161,N,01238.3412,E,1,04,3.7,152.8,M,37.1,M,,0000*52
        Received row:  $GPGSA,A,3,28,24,17,05,,,,,,,,,6.1,3.7,4.8*32
        Received row:  $GPGSV,4,1,15,05,04,195,21,07,00,084,,08,06,014,,10,10,335,15*76
        Received row:  $GPGSV,4,2,15,11,10,039,,13,67,160,21,15,65,257,15,17,15,128,34*7A
        Received row:  $GPGSV,4,3,15,19,01,145,,20,26,307,13,21,08,337,,23,26,313,18*72
        Received row:  $GPGSV,4,4,15,24,24,264,25,28,61,091,29,30,27,086,22*4C
        Received row:  $GPGLL,5739.7161,N,01238.3412,E,231743.000,A,A*5C
        Received row:  $GPRMC,231744.000,A,5739.7165,N,01238.3414,E,0.67,13.15,060820,,,A*55
        Used NMEA:  $GPRMC,231744.000,A,5739.7165,N,01238.3414,E,0.67,13.15,060820,,,A*55

        GPS datetime:  2020-08-06 23:17:44
        GPS latitude:  57.66194
        GPS longitude:  12.63902
"""


class GpsTest(object):
    """ Test class for USB GPS Receiver. """

    def __init__(self):
        """ """
        self.is_gps_quality_ok = False
        self.asyncio_loop = None

    async def start(self):
        """ """
        self.asyncio_loop = asyncio.get_event_loop()
        # Check if USB GPS is connected.
        gps_device_path_found = None
        for gps_device_path in ["/dev/ttyACM0", "/dev/ttyUSB0"]:
            gps_device = pathlib.Path(gps_device_path)
            if gps_device.exists():
                gps_device_path_found = gps_device_path
                break
        # Read serial, if connected.
        if gps_device_path_found:
            self.serial_coro = serial_asyncio.create_serial_connection(
                self.asyncio_loop,
                ReadGpsSerialNmea,
                gps_device_path_found,  # For example "/dev/ttyACM0".
                baudrate=4800,  # 9600, 19200, 38400
            )
            # Start. Serial_protocol is instance of ReadGpsSerialNmea
            self.serial_transport, self.serial_protocol = await self.serial_coro
            # To be used for calls back to master.
            self.serial_protocol.gps_manager = self
        else:
            # GPS device not found.
            self.is_gps_quality_ok = False
            self.last_used_lat_dd = 0.0
            self.last_used_long_dd = 0.0

    async def stop(self):
        """ """
        if self.serial_coro:
            if self.serial_transport:
                self.serial_transport.close()

    def parse_nmea(self, data):
        """ 
        From NMEA documentation:

        RMC - NMEA has its own version of essential gps pvt 
        (position, velocity, time) data. It is called RMC, 
        The Recommended Minimum, which will look similar to:
        $GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
        Where:
            RMC          Recommended Minimum sentence C
            123519       Fix taken at 12:35:19 UTC
            A            Status A=active or V=Void.
            4807.038,N   Latitude 48 deg 07.038' N
            01131.000,E  Longitude 11 deg 31.000' E
            022.4        Speed over the ground in knots
            084.4        Track angle in degrees True
            230394       Date - 23rd of March 1994
            003.1,W      Magnetic Variation
            *6A          The checksum data, always begins with *

        Example from test (Navilock NL-602U):
            $GPRMC,181841.000,A,5739.7158,N,01238.3515,E,0.52,289.92,040620,,,A*6D
        """
        parts = data.split(",")
        print("Used NMEA: ", data)

        # GPGGA. Check quality.
        if (len(parts) >= 8) and (parts[0] == "$GPGGA"):
            if parts[6] == "0": 
                # Fix quality 0 = invalid. 
                self.is_gps_quality_ok = False
                return
            number_of_satellites = parts[7]
            if int(number_of_satellites) < 3:
                # More satellites needed.
                self.is_gps_quality_ok = False
                return
            # Seems to be ok.
            self.is_gps_quality_ok = True
            return

        # GPRMC. Get date, time and lat/long.
        if (len(parts) >= 8) and (parts[0] == "$GPRMC"):
            if self.is_gps_quality_ok == False:
                return

            latitude_dd = 0.0
            longitude_dd = 0.0

            if (len(data) >= 50) and (len(parts) >= 8):
                time = parts[1]
                _gps_status = parts[2]
                latitude = parts[3]
                lat_n_s = parts[4]
                longitude = parts[5]
                long_w_e = parts[6]
                date = parts[9]
            else:
                self.last_used_lat_dd = 0.0
                self.last_used_long_dd = 0.0
                return

            # Extract date and time.
            datetime_utc = datetime.datetime(
                int("20" + date[4:6]),
                int(date[2:4]),
                int(date[0:2]),
                int(time[0:2]),
                int(time[2:4]),
                int(time[4:6]),
            )
            # Extract latitude and longitude.
            latitude_dd = round(
                float(latitude[0:2]) + (float(latitude[2:].strip()) / 60.0), 5
            )
            if lat_n_s == "S":
                latitude_dd *= -1.0
            longitude_dd = round(
                float(longitude[0:3]) + (float(longitude[3:].strip()) / 60.0), 5
            )
            if long_w_e == "W":
                longitude_dd *= -1.0

            self.gps_datetime_utc = datetime_utc
            self.gps_latitude = latitude_dd
            self.gps_longitude = longitude_dd

            print("")
            print("GPS datetime: ", datetime_utc)
            print("GPS latitude: ", latitude_dd)
            print("GPS longitude: ", longitude_dd)
            print("")



class ReadGpsSerialNmea(asyncio.Protocol):
    """ Serial connection for serial_asyncio. """

    def __init__(self):
        """ """
        super().__init__()
        self.buf = bytes()
        self.gps_manager = None

    def connection_made(self, transport):
        transport.serial.rts = False
        # self.gps_manager: GPS manager for callbacks will be set externally.
        # print("GPS: Connection made.")

    def data_received(self, data):
        try:
            # print("Data: ", data)
            # Avoid problems with data streams without new lines.
            if len(self.buf) >= 1000:
                self.buf = bytes()
            #
            self.buf += data
            if b'\n' in self.buf:
                rows = self.buf.split(b'\n')
                self.buf = rows[-1]  # Save remaining part.
                for row in rows[:-1]:
                    row = row.decode().strip()

                    print("Received row: ", row)

                    if (row.find("GPRMC") > 0) or (row.find("GPGGA") > 0):
                        # print("NMEA: ", row)
                        if self.gps_manager:
                            self.gps_manager.parse_nmea(row)
        except Exception as e:
            # Logging debug.
            message = "EXCEPTION in GPS:ReadGpsSerialNmea:data_received: " + str(e)
            print(message)

    def connection_lost(self, exc):
        pass


# === MAIN - for test ===
async def main():
    """ """
    print("Test started.")
    gps_test = GpsTest()
    await gps_test.start()
    await asyncio.sleep(60.0)
    # await gps_test.stop()
    print("Test finished.")

if __name__ == "__main__":
    """ """
    asyncio.run(main(), debug=True)
