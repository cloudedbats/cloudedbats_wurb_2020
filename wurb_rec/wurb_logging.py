#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import datetime
import pathlib
import logging
from logging import handlers


class WurbLogging(object):
    """ """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.rotating_log = logging.getLogger("CloudedBats-WURB")
        self.logging_event = None
        self.client_messages = []
        self.event_loop = None
        # Config.
        self.max_client_messages = 50

    async def startup(self):
        """ """
        self.event_loop = asyncio.get_event_loop()
        log_dir_path = self.get_logging_dir_path()
        self.setup_rotating_log(log_dir_path=log_dir_path)
        # Welcome message.
        self.rotating_log.info("")
        self.rotating_log.info("")
        self.rotating_log.info("Welcome to CloudedBats WURB 2020.")
        self.rotating_log.info("Main project page: http://cloudedbats.org")
        self.rotating_log.info("Source code: https://github.com/cloudedbats")
        self.rotating_log.info("================== ^ö^ ====================")
        self.rotating_log.info("")

    async def shutdown(self):
        """ """

    def info(self, message, short_message=None):
        """ """
        self.rotating_log.info(message)
        self.write_log("info", message, short_message)

    def warning(self, message, short_message=None):
        """ """
        self.rotating_log.warning(message)
        self.write_log("warning", message, short_message)

    def error(self, message, short_message=None):
        """ """
        self.rotating_log.error(message)
        self.write_log("error", message, short_message)

    def debug(self, message, short_message=None):
        """ """
        self.rotating_log.debug(message)
        # self.write_log("debug", message, short_message)

    def write_log(self, msg_type, message, short_message=None):
        """ """
        # Run the rest in the main asyncio event loop.
        datetime_local = datetime.datetime.now()
        asyncio.run_coroutine_threadsafe(
            self.write_log_async(msg_type, datetime_local, message, short_message),
            self.event_loop,
        )

    async def write_log_async(
        self, msg_type, datetime_local, message, short_message=None
    ):
        """ """
        try:
            time_str = datetime_local.strftime("%H:%M:%S")
            # datetime_str = datetime_local.strftime("%Y-%m-%d %H:%M:%S%z")
            if short_message:
                if msg_type in ["info", "warning", "error"]:
                    if msg_type in ["warning", "error"]:
                        self.client_messages.append(
                            time_str
                            + " - "
                            + msg_type.capitalize()
                            + ": "
                            + short_message
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
            # Can't log this, must use print.
            print("Exception: Logging: write_log_async: ", e)

    async def get_logging_event(self):
        """ """
        try:
            if self.logging_event == None:
                self.logging_event = asyncio.Event()
            return self.logging_event
        except Exception as e:
            # Logging error.
            message = "get_logging_event: " + str(e)
            self.error(message, short_message=message)

    async def get_client_messages(self):
        """ """
        return self.client_messages[::-1]

    def get_logging_dir_path(self):
        """ """
        rpi_dir_path = "/home/pi/"  # For RPi SD card with user 'pi'.
        # Default for not Raspberry Pi.
        dir_path = pathlib.Path("wurb_logging")
        if pathlib.Path(rpi_dir_path).exists():
            dir_path = pathlib.Path(rpi_dir_path, "wurb_logging")
        # Create directories.
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
        return dir_path

    def setup_rotating_log(self, log_dir_path):
        """ """
        try:
            # Create directory for log files.
            logging_dir_path = pathlib.Path(log_dir_path)
            if not logging_dir_path.exists():
                logging_dir_path.mkdir(parents=True)
            # Info and debug logging.
            wurb_logger_info = logging.getLogger("CloudedBats-WURB")
            wurb_logger_info.setLevel(logging.INFO)
            wurb_logger_debug = logging.getLogger("CloudedBats-WURB")
            wurb_logger_debug.setLevel(logging.DEBUG)
            # Define rotation log files for info logger.
            log_info_name_path = pathlib.Path(log_dir_path, "wurb_rec_log.txt")
            log_handler = handlers.RotatingFileHandler(
                str(log_info_name_path), maxBytes=128 * 1024, backupCount=10
            )
            log_handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)-8s : %(message)s ")
            )
            log_handler.setLevel(logging.INFO)
            wurb_logger_info.addHandler(log_handler)
            # Define rotation log files for debug logger.
            log_info_name_path = pathlib.Path(log_dir_path, "wurb_rec_debug_log.txt")
            log_handler = handlers.RotatingFileHandler(
                str(log_info_name_path), maxBytes=128 * 1024, backupCount=10
            )
            log_handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)-8s : %(message)s ")
            )
            log_handler.setLevel(logging.DEBUG)
            wurb_logger_debug.addHandler(log_handler)
        except Exception as e:
            print("Logging: Failed to set up logging: " + str(e))
