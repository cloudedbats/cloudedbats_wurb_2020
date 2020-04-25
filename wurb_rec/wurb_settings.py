#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import os
import datetime
import pathlib

class WurbSettings(object):
    """ """

    def __init__(self):
        """ """
        self.latitude_dd = None
        self.longitude_dd = None
        self.os_raspbian = None
 

    async def set_location(self, latitude_dd, longitude_dd):
        """ """
        self.latitude_dd = latitude_dd
        self.longitude_dd = longitude_dd

    async def set_detector_time(self, posix_time_s):
        """ """
        if self.is_os_raspbian():
            time_string = datetime.datetime.utcfromtimestamp(posix_time_s).strftime('%Y-%m-%d %H:%M:%S')
            print(time_string)
            os.system('sudo date --set "' + time_string + '"')

    def is_os_raspbian(self):
        """ """
        if self.os_raspbian is not None:
            return self.os_raspbian
        else:
            os_version_path = pathlib.Path("/etc/os_version")
            if os_version_path.exists():
                with os_version_path.open("r") as os_file:
                    os_file_content = os_file.read()
                    if "Raspbian" in os_file_content:
                        self.os_raspbian = True
                    else:
                        self.os_raspbian = False
            else:
                self.os_raspbian = False
        #
        return self.os_raspbian

