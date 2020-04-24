#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import time
import datetime
import asyncio
import fastapi
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# CloudedBats.
from wurb_rec.wurb_recorder import WurbRecManager

app = fastapi.FastAPI(
    title="CloudedBats WURB 2020",
    description="CloudedBats WURB 2020 - with FastAPI, Python asyncio, etc.",
    version="0.1.0",
)


app.mount("/static", StaticFiles(directory="wurb_rec/static"), name="static")
templates = Jinja2Templates(directory="wurb_rec/templates")

# CloudedBats.

wurb_rec_manager = None

# try:
#     wurb_rec_manager = WurbRecManager()
# except Exception as e:
#     print("EXCEPTION: import: ", e)


@app.on_event("startup")
async def startup_event():
    """ """
    try:
        print("DEBUG: Called: startup.")
        global wurb_rec_manager
        await wurb_rec_manager.startup()
    except Exception as e:
        print("EXCEPTION: Called: startup: ", e)


@app.on_event("shutdown")
async def shutdown_event():
    """ """
    try:
        print("DEBUG: Called: shutdown.")
        global wurb_rec_manager
        await wurb_rec_manager.shutdown()
    except Exception as e:
        print("EXCEPTION: Called: shutdown: ", e)


@app.get("/")
async def webpage(request: fastapi.Request):
    try:
        global wurb_rec_manager
        status_dict = await wurb_rec_manager.get_status_dict()
        return templates.TemplateResponse(
            "wurb_rec_web.html",
            {
                "request": request,
                "rec_status": status_dict.get("rec_status", ""),
                "device_name": status_dict.get("device_name", ""),
                "detector_time": time.strftime("%Y-%m-%d %H:%M:%S%z"),
             },
        )
    except Exception as e:
        print("EXCEPTION: Called: webpage: ", e)


@app.get("/start_rec")
async def start_recording():
    try:
        print("DEBUG: Called: start_recording.")
        global wurb_rec_manager
        await wurb_rec_manager.start_rec()
    except Exception as e:
        print("EXCEPTION: Called: start_recording: ", e)


@app.get("/stop_rec")
async def stop_recording():
    try:
        print("DEBUG: Called: stop_recording.")
        global wurb_rec_manager
        await wurb_rec_manager.stop_rec()
    except Exception as e:
        print("EXCEPTION: Called: stop_recording: ", e)


@app.get("/get_status")
async def get_status():
    try:
        print("DEBUG: Called: get_status.")
        global wurb_rec_manager
        status_dict = await wurb_rec_manager.get_status_dict()
        return {
            "rec_status": status_dict.get("rec_status", ""),
            "device_name": status_dict.get("device_name", ""),
            "detector_time": time.strftime("%Y-%m-%d %H:%M:%S%z"),
        }
    except Exception as e:
        print("EXCEPTION: Called: get_status: ", e)


@app.get("/set_location/")
async def set_location(latitude: str = "0.0", longitude: str = "0.0"):
    try:
        print("DEBUG: Called: set_location: ", latitude, " : ", longitude)
        global wurb_rec_manager
        # await wurb_rec_manager.set_location(latitude, longitude)
        # return {
        #     "rec_status": status_dict.get("rec_status", ""),
        #     "device_name": status_dict.get("device_name", ""),
        #     "detector_time": time.strftime("%Y-%m-%d %H:%M:%S%z"),
        # }
    except Exception as e:
        print("EXCEPTION: Called: set_location: ", e)


@app.get("/set_time/")
async def set_time(posix_time_ms: str):
    try:
        print("DEBUG: Called: set_time: ", posix_time_ms)
        global wurb_rec_manager

        # posix_time_ms = int(int(posix_time_ms) / 1000)
        # print(datetime.datetime.utcfromtimestamp(posix_time_ms).strftime('%Y-%m-%d %H:%M:%S'))
        # # os.system('sudo date --set "' + str(self.gps_time) + '"')

        # await wurb_rec_manager.set_time(posix_time_ms)
        # return {
        #     "rec_status": status_dict.get("rec_status", ""),
        #     "device_name": status_dict.get("device_name", ""),
        #     "detector_time": time.strftime("%Y-%m-%d %H:%M:%S%z"),
        # }
    except Exception as e:
        print("EXCEPTION: Called: set_time: ", e)


@app.websocket("/ws")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    try:
        print("DEBUG: Called:  websocket_endpoint.")
        global wurb_rec_manager
        await websocket.accept()
        while True:
            status_dict = await wurb_rec_manager.get_status_dict()
            await websocket.send_json(
                {
                    "rec_status": status_dict.get("rec_status", ""),
                    "device_name": status_dict.get("device_name", ""),
                    "detector_time": time.strftime("%Y-%m-%d %H:%M:%S%z"),
                }
            )
            # Wait for next event to happen.

            timer_notification = asyncio.sleep(1)

            rec_manager_notification = await wurb_rec_manager.get_notification_event()
            # device_notification = ultrasound_devices.get_notification_event()
            # rec_notification = recorder.get_notification_event()
            events = [
                timer_notification,
                rec_manager_notification.wait(),
                # device_notification.wait(),
                # rec_notification.wait(),
            ]
            await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED)

    except Exception as e:
        print("EXCEPTION: Called: websocket_endpoint: ", e)


# @app.get("/items/{item_id}")
# async def read_item(item_id: int, q: str = None, q2: int = None):
#    return {"item_id": item_id, "q": q, "q2": q2}
