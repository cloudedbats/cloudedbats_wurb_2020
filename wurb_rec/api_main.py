#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio
import fastapi
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# CloudedBats.
try:
    from wurb_rec.wurb_recorder import UltrasoundDevices, WurbRecorder
except:
    from wurb_recorder import UltrasoundDevices, WurbRecorder

app = fastapi.FastAPI(
    title="CloudedBats WURB 2020",
    description="CloudedBats WURB 2020 - with FastAPI, asyncio, Docker, etc.",
    version="0.1.0",
)


app.mount("/static", StaticFiles(directory="wurb_rec/static"), name="static")
templates = Jinja2Templates(directory="wurb_rec/templates")

# CloudedBats.
try:
    ultrasound_devices = UltrasoundDevices()
    recorder = WurbRecorder()
except Exception as e:
    print("Exception: ", e)


@app.on_event("startup")
async def startup_event():
    """ """
    try:
        print("DEBUG: startup")
        await ultrasound_devices.setup()
        await recorder.setup()
    except Exception as e:
        print("Exception: ", e)


@app.on_event("shutdown")
async def shutdown_event():
    """ """
    try:
        print("DEBUG: shutdown")
        await ultrasound_devices.shutdown()
        await recorder.shutdown()
    except Exception as e:
        print("Exception: ", e)


@app.get("/")
async def webpage(request: fastapi.Request):
    try:
        device_name, sample_rate = ultrasound_devices.get_connected_device()
        return templates.TemplateResponse(
            "wurb_miniweb.html",
            {
                "request": request,
                "device_name": device_name,
                "sample_rate": sample_rate,
            },
        )
    except Exception as e:
        print("Exception: ", e)


@app.get("/get_status")
async def get_status():
    try:
        print("Called: get_status")
        await asyncio.sleep(0.5)
        return {
            "rec_status": "Don't know",
        }
    except Exception as e:
        print("Exception: ", e)


@app.get("/start_rec")
async def start_recording():
    try:
        print("Called: start_rec")
        recorder.set_rec_status("Recording")
        return {"rec_status": "Recording"}
    except Exception as e:
        print("Exception: ", e)


@app.get("/stop_rec")
async def stop_recording():
    try:
        print("Called: stop_rec")
        recorder.set_rec_status("Stopped")
        return {"rec_status": "Stopped"}
    except Exception as e:
        print("Exception: ", e)


@app.websocket("/ws")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    try:
        print("WS Called...")
        await websocket.accept()
        device_name = "-"
        sample_rate = 0
        rec_status = "-"
        rec_status = recorder.get_rec_status()
        device_name, sample_rate = ultrasound_devices.get_connected_device()
        while True:
            await websocket.send_json(
                {
                    "rec_status": rec_status,
                    "device_name": device_name,
                    "sample_rate": str(sample_rate),
                }
            )
            # Wait for next event to happen.
            device_notification = ultrasound_devices.get_notification_event()
            rec_notification = recorder.get_notification_event()
            events = [
                device_notification.wait(),
                rec_notification.wait(),
            ]
            await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED)
            print("WS event released...")
            rec_status = recorder.get_rec_status()
            device_name, sample_rate = ultrasound_devices.get_connected_device()
    except Exception as e:
        print("WS Exception: ", e)


# @app.get("/items/{item_id}")
# async def read_item(item_id: int, q: str = None, q2: int = None):
#    return {"item_id": item_id, "q": q, "q2": q2}

if __name__ == "__main__":

    # uvicorn.run(app, host="0.0.0.0", port=19594, log_level="info")
    uvicorn.run(app, host="0.0.0.0", port=19594, log_level="debug")

    # Or from the command line:
    # > uvicorn wurb_recorder.api_main:app --reload --port 19594 --log-level info
