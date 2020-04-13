#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import uvicorn

import wurb_rec
from wurb_rec.wurb_recorder import WurbRecManager
import wurb_rec.api_main

if __name__ == "__main__":

    rec_manager = WurbRecManager()

    wurb_rec.api_main.wurb_rec_manager = rec_manager

    uvicorn.run(
        # "wurb_rec.api_main:app", workers=1, loop='asyncio', host="0.0.0.0", port=8000, log_level="info" # "debug",
        "wurb_rec.api_main:app", loop='asyncio', host="0.0.0.0", port=8000, log_level="info",
    )
