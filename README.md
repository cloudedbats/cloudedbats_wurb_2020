#  CloudedBats - WURB 2020

**Note: This is a new version of the WURB bat detector.
The old version can still be found here: 
https://github.com/cloudedbats/cloudedbats_wurb**

## New features

Some differences from a user perspective:

- The detector acts as a WiFi Hotspot/AccessPoint and contains a web server. 
- Web pages are used for configuration and control.
- Automatic detection of connected Ultrasonic microphones.
- Automatic detection of connected USB GPS Receiver.
- etc.

## Software

Notes from a developers perspective:

- Software completely rewritten. Python 3.7+ needed.
- Raspbian Buster Lite used for Raspberry Pi 4 support.
- RaspAP (https://raspap.com/) used to run the detector as a WiFi Hotspot/AccessPoint.
- More modular software design by use of micro services.
- API:s are specified as OpenAPI 3.0.
- Asynchronous (async/await) programming both in frontend and backend.
- WebSockets are used for fast client updates.
- Stylesheets for responsive web pages are based on Bulma (https://bulma.io).
- FastAPI and uvicorn (https://www.uvicorn.org) are used to run the asynchronous web services.
- Pythons new asyncio library is used to replace all threads in the backend services. 
- Sounddevice (https://python-sounddevice.readthedocs.io/) used instead of pyaudio.

## Hardware needed

- Any Raspberry Pi model with WiFi. (RPi Zero W may work but is not recommended.) 
- SD card. For example Toshiba Exceria Pro 16GB, or similar.
- Ultrasonic microphone. Tested with Pettersson u256, u384, M500-384 and 
Dodotronic UltraMic 192K, 250K, 384K BLE.

**Note:** For some strange reason M500-384 has problems if connected directly to a 
Raspberry Pi 4 at startup (RPi3B+ works fine). Workarounds are to use an extra USB 2.0 Hub, 
or attach the M500-384 microphone after startup.

Optional hardware:

- USB memory sticks. This is optional since the internal SD card will be used for storage if 
no USB sticks are available. More than one memory stick can be used.
- USB GPS Receiver using the NMEA format. Tested with "Navilock NL-602U" and "GPS/GLONASS U-blox7".
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

    sudo apt update
    sudo apt upgrade

Make some configurations:

    sudo raspi-config

Change this (example for Swedish users):

- Password: chiroptera
- Network options-Hostname: wurb 
- Localisation Options-Timezone: Europe - Stockholm
- Localisation Options-WLAN Country: SE
- Advanced Options-Expand Filesystem.

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
For advanced users there are a wide range of opportunities to set up networks with 
multiple collaborating Raspberry Pi units.

### Install packages

Check that the Python version is 3.7 or later. If not you 
have to download and install a new version:

    python3 --version

Install software:

    sudo apt install git python3-venv python3-dev
    sudo apt install libportaudio2 libatlas-base-dev udevil
    sudo apt install python3-rpi.gpio

### USB GPS Receiver (optional)

The detector is listening to GPS units that are connected to  
"/dev/ttyACM0" or "/dev/ttyUSB0". Only NMEA format is supported. 
If there are problems this may help:

    # Connect the USB GPS Receiver and check if it is available.
    ls /dev/ttyUSB*
    ls /dev/ttyACM*

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

    ( sleep 5 && sudo -u pi devmon ) &
    sudo -u pi bash /home/pi/cloudedbats_wurb_2020/wurb_rec_start.sh &

And finally restart the detector:

    sudo reboot


## Run the detector

- Connect the ultrasonic microphone to the detector (can also be done after startup).
- Connect USB memory stick(s) (optional, or can be done after startup).
- Start the Raspberry Pi. It will start automatically when power is added.
- Connect a computer or mobile phone to the WiFi network called "wifi4bats". Password: chiroptera.
- Open a web browser and go to http://10.3.141.1:8000
- Check "Geographic location" and "Settings". 
- Press "Start recording".
- Record some bats.
- Press "Stop recording".

There are different ways to turn the Raspberry Pi detector off (power off only is not
recommended since there is a small risk of corrupted SD card or USB memory sticks): 

- Go to "Settings - More" and press the "Shutdown" button.
- Go to the WiFi administration page at http://10.3.141.1. Select "System" and press "Shutdown".
- If you are using a "Witty Pi 3" board from UUGear.com, just press the power off button. 

More than one USB memory stick can be used. They will be filled up with wave files 
in alphabetic order. When the last USB memory stick is full, then it will continue 
on the SD card. It will stop when there is less than 0.5 GB left on the SD card.

If files are stored on the SD card then they can be downloaded and/or removed by 
using for example FileZilla. Connect with SFTP to http://10.3.141.1 
with user "pi" and password "chiroptera".
Path to files on the SD card: "/home/pi/wurb_files".

It is also possible to download files by using FileZilla, or similar, from the USB 
memory stick during an ongoing recording session. The path to the USB memory is then 
"/media/pi/<your-usb-memory-stick-name>".

Note: Some mobile phones complains if the "wifi4bats" network not is 
connected to internet. If that happens, then tell it to forget the network, 
connect to i again and answer the question if you want to connect to it
anyway.


## Contact

Arnold Andreasson, Sweden.

info@cloudedbats.org
