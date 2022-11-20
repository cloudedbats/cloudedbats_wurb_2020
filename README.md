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

Release v0.9:

- Reorganized user interface with a more intuitive detector mode selector.
- Audio feedback via the 3.5 mm audio jack for active monitoring with adjustable pitch level.
- New alternatives for GPS sources with fallback alternatives suitable for passive monitoring.
- Two configurable settings: "user default settings" and "start-up settings".
- Basic control via switches or a computer mouse (reintroduced, was missing in v0.8).
- Configurable host and port for internet traffic via environment variables.
- Possible to experiment and use other sound cards that are compatible with ALSA on Raspberry Pi.
  Environment variables are used to specify sound card name and sampling frequency.
- User manual for basic usage.

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

## User manuals:
- User manual for basic usage:
  https://github.com/cloudedbats/cloudedbats_wurb_2020/blob/master/docs/user_manual_basic.md
- The user manual for advanced usage is not written yet. Please contact me if there are questions.

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

Note: This installation guide is updated to match the Ansible
installation guide that is used for more automated installations.
If you are familiar with Ansible, then please have a look here:
https://github.com/cloudedbats/ansible-playbooks

### Main workflow, overview

The main steps during the installation are:

- Install the Raspberry Pi Operating system on an SD card, with some basic configurations.
- Move the SD card to a Raspberry Pi computer and power it up.
- The Raspberry Pi should now be connected to your local WiFi network, or via an optional Ethernet cable.
- Login to the Raspberry Pi with SSH by using a terminal window.
- Make some basic configurations.
- Install needed Linux modules.
- Install the CloudedBats WURB-2020 software.
- Restart the Raspberry Pi.
- Add extra optional features like RaspAP, etc.

### Install the Raspberry Pi OS

Use the **Raspberry Pi Imager** to install the Raspberry Pi operating system.

- Download and install the Raspberry Pi Imager from here:
https://www.raspberrypi.com/software/
- Start the Raspberry Pi Imager.
- Select the operating system **"Raspberry Pi OS Lite"**, use the 32-bit version. (The "Desktop" version will not work, it must be the **"Lite"** version.)
- Attach an SD card and select it in the Raspberry Pi Imager.
- Click the “settings” button (the cogwheel).

Then make these setting, to be used as an example. It will also work with an
Ethernet cable connected to the Raspberry Pi, and then the WiFi (wireless LAN) part can be omitted.

Note that the username must be **pi** in this version of the WURB bat detector.

- Hostname: wurb99
- Enable SSH
- Use password authentication
- Username: pi
- Password: my-wurb99-password
- Configure wireless LAN
  - SSID: my-home-wifi
  - Password: my-home-wifi-password
  - Wireless LAN country: SE
- Locale settings
  - Time zone: Europe/Stockholm
  - Keyboard layout: se

Finally write to the SD card. When finished remove the SD card.

If you have many detectors, then be sure that you use different hostnames.
Otherwise there will be problems when they are connected to the same network
if more than one is identified as, for example, "wurb99.local".

### Start the Raspberry Pi

Insert the SD card into the Raspberry Pi and power it up.

The Raspberry Pi should now be connected to your local network, either via 
WiFi or an Ethernet cable depending on your configuration above.

Start a terminal window and connect with SSH.
For Windows users Putty is a well known alternative.

    ssh pi@wurb99.local

It is also possible to attach a screen and keyboard/mouse directly to
the Raspberry Pi instead of using ssh. 
No graphical user interface will be available, only command line mode.

### Basic configurations

Update the Raspberry Pi software.

    sudo apt update
    sudo apt upgrade

Make some configurations.
Most of them are already made when running
Raspberry Pi Imager above, but the last two must
be done here. Later modification can be done
whenever you want by running raspi-config.

    sudo raspi-config

Check or change this (example for Swedish users):

- System Options - Hostname: wurb99 
- System Options - Password: my-wurb99-password
- Localization Options - Timezone: Europe - Stockholm

Mandatory:

- System Options - Network at boot: No
- Advanced Options - Expand Filesystem.

A reboot is needed to expand the file system.

    sudo reboot

Hint: WiFi networks can be changed via raspi-config.
Another alternative is to edit the wpa_supplicant.conf file
and change SSID and password for the network.
Even a list of networks can be added in this file if the
detector is used at different places.

    sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

### Install Linux packages

Install needed software packages.

    sudo apt install git python3-venv python3-dev libatlas-base-dev udevil

### Pettersson M500 (500kHz)

The Pettersson M500 microphone (the 500kHz version) differ in communication
format compared to M500-384, u256, and u384. Some udev rules must be setup
to allow the detector to communicate with it.

    # Create a file with udev rules:
    sudo nano /etc/udev/rules.d/pettersson_m500_batmic.rules
    
    # Add this row in the new file. 
    SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", MODE="0664", GROUP="pi"

### Install the CloudedBats WURB-2020 software

Clone the software from the GitHub repository and install Python related packages.

    git clone https://github.com/cloudedbats/cloudedbats_wurb_2020.git
    cd cloudedbats_wurb_2020/
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt 

Note: When installing packages most of them are pre-prepared in something
called "wheels".
The main source for wheels for Raspberry Pi can be found here,
with an example for SciPy:
https://piwheels.org/project/scipy/
If that build has failed, then it is possible to use an older version.
The installation process may find a working version automatically with a
lot of warnings during the installation process.
Then it is possible to edit the requirements.txt file to speed up the
installation process. In the SciPy case the row can be changed
from "scipy" to "scipy<1.9" if there are problems with version 1.9.

### Run the detector software as a service

Install the service and enable it. Enable means that the service will
start automatically when the Raspberry Pi is started.

    sudo cp wurb_2020.service /etc/systemd/system/wurb_2020.service
    sudo systemctl daemon-reload
    sudo systemctl enable wurb_2020.service
    sudo systemctl start wurb_2020.service

### Adjust sound level

Set the headphone volume used for audio feedback.

    amixer set 'Headphone' 100%

### And finally, restart the detector

    sudo reboot

### RaspAP, optional installation

If you want to use the detector away from computer networks, then
the RaspAP software can help. Read more here: https://raspap.com

Note that the built-in WiFi module will be used by RaspAP to provide a WiFi
access point. That means that the previously used WiFi connection to
the local wireless network will not work when RaspAP is installed.
When internet access is needed you have to connect an Ethernet cable.
Another option is to use a 4G/LTE modem, like the HUAWEI E3372, and then
the detector also can be used as a WiFi access point for internet access.

Download and install RaspAp.

    curl -sL https://install.raspap.com | bash

    # It is ok to select "Y" on all steps during the installation.
    # OpenVPN and Wireguard are not used, you can press "N" for them.

Restart the detector.

    sudo reboot

Connect to the wifi network named raspi-webgui. Password: ChangeMe.

Start a web browser and go to: http://10.3.141.1.

If the detector is using an Ethernet cable the web address "http://wurb99.local/"
will work from any computer in the network (if the hostname is wurb99).

Login for the administration page: Username: **admin**, password: **secret**.

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

## Run the detector

- Connect the ultrasonic microphone to the detector (can also be done after startup).
- Connect USB memory stick(s) (optional, or can be done after startup).
- Start the Raspberry Pi. It will start automatically when power is added.
- Connect a computer or mobile phone to the WiFi network called "wifi4bats". Password: chiroptera.
- Open a web browser and go to http://10.3.141.1:8000 (http://wurb99:8000 will work if not using RaspAP.)
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
