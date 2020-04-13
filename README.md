#  CloudedBats - WURB 2020

**Note: New version of the bat detector - work in progress.**

The old version can be found here: https://github.com/cloudedbats/cloudedbats_wurb

## New features

Some differences from a user perspective:

- The detector acts as a WiFi Hotspot/AccessPoint and contains a web server. 
- Web pages are used for configuration and control.
- Automatic detection of connected ultrasonic microphones.
- etc.

## Software

Notes from a developers perspective:

- Software completely rewritten. Python 3.7+ needed.
- Raspbian Buster Lite used for Raspberry Pi 4 support.
- RaspAP (https://raspap.com/) used to run the detector as a WiFi Hot Spot.
- More modular software design by use of micro services.
- API:s are specified as OpenAPI 3.0.
- Asynchronous (async/await) programming both in frontend and backend.
- WebSockets are used for fast client updates.
- Stylesheets for responsive web pages are based on Bulma (https://bulma.io).
- FastAPI and uvicorn (https://www.uvicorn.org) are used to run the asynchronous web services.
- Pythons new asyncio library is used to replace all threads in the backend services. 
- Sounddevice (https://python-sounddevice.readthedocs.io/) used instead of pyaudio.

## Hardware needed

- Any Raspberry Pi model with WiFi. (RPi Zero W works but is not recommended.) 
- SD card. For example Toshiba Exceria Pro 16GB, or similar.
- Ultrasonic microphone. Tested with Pettersson u256, u384, M500-384 and UltraMic 192K.

Note: For some strange reason M500-384 has problems if connected directly to a 
Raspberry Pi 4 at startup. Workarounds are to use an extra USB 2.0 Hub, or 
attach the M500-384 microphone after startup.

Optional hardware:

- USB memory to store recorded sound files. 
- GPS USB dongle. (Support for this not implemented yet.)
- Witty Pi 3 from UUGear.com. An extra board for the Raspberry Pi that adds a lot of 
missing features: On/off button, real time clock, possibility to use other 
power sources than 5V, and scripting capability for turning the unit on/off 
to save battery during daytime. 
http://www.uugear.com/product/witty-pi-3-realtime-clock-and-power-management-for-raspberry-pi/

## Installation

Use Raspberry Pi Imager to download Raspbian Buster Lite 
and install it on a SD card. Raspberry Pi Imager can be found here: 
https://www.raspberrypi.org/downloads

Connect the SD card to a computer and add an empty file with 
the name "ssh" to the SD card (the SD card will have the name 
"boot" when connected). This step is done to activate the possibility
to connect to the Raspberry Pi via ssh. 

Insert the SD card into you Raspberry Pi, connect an Ethernet 
cable and start it.

### Raspberry Pi setup:

Connect to the Raspberry Pi from a computer over ssh. 
The address "raspberrypi.local" can be used if your computer supports mDNS. 
Otherwise you have to check up the IP number:

    ssh pi@raspberrypi.local
    
Default password is: raspberry

Update the Raspberry Pi: 

    sudo apt-get update
    sudo apt-get dist-upgrade

Make some configurations:

    sudo raspi-config

For example, if you live in Sweden:

- Password: chiroptera
- Network options - Hostname: wurb 
- Localisation Options - Timezone: Europe - Stockholm
- Localisation Options - WiFi-country: SE
- Advanced Options - Expand Filesystem.

Reboot and reconnect to:

    sudo reboot
    # Wait...
    ssh pi@wurb.local

### RaspAP

Download and install RaspAp (https://raspap.com):

    curl -sL https://install.raspap.com | bash

Connect to the wifi network named raspi-webgui. Password: ChangeMe.

Start a web browser and go to: http://10.3.141.1. Username: admin, password: secret.

Change the defaults settings from:

- SSID: raspi-webgui
- Password: ChangeMe
- Admin username: admin
- Password: secret

Change to:

- SSID: wifi4bats
- Password: chiroptera
- Admin username: batman
- Password: chiroptera
- Country Code: SE

About Internet connection:

When running the detector as a standalone unit and the Ethernet cable is not connected to 
the Raspberry Pi, then Internet is not available. 
That's ok if you only want to control the detector. If you have to, for example, 
upgrade the Raspberry Pi, then you must connect an Ethernet cable to it to reach Internet.
For advanced users there are a wide range of opportunities to set up networks with 
multiple collaborating Raspberry Pi units.


### CloudedBats software

Check that the Python version is 3.7 or later. If not you 
have to download and install a new version:

    python3 --version

Install software:

    sudo apt install python3-venv
    sudo apt install libportaudio2
    sudo apt install libatlas-base-dev # Only needed if gunicorn is used.

    git clone https://github.com/cloudedbats/cloudedbats_wurb_2020.git
    cd cloudedbats_wurb_2020/
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt 

    sudo nano /etc/rc.local 

    # Add this before the "exit" row: 
    sudo -u pi bash /home/pi/cloudedbats_wurb_2020/wurb_rec_start.sh &

And finally restart the detector:

    sudo reboot


## Run the detector

**Note: Again - work in progress - only a few parts have been implemented so far.**

- Start the Raspberry Pi with an ultrasonic microphone attached.
- Connect a computer or mobile phone to the WiFi network called "wifi4bats".
- Open a web browser and go to http://10.3.141.1:8000
- Press "Start recording".
- Record some bats.
- Press "Start recording".
- Go to the WiFi administration page at http://10.3.141.1
- Select "System" and press "Shutdown" to turn off the detector.

If files are stored on the SD card then they can be downloaded by 
using for example FileZilla. Connect with SFTP to http://10.3.141.1 
with user "pi" and password "chiroptera".

Note: Some mobile phones complains if the "wifi4bats" network not is 
connected to internet. If that happens, then tell it to forget the network, 
connect to i again and answer the question if you want to connect to it
anyway.


## Contact

Arnold Andreasson, Sweden.

info@cloudedbats.org
