#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import datetime

class WurbLogging(object):
    """ """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.wurb_settings = wurb_manager.wurb_settings
        self.wurb_logging = wurb_manager.wurb_logging
        self.logging_event = None
        self.client_messages = []

    async def startup(self):
        """ """

    async def shutdown(self):
        """ """

    async def info(self, message, client_message=None):
        """ """
        await self.write_log("info", message, client_message)

    async def warning(self, message, client_message=None):
        """ """
        await self.write_log("warning", message, client_message)

    async def error(self, message, client_message=None):
        """ """
        await self.write_log("error", message, client_message)

    async def debug(self, message, client_message=None):
        """ """
        await self.write_log("debug", message, client_message)

    async def write_log(self, type, message, client_message=None):
        """ """
        time_local = datetime.datetime.now()
        if client_message:
            time_str = time_local.strftime("%H:%M:%S")
            self.client_messages.append(time_str + "  " + client_message)

        # Create a new event and release all from the old event.
        old_logging_event = self.logging_event
        self.logging_event = asyncio.Event()
        if old_logging_event:
            old_logging_event.set()

    async def get_logging_event(self):
        """ """
        try:
            if self.logging_event == None:
                self.logging_event = asyncio.Event()
            return self.logging_event
        except Exception as e:
            print("Exception: ", e)

    async def get_client_messages(self):
        """ """
        return self.client_messages[::-1]
