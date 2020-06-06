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
from pydantic import BaseModel

# CloudedBats.
import wurb_rec

app = fastapi.FastAPI(
    title="CloudedBats WURB 2020",
    description="CloudedBats WURB 2020 - a part of CloudedBats.org.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="wurb_rec/static"), name="static")
templates = Jinja2Templates(directory="wurb_rec/templates")

# CloudedBats.
wurb_rec_manager = None

# Schemas.
class LocationSettings(BaseModel):
    geo_source_option: str = None
    latitude_dd: float = None
    longitude_dd: float = None
    manual_latitude_dd: float = None
    manual_longitude_dd: float = None


class DetectorSettings(BaseModel):
    rec_mode: str = None
    file_directory: str = None
    filename_prefix: str = None
    detection_limit: float = None
    detection_sensitivity: float = None
    detection_algorithm: str = None
    scheduler_start_event: str = None
    scheduler_start_adjust: float = None
    scheduler_stop_event: str = None
    scheduler_stop_adjust: float = None


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


@app.get("/start-rec")
async def start_recording():
    try:
        print("DEBUG: Called: start_rec.")
        global wurb_rec_manager
        await wurb_rec_manager.start_rec()
    except Exception as e:
        print("EXCEPTION: Called: start_rec: ", e)


@app.get("/stop-rec")
async def stop_recording():
    try:
        print("DEBUG: Called: stop_rec.")
        global wurb_rec_manager
        await wurb_rec_manager.stop_rec()
    except Exception as e:
        print("EXCEPTION: Called: stop_rec: ", e)


@app.get("/get-status")
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


@app.post("/save-location/")
async def save_location(settings: LocationSettings):
    try:
        print("DEBUG: Called: save_location: ", settings)
        global wurb_rec_manager
        await wurb_rec_manager.wurb_settings.save_location(settings.dict())
    except Exception as e:
        print("EXCEPTION: Called: save_location: ", e)


@app.get("/get-location/")
async def get_location(default: bool = False):
    try:
        print("DEBUG: Called: get_location.")
        global wurb_rec_manager
        current_location_dict = await wurb_rec_manager.wurb_settings.get_location()
        return current_location_dict
    except Exception as e:
        print("EXCEPTION: Called: get_location: ", e)


@app.get("/set-time/")
async def set_time(posixtime: str):
    try:
        print("DEBUG: Called: set_time: ", posixtime)
        global wurb_rec_manager
        posix_time_s = int(int(posixtime) / 1000)
        await wurb_rec_manager.wurb_settings.set_detector_time(posix_time_s)
    except Exception as e:
        print("EXCEPTION: Called: set_time: ", e)


@app.get("/save-rec-mode/")
async def save_rec_mode(recmode: str):
    try:
        print("DEBUG: Called: save_rec_mode: ", recmode)
        global wurb_rec_manager
        await wurb_rec_manager.wurb_settings.save_rec_mode(recmode)
    except Exception as e:
        print("EXCEPTION: Called: save_rec_mode: ", e)


@app.post("/save-settings/")
async def save_settings(settings: DetectorSettings):
    try:
        print("DEBUG: Called: save_settings: ", settings)
        global wurb_rec_manager
        await wurb_rec_manager.wurb_settings.save_settings(settings.dict())
    except Exception as e:
        print("EXCEPTION: Called: save_settings: ", e)


@app.get("/get-settings/")
async def get_settings(default: bool = False):
    try:
        print("DEBUG: Called: get_settings.")
        global wurb_rec_manager
        current_settings_dict = await wurb_rec_manager.wurb_settings.get_settings(
            default
        )
        return current_settings_dict
    except Exception as e:
        print("EXCEPTION: Called: get_settings: ", e)


@app.get("/rpi-control/")
async def rpi_control(command: str):
    try:
        print("DEBUG: Called: rpi_control: ", command)
        global wurb_rec_manager
        await wurb_rec_manager.wurb_settings.rpi_control(command)
    except Exception as e:
        print("EXCEPTION: Called: rpi_control: ", e)


@app.websocket("/ws")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    try:
        print("DEBUG: Called:  websocket_endpoint.")
        global wurb_rec_manager
        await websocket.accept()
        while True:
            # Wait for next event to happen.
            rec_manager_notification = await wurb_rec_manager.get_notification_event()
            location_changed_notification = await wurb_rec_manager.wurb_settings.get_location_event()
            latlong_changed_notification = await wurb_rec_manager.wurb_settings.get_latlong_event()
            settings_changed_notification = await wurb_rec_manager.wurb_settings.get_settings_event()
            events = [
                asyncio.sleep(1), # Update detector time field each second.
                rec_manager_notification.wait(),
                location_changed_notification.wait(),
                latlong_changed_notification.wait(),
                settings_changed_notification.wait(),
            ]
            await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED)

            # Prepare message to client.
            ws_json = {}
            status_dict = await wurb_rec_manager.get_status_dict()
            ws_json["status"] = {
                "rec_status": status_dict.get("rec_status", ""),
                "device_name": status_dict.get("device_name", ""),
                "detector_time": time.strftime("%Y-%m-%d %H:%M:%S%z"),
            }
            if location_changed_notification.is_set():
                ws_json[
                    "location"
                ] = await wurb_rec_manager.wurb_settings.get_location()
            if latlong_changed_notification.is_set():
                ws_json[
                    "latlong"
                ] = await wurb_rec_manager.wurb_settings.get_location()
            if settings_changed_notification.is_set():
                ws_json[
                    "settings"
                ] = await wurb_rec_manager.wurb_settings.get_settings()

            # Send to client.
            await websocket.send_json(ws_json)

    except Exception as e:
        print("EXCEPTION: Called: websocket_endpoint: ", e)


# @app.get("/items/{item-id}")
# async def read_item(item-id: int, q: str = None, q2: int = None):
#    return {"item-id": item_id, "q": q, "q2": q2}
