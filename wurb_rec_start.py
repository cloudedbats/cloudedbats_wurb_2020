#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import uvicorn
import wurb_rec

if __name__ == "__main__":

    # CloudedBats recording unit manager.
    rec_manager = wurb_rec.WurbRecManager()
    
    # Launch REST API.
    wurb_rec.api_app.wurb_rec_manager = rec_manager
    uvicorn.run(
        "wurb_rec.api_app:app",
        loop="asyncio",
        host= os.getenv("WURB_REC_HOST", "0.0.0.0"),
        port=int(os.getenv("WURB_REC_PORT", "8000")),
        log_level=os.getenv("WURB_REC_LOG_LEVEL", "info"),
    )
