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
        # Config.
        self.max_client_messages = 50

    async def startup(self):
        """ """

    async def shutdown(self):
        """ """

    def info(self, message, short_message=None):
        """ """
        self.write_log("info", message, short_message)

    def warning(self, message, short_message=None):
        """ """
        self.write_log("warning", message, short_message)

    def error(self, message, short_message=None):
        """ """
        self.write_log("error", message, short_message)

    def debug(self, message, short_message=None):
        """ """
        self.write_log("debug", message, short_message)

    def write_log(self, msg_type, message, short_message=None):
        """ """
        # Run the rest in main loop.
        datetime_local = datetime.datetime.now()
        asyncio.run_coroutine_threadsafe(
            self.write_log_async(msg_type, datetime_local, message, short_message),
            asyncio.get_event_loop(),
        )

    async def write_log_async(
        self, msg_type, datetime_local, message, short_message=None
    ):
        """ """
        try:
            time_str = datetime_local.strftime("%H:%M:%S")
            datetime_str = datetime_local.strftime("%Y-%m-%d %H:%M:%S%z")
            if short_message:
                if msg_type in ["info", "warning", "error"]:
                    if msg_type in ["warning", "error"]:
                        self.client_messages.append(
                            time_str + " - " + msg_type.capitalize() + ": " + short_message
                        )
                    else:
                        self.client_messages.append(time_str + " - " + short_message)
                    # Log list too large. Remove oldest item.
                    if len(self.client_messages) > self.max_client_messages:
                        del self.client_messages[0]
                    # Create a new event and release all from the old event.
                    old_logging_event = self.logging_event
                    self.logging_event = asyncio.Event()
                    if old_logging_event:
                        old_logging_event.set()
        except Exception as e:
            print("Exception: Logging: write_log_async: ", e)

    async def get_logging_event(self):
        """ """
        try:
            if self.logging_event == None:
                self.logging_event = asyncio.Event()
            return self.logging_event
        except Exception as e:
            print("Exception: Logging: get_logging_event: ", e)
            # Logging error.
            message = "get_logging_event: " + str(e)
            self.wurb_manager.wurb_logging.error(message, short_message=message)

    async def get_client_messages(self):
        """ """
        return self.client_messages[::-1]
