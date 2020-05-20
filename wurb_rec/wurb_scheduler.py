#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio

class WurbScheduler(object):
    """ """

    def __init__(self, wurb_manager):
        """ """
        self.wurb_manager = wurb_manager
        self.main_loop_task = None

    async def startup(self):
        """ """
        self.main_loop_task = asyncio.create_task(self.main_loop())

    async def shutdown(self):
        """ """
        if self.main_loop_task:
            self.main_loop_task.cancel()

    async def main_loop(self):
        """ """
        try:
            while True:
                await asyncio.sleep(10)
                rec_mode = self.wurb_manager.wurb_settings.get_setting("rec_mode")
                if rec_mode == "rec-mode-on":
                    await self.wurb_manager.start_rec()
                if rec_mode == "rec-mode-scheduler":
                    await self.check_scheduler()

        except Exception as e:
            print("DEBUG: Scheduler main_loop exception: ", e)
        finally:
            print("DEBUG: Scheduler main_loop terminated.")

    async def check_scheduler(self):
        """ """
        await self.wurb_manager.start_rec()
