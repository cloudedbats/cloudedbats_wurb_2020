#!/bin/bash

# This is needed to detect USB devices 
# when using the udevil utility.
###( sleep 5 && sudo -u pi devmon ) &
sleep 5
sudo -u pi devmon &

# Activate the virtual environment (venv) for Python.
cd /home/pi/cloudedbats_wurb_2020
source venv/bin/activate

# Defined environment variables.
# export WURB_REC_HOST=0.0.0.0
# export WURB_REC_PORT=8000
# export WURB_REC_LOG_LEVEL=info
# export WURB_REC_INPUT_DEVICE=hifiberry
# export WURB_REC_INPUT_DEVICE_FREQ_HZ=192000
# export WURB_REC_OUTPUT_DEVICE=Headphones
# export WURB_REC_OUTPUT_DEVICE_FREQ_HZ=48000

# Launch control by GPIO and/or computer mouse.
# It is running in it's own process.
python3 wurb_rpi/control_via_rpi.py &

# Launch the WURB detector.
python3 wurb_rec_start.py
