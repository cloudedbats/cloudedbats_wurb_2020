#!/bin/bash

cd /home/pi/cloudedbats_wurb_2020
source venv/bin/activate
sudo -u pi python3 wurb_rec_start.py &