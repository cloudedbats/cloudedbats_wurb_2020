#  CloudedBats - WURB 2020

Welcome to CloudedBats-WURB, the DIY bat detector.

**Note: This is a new version of the WURB bat detector.
The old version can still be found here: 
https://github.com/cloudedbats/cloudedbats_wurb**

![WURB-2020](images/CloudedBats-WURB.jpg?raw=true  "CloudedBats WURB 2020.")
CloudedBats - WURB 2020. CloudedBats.org / [CC-BY](https://creativecommons.org/licenses/by/3.0/)

## Introduction

This is what you need to build your own bat detector; an ultrasonic USB microphone, a Raspberry Pi computer 
with SD card, power supply and this CloudedBats-WURB 2020 open source software. Optional parts that 
are recommended are USB memory sticks, an USB GPS receiver and a Power bank for single night sessions.
For the v0.9.0 release you will also need headphones with a 3.5 mm jack for audio feedback.

## Functional features, from the earlier CloudedBats-WURB:

- Support for USB ultrasonic microphones from Pettersson and Dodotronic 
  (tested with Pettersson u256, u384, M500 (the 500 kHz variant), M500-384 (384 kHz) and 
  Dodotronic UltraMic 192K, 250K, 384K BLE).
- Support for USB GPS receivers (tested with "Navilock NL-602U", "G-STAR IV, BU-353S4" 
  and "GPS/GLONASS U-blox7").
- File storage alternatives are; internally (on the SD card), USB memory or USB disc.
- Recording modes are full spectrum or time expanded "wav" files.
- Sound detection algorithm to avoid empty files. Buffer before the detected sound is always on.
- Time and position from attached GPS receiver is used in filenames and for the schedulers calculations.
- Scheduler for start and stop related to timestamps, sunset, dawn, etc. that are calculated from GPS time and position.
- Manually controlled via switches or a computer mouse.
- Log files for performed actions and errors.
- This version was configured via settings files stored on the USB memory stick.

## Added features in CloudedBats-WURB 2020:

Release v0.8:

- The detector acts as a WiFi Hotspot/AccessPoint and contains a web server. 
- Web pages are used for configuration and control. Adaptive layout for both smartphones and computers.
- Automatic detection of connected Ultrasonic microphones (valid for Pettersson and Dodotronic).
- Automatic detection of connected USB GPS Receiver.
- Sound peaks in kHz and dBFS are presented in live log and in file names.
- Automatic check where recorded files should be stored. On USB memory (multiple can be used) or 
  internally if no USB are found. Automatic failover to internal storage when USB memory is full.
- Possible to run the detectors user interface over internet, and to download files via SFTP.

Next release, v0.9 (available for test in the "master" branch):

- Reorganized user interface with a more intuitive detector mode selector.
- Audio feedback via the 3.5 mm audio jack for active monitoring with adjustable pitch level.
- New alternatives for GPS sources with fallback alternatives suitable for passive monitoring.
- Two configurable settings: "user default settings" and "start-up settings".
- Basic control via switches or a computer mouse (reintroduced, was missing in v0.8).
- Configurable host and port for internet traffic via environment variables.
- Possible to experiment and use other compatible sound cards that are compatible with ALSA on Raspberry Pi.
  Environment variables are used to specify sound card name and sampling frequency.

## Other characteristics

- The CloudedBats software is developed as open source software. Free to use under the terms of the MIT license.
- The software is developed on top of modern open source code libraries and frameworks.
- Inexpensive hardware can be used. Most of it is available where they are selling electronic things, except for the ultrasonic microphone.
- The Raspberry Pi computer offers many options for enhancements, like adding cameras and different types of sensors.
- Software developers can fork the code from GitHub to adjust the detector code to match their own needs.

## Drawbacks

- Higher power consumption compared to other passive monitoring systems. 
- You must put together the system yourself.
- The code is delivered "as-is" with no warranties at all. However, most software developers using Linux / Python 
  should understand the code and system setup to correct errors if I can't help.

**User manuals:** They are not written yet. Please contact me if there are any questions.

## Software notes, for developers:

This is valid for the CloudedBats-WURB 2020 version.

- Software completely rewritten. Python 3.7+ needed.
- Raspbian Buster Lite used for Raspberry Pi 4 support.
- RaspAP (https://raspap.com/) used to run the detector as a WiFi Hotspot/AccessPoint.
- The software design is inspired by micro services.
- The REST API is specified as OpenAPI 3.0.
- Asynchronous (async/await) programming both in frontend and backend.
- WebSockets are used for fast client updates.
- Stylesheets for responsive web pages are based on Bulma (https://bulma.io).
- FastAPI and uvicorn (https://www.uvicorn.org) are used to run the asynchronous web services.
- Pythons new asyncio library is used to replace all threads in the backend services. 
- Sounddevice and pyaudio have previously been used for communication with audio devices, but
  they are now replaced by alsaaudio (https://larsimmisch.github.io/pyalsaaudio/).

## Hardware

Any Raspberry Pi model with WiFi. (RPi Zero W works if auto detection and 
audio feedback is turned off). Raspberry Pi 4 is recommended if you want high speed transfer
of recorded files over internet.

Most SD cards seems to work but faster ones are recommended.
Personally I mostly use U3 (UHS Speed Class U3), for example Toshiba Exceria Pro.

**Note:** For some strange reason both M500 and M500-384 have problems if connected directly to a 
Raspberry Pi 4 at startup (RPi3B+ works fine). Workarounds are to use an extra USB 2.0 Hub (passive is ok), 
or attach the M500 or M500-384 microphone after startup.


## Installation

Use Raspberry Pi Imager to download "Raspbian Pi OS Lite" 
and install it on a SD card. Raspberry Pi Imager can be found here: 
https://www.raspberrypi.org/software/operating-systems/

Alternative: BalenaEtcher is an alternative to Raspberry Pi Imager.

Connect the SD card to a computer and add an empty file with 
the name "ssh" to the SD card (the SD card will have the name 
"boot" when connected). This step is done to activate the possibility
to connect to the Raspberry Pi via ssh. 

Insert the SD card into you Raspberry Pi, connect an Ethernet 
cable and start it.

Alternative: It is possible to connect a HDMI screen and USB keyboard as 
an alternative to do the installation from a terminal window on another computer.

### Raspberry Pi setup:

Connect to the Raspberry Pi from a computer over ssh. 
The address "raspberrypi.local" can be used if your computer supports mDNS. 
Otherwise you have to check up the IP number:

    ssh pi@raspberrypi.local
    
Default password is: raspberry

Update the Raspberry Pi: 

    sudo apt update
    sudo apt upgrade

Make some configurations:

    sudo raspi-config

Change this (example for Swedish users):

- System Options - Password: chiroptera
- System Options - Hostname: wurb 
- System Options - Network at boot: No 
- Localisation Options - Timezone: Europe - Stockholm
- Localisation Options - WLAN Country: SE
- Advanced Options - Expand Filesystem.

Reboot and reconnect. Remember to use the new password.:

    sudo reboot
    # Wait...
    ssh pi@wurb.local

### RaspAP

Download and install RaspAp (https://raspap.com):

    curl -sL https://install.raspap.com | bash

Connect to the wifi network named raspi-webgui. Password: ChangeMe.

Start a web browser and go to: http://10.3.141.1. Username: admin, password: secret.

Change the defaults settings from:

- Hotspot-Basic-SSID (wifi name): raspi-webgui
- Hotspot-Security-PSK (wifi password): ChangeMe
- Authentication-Username (admin username): admin
- Authentication-Password (admin password): secret

Change to (example for Swedish users):

- Hotspot-Basic-SSID (wifi name): wifi4bats
- Hotspot-Security-PSK (wifi password): chiroptera 
- Authentication-Username (admin username): batman
- Authentication-Password (admin password): chiroptera
- Hotspot-Advanced-Country Code: Sweden

About Internet connection:

When running the detector as a standalone unit and the Ethernet cable is not connected to 
the Raspberry Pi, then Internet is not available. 
That's ok if you only want to control the detector. If you have to, for example, 
upgrade the Raspberry Pi, then you must connect an Ethernet cable to it to reach Internet.
For advanced users there are many possible ways to set up networks with 
multiple collaborating Raspberry Pi units.

### Install packages

Check that the Python version is 3.7 or later. If not you 
have to download and install a new version:

    python3 --version

Install software:

    sudo apt install git python3-venv python3-dev
    sudo apt install libatlas-base-dev udevil

### Pettersson M500 (500kHz)

The Pettersson M500 microphone (the 500kHz version) differ in communication
format compared to M500-384, u256, and u384. Some udev rules must be setup
to allow the detector to communicate with it.

    # Create a file with udev rules:
    sudo nano /etc/udev/rules.d/pettersson_m500_batmic.rules
    
    # Add this row in the new file. 
    SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", MODE="0664", GROUP="pi"

### USB GPS Receiver (optional)

The detector is listening to GPS units that are connected to  
"/dev/ttyACM0" or "/dev/ttyUSB0". Only NMEA format is supported. 

There is a python script to be used if the detector can't detect your GPS receiver. 
Read the instructions in the test script: 
https://github.com/cloudedbats/cloudedbats_wurb_2020/blob/master/test/gps_test.py 

**Note:** This will not work if GPSD is installed. 
Please uninstall it if that's the case.

### CloudedBats software

    git clone https://github.com/cloudedbats/cloudedbats_wurb_2020.git
    cd cloudedbats_wurb_2020/
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt 

    sudo nano /etc/rc.local 

    # Add this before the "exit" row in rc.local:
    sudo -u pi bash /home/pi/cloudedbats_wurb_2020/wurb_rec_start.sh &

And finally, set the headphone volume and restart the detector:

    amixer set 'Headphone' 100%
    sudo reboot

### Start problems

If the detector does not start properly, the cause may be incompatible releases 
of the software packages used. Try to start the detector in the development mode 
to check for error messages.

    cd /home/pi/cloudedbats_wurb_2020
    source venv/bin/activate
    python3 wurb_rec_start.py
   
Please contact me if this happens. Most of the time the solution is to avoid 
the latest release of the library that causes the error. Together we can help other.

### CloudedBats software - latest stable version

If you want to run the latest stable version, then replace the git clone line in the instruction above.

    git clone https://github.com/cloudedbats/cloudedbats_wurb_2020.git -b v0.8.1

## Run the detector

- Connect the ultrasonic microphone to the detector (can also be done after startup).
- Connect USB memory stick(s) (optional, or can be done after startup).
- Start the Raspberry Pi. It will start automatically when power is added.
- Connect a computer or mobile phone to the WiFi network called "wifi4bats". Password: chiroptera.
- Open a web browser and go to http://10.3.141.1:8000
- Check "Geographic location" and "Settings". 
- Press "Set time".
- Select "Mode", for example "Recording - Auto detection".
- Connect headphones (3.5 mm jacket on the Raspberry Pi) and listen to the bats.
- Record some bats.
- Press "Stop recording".

There are different ways to turn the Raspberry Pi detector off (power off only is not
recommended since there is a small risk of corrupted SD card or USB memory sticks): 

- Select "Mode": "Detector - Power off..." and press the "Shutdown" button.
- Go to the WiFi administration page at http://10.3.141.1. Select "System" and press "Shutdown".
- Attach an USB Computer mouse and hold down both the left end right button for 5 sec.
- Connect a physical button to GPIO pin #37 and pin #39 (but be careful, connecting the wrong GPIO 
  pins can destroy your Raspberry Pi). Then press that button for a few seconds.

More than one USB memory stick can be used. They will be filled up with wave files 
in alphabetic order. When the last USB memory stick is full, then it will continue 
on the SD card. It will stop when there is less than 0.5 GB left on the SD card.

If files are stored on the SD card then they can be downloaded and/or removed by 
using for example FileZilla. Connect with SFTP to http://10.3.141.1 
with user "pi" and password "chiroptera".
Path to files on the SD card: "/home/pi/wurb_recordings".

It is also possible to download files by using FileZilla, or similar, from the USB 
memory stick during an ongoing recording session. The path to the USB memory is then 
"/media/pi/<your-usb-memory-stick-name>".

Note: Some mobile phones complains if the "wifi4bats" network not is 
connected to internet. If that happens, then tell it to forget the network, 
connect to i again and answer the question if you want to connect to it
anyway.

## The MIT license

This software is released under the MIT license that means that you are free to use it as you want; 
use it, share it, cut it into pieces, extend it, or even sell it for money. 
But you are not allowed to remove the MIT license clause 
(just change my name to yours in the copyright row for modified code files), 
and it comes "as-is" with no warranties at all.

## Contact

Arnold Andreasson, Sweden.

info@cloudedbats.org
