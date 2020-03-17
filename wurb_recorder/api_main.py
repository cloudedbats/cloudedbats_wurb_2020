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
    from wurb_recorder.wurb_recorder import UltrasoundDevices
except:
    from wurb_recorder import UltrasoundDevices

app = fastapi.FastAPI(
    title="CloudedBats WURB 2020",
    description="CloudedBats WURB 2020 - with FastAPI, Docker, etc.",
    version="0.1.0",
)


app.mount("/static", StaticFiles(directory="wurb_recorder/static"), name="static")
templates = Jinja2Templates(directory="wurb_recorder/templates")

# CloudedBats.
ultrasound_devices = UltrasoundDevices()


@app.on_event("startup")
async def startup_event():
    """ """
    print("DEBUG: startup")
    asyncio.create_task(ultrasound_devices.check_connected_devices())


@app.on_event("shutdown")
def shutdown_event():
    """ """
    print("DEBUG: shutdown")


@app.get("/")
async def read_root(request: fastapi.Request):
    device_name, sample_rate = ultrasound_devices.get_connected_device()
    return templates.TemplateResponse(
        "wurb_miniweb.html",
        {"request": request, "device_name": device_name, "sample_rate": sample_rate,},
    )


@app.get("/get_status")
async def get_status():
    print("Called: get_status")
    await asyncio.sleep(0.5)
    return {
        "rec_status": "Don't know",
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    print("WS Called...")
    await websocket.accept()

    device_name = ""
    sample_rate = 0
    rec_status = "Device changed."
    device_name, sample_rate = ultrasound_devices.get_connected_device()
    while True:
        await websocket.send_json(
            {
                "rec_status": rec_status,
                "device_name": device_name,
                "sample_rate": str(sample_rate),
            }
        )
        device_name, sample_rate = await ultrasound_devices.get_device_when_changed()


@app.get("/start_rec")
async def start_rec():
    print("Called: start_rec")
    return {"rec_status": "Recording"}


@app.get("/stop_rec")
async def stop_rec():
    print("Called: stop_rec")
    return {"rec_status": "Stopped"}


# @app.get("/items/{item_id}")
# async def read_item(item_id: int, q: str = None, q2: int = None):
#    return {"item_id": item_id, "q": q, "q2": q2}

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=19594, log_level="info")

    # Or from command line:
    # > uvicorn wurb_recorder.api_main:app --reload --port 19594 --log-level info
