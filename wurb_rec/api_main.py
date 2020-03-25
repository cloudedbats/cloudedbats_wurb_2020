#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import fastapi
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# CloudedBats.
try:
    from wurb_rec.wurb_recorder import WurbRecManager
except:
    from wurb_recorder import WurbRecManager

app = fastapi.FastAPI(
    title="CloudedBats WURB 2020",
    description="CloudedBats WURB 2020 - with FastAPI, asyncio, Docker, etc.",
    version="0.1.0",
)


app.mount("/static", StaticFiles(directory="wurb_rec/static"), name="static")
templates = Jinja2Templates(directory="wurb_rec/templates")

# CloudedBats.
try:
    wurb_rec_manager = WurbRecManager()
except Exception as e:
    print("Exception import: ", e)


@app.on_event("startup")
async def startup_event():
    """ """
    try:
        print("DEBUG: startup")
        wurb_rec_manager.startup()
    except Exception as e:
        print("Exception startup_event: ", e)


@app.on_event("shutdown")
async def shutdown_event():
    """ """
    try:
        print("DEBUG: shutdown")
        wurb_rec_manager.shutdown()
    except Exception as e:
        print("Exception shutdown_event: ", e)


@app.get("/")
async def webpage(request: fastapi.Request):
    try:
        status_dict = wurb_rec_manager.get_status_dict()
        return templates.TemplateResponse(
            "wurb_miniweb.html",
            {
                "request": request,
                "rec_status": status_dict.get("rec_status", ""),
                "device_name": status_dict.get("device_name", ""),
                "sample_rate": str(status_dict.get("sample_rate", "")),
            },
        )
    except Exception as e:
        print("Exception webpage: ", e)


@app.get("/start_rec")
async def start_recording():
    try:
        print("Called: start_rec")
        wurb_rec_manager.start_rec()
    except Exception as e:
        print("Exception start_recording: ", e)


@app.get("/stop_rec")
async def stop_recording():
    try:
        print("Called: stop_rec")
        wurb_rec_manager.stop_rec()
    except Exception as e:
        print("Exception stop_recording: ", e)


@app.get("/get_status")
async def get_status():
    try:
        print("Called: get_status")
        status_dict = wurb_rec_manager.get_status_dict()
        return {
                "rec_status": status_dict.get("rec_status", ""),
                "device_name": status_dict.get("device_name", ""),
                "sample_rate": str(status_dict.get("sample_rate", "")),
            }
    except Exception as e:
        print("Exception get_status: ", e)


@app.websocket("/ws")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    try:
        print("WS Called...")
        await websocket.accept()
        while True:
            status_dict = wurb_rec_manager.get_status_dict()
            await websocket.send_json(
                {
                    "rec_status": status_dict.get("rec_status", ""),
                    "device_name": status_dict.get("device_name", ""),
                    "sample_rate": str(status_dict.get("sample_rate", "")),
                }
            )
            # Wait for next event to happen.
            rec_manager_notification = wurb_rec_manager.get_notification_event()
            # device_notification = ultrasound_devices.get_notification_event()
            # rec_notification = recorder.get_notification_event()
            events = [
                rec_manager_notification.wait(),
                # device_notification.wait(),
                # rec_notification.wait(),
            ]
            await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED)

    except Exception as e:
        print("Exception websocket: ", e)


# @app.get("/items/{item_id}")
# async def read_item(item_id: int, q: str = None, q2: int = None):
#    return {"item_id": item_id, "q": q, "q2": q2}

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=19594, log_level="info")
    # uvicorn.run(app, host="0.0.0.0", port=19594, log_level="debug")

    # Or from the command line:
    # > uvicorn wurb_rec.api_main:app --reload --port 19594 --log-level info
