#!/bin/bash

# This is needed to detect USB devices 
# when using the udevil utility.
###( sleep 5 && sudo -u pi devmon ) &
sleep 5
sudo -u pi devmon &

# Activate the virtual environment (venv) for Python.
cd /home/pi/cloudedbats_wurb_2020
source venv/bin/activate

# Launch control by GPIO and/or computer mouse.
# It is running in it's own process.
python3 wurb_rpi/control_via_rpi.py &

# Launch the WURB detector.
python3 wurb_rec_start.py
