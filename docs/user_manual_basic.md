### CloudedBats-WURB
# User manual - basic usage

Welcome to the user manual for the CloudedBats-WURB bat detector.

The user manual is valid for the CloudedBats-WURB 2020 v0.9-version and describes how to use the detector when running without any deviations from the standard installation.

## Introduction

The CloudedBats-WURB detector is a Do-It-Yourself bat detector. The software is provided as open and free software and you have to buy the necessary hardware parts and assemble them yourself.

The main hardware component is the Raspberry Pi microcomputer. They are inexpensive, powerful, easily available, and many uses them for a wide range of hobby projects. Other hardware components are USB devices like USB memory, USB GPS receiver, and the most important component; the ultrasonic microphone. Ultrasonic USB microphones from Pettersson and Dodotronic are supported and identified automatically by the detector.

The user interface for controlling the detector is web-based and any browser on a mobile phone or computer can be used. The detector shares a WiFi network that the client device can connect to. It is also possible to specify a user defined start-up configuration for fast deployment without the need to activate the detector by using the user interface. 

For a detailed instruction on how to build your own detector, please visit the software page at GitHub:
- https://github.com/cloudedbats/cloudedbats_wurb_2020 

Note: To install the software used by the Raspberry Pi you have to be familiar with the operating system Linux and know how to run commands in a terminal window. If not, then you must ask for help. A lot of software developer knows about the Raspberry Pi and should be really happy if they can help someone to monitor cool animals like bats.

### Hardware

This is what it looks like when the detector is assembled for indoor use. When used outdoors it must be protected from rain, moisture and small animals, such as ants, which like the heat produced by the detector.

![WURB v0.9 HW](../images/WURBv0.9-HW-User-manual-basic.jpg?raw=true  "WURB v0.9 Hardware")

Components from left to right:
 
1. Power bank that runs a Raspberry Pi 4 for about 12 hours.
2. The Raspberry Pi 4 microcomputer in a transparent case. Also contains the SD card with software installed.
3. Note the 3.5 mm earphone jacket on the Raspberry Pi. This is used if you want to use the audio feedback feature.
4. The Pettersson u384 USB Ultrasound microphone.
5. A SanDisk Ultra USB 3.0 memory.
6. A USB GPS receiver.

### Quick startup guide

1. Attach power, either from a 5V mobile phone charger or a power bank. Raspberry Pi 4 uses USB-C and Raspberry Pi 3 uses Micro-USB cables for power.
2. Wait until the detector has started. It's normally takes about a minute before the WiFi network is available.
3. Check for WiFi networks from your computer or mobile phone. Connect to "wifi4bats" when it appears. Password: chiroptera.
4. Open a web browser and connect to the address "http://10.3.141.1:8000". Then the user interface should appear. If the field with the detectors time is constantly updated, then you know that the communication between the units works well.
5. Press the button "Set time". This step is necessary if the detector is running without internet connection or without an attached USB GPS receiver. 
6. Use the detector.
7. Turn the detector off by selecting "Detector - Power off..." in the "Mode" selection list, then press the "Shutdown" button. An alternative when running without the user interface is to connect a computer mouse with USB and press the left and right buttons simultaneously for about 5 sec.
8. Wait until the detector has stopped and then disconnect power. 

## About purpose and captured sound

The main purpose of the detector is to make it possible to record bat sound and store the recordings on a USB memory for further analysis later.

The detector should be easy to use for active monitoring, transect monitoring and single night sessions. For advanced usage it should be possible to use it as a permanent monitoring station controlled over internet. It should also be possible for software developers to add post processing functionality since the Raspberry Pi is a powerful computer comparable with a smaller desktop computer.

### Microphone quality

High quality microphones should be supported. The detector does not modify the captured sound stream delivered from the microphone, and the unmodified data stream is saved in the WAV file format. For example, if the Pettersson M500 USB microphone is used, then you can assume that the frequency response is comparable with other detectors from Pettersson that are using the same type of microphone element. But the number of files recorded may differ due to different algorithms used to detect sound.

There is also a possibility for advanced users to experiment with other types of microphones, for example by using special sound cards developed for the Raspberry Pi computer.

### Metadata and filenames

Essential metadata for recorded files are stored in the filenames as parts separated by the underscore sign. Example:

**u384_20210426T155651+0200_N57.6619E12.6389_TE384_29kHz-38dB.wav**

From this example we can extract the following information:

- The prefix "u384" is in this case used to describe the used type of microphone. The prefix is a free text field and can be used for other purposes.
- The timestamp is in the ISO format with the parts: year-month-day, the delimiter "T", hour-minute-second and finally "+0200" that indicates that it is a local timestamp two hours before the UTC time.
- Position as decimal latitude/longitude, N=north, S=south, E=east and W=west.
- TE384 indicates that it is recorded in Time Expansion mode with a sampling frequency of 384 kHz. TE=Time Expansion and FS=Full Spectrum.
- "29kHz-38dB" means that the detection algorithm has found the peak signal in the file at 29 kHz with a signal strength at -38 dBFS. dBFS values are expressed as negative numbers and the value zero indicates the strongest signal before overload. The value of -50 dBFS is the default value for the detector to start recording.
- The file extension ".wav" indicates that the file is stored in the WAV sound file format. 

A note about metadata: Other detectors may use the GUANO metadata format to store embedded metadata inside the WAV file. But this is a conscious choice to not use hidden information that requires special tools to read and modify. GUANO is a great format for metadata, but it is better suited to use in a later step in the workflow. In addition, with the essential metadata in the file name it is easier to search for files with the search options offered by regular file managers.

### Directories where files are stored

Normally the files are stored on the USB memory stick. They are organised in directories (folders) and it is possible to automatically add date to the directories names. To keep recorded files from a single night together it is possible to choose to use the date from before, or after, midnight. See settings below.

In each directory there will be a copy of the file containing the detectors settings. It is a text file with rows containing keywords and values. The name of that file is "wurb_rec_settings.txt".

If there is no USB memory available, or if there is no space left, then the recorded files will be stored internally in the detector. The path is then "/home/pi/wurb_recordings". To get them out from the detector you need to connect to the detector with SFTP. How to do this is described later in this document.

## User interface

This is what it looks like when the user interface is running on a desktop computer. When using a smaller device, like a smart phone, the layout will be automatically adjusted to the smaller screen.

![WURB v0.9 UI-1](../images/WURBv0.9-UI-1-User-manual-basic.jpg?raw=true  "WURB v0.9 User interface")

References to the marked numbers below.

#### 1: Detector modes

The detector can be used for both active and passive monitoring. To make it easy to switch between different modes of usage there is a list of available options.  

- **Microphone - Off**

In this mode the detector is on but the sound stream from the microphone is turned off. That also means that there are no audio feedback.

- **Recording - On (continuously)**

Recording is on and all sound will continuously be saved to files. The file length will still be as specified, for example 6 seconds, and no sound frames will be lost between the files if they are to be concatenated into bigger files later. 

- **Recording - Auto detection**

This mode can be used for both active and passive monitoring. The recording is started when sound is detected, see settings below for more details. A 1.5-2.0 seconds long buffer of recorded sound before the triggering event will be saved to file, and then the recording will last until the specified file length is reached. If needed, the recording will continue and result in more files, all of them with the same length.

- **Recording - Manual triggering**

This is mainly used for active monitoring in combination with audio feedback. A button with the text "Trigger" will appear. The same prefetch buffer as for auto detection is used.

- **Scheduler - Recording on**

The detector is able to calculate when sunset, dusk, dawn and sunrise occurs if a position expressed in latitude/longitude is available. This makes it possible to let the detector automatically adjust the start and stop times for recordings when it is deployed for passive monitoring during longer periods.  

- **Scheduler - Auto detection**

This is mainly the same as "Scheduler - Recording on" but sound files are only stored when sounds are detected in the same way as in the recording mode "Recording - Auto detection".

- **Load "User default" settings**

It is possible to save settings as "User default". When selecting this mode the detector is reset to this state. More info in the settings section below.

- **Load "Start-up" settings**

This is another option similar to the previous one. The only difference is that this one can be defined as the state the detector should have when started.

- **Load "Factory default" settings**

This is used to restore the detector to its initial state. Ii will not change the stored "User default" and "Start-up" settings.

- **Detector - Power off**

Three buttons will appear: "Shutdown", "Restart" and "Cancel". 

It is always a good idea to turn off the detector before removing the power. There is a small risk that the SD card or USB memory will be damaged if there is an ongoing write access when the power is removed. The risk is small, but be careful when it is important that the detector works properly. An extra SD card with installed software may be a good backup solution during critical surveys. 

#### 2. Connected microphones

USB microphones can be attached or removed without turning the detector off. Each time a recording session is activated, then the detector will scan for connected microphones. The name of the used one is displayed here.

#### 3. Info log /  show status

This logging table displays the same information that can be found in the log files located in the detectors internal file system. Most useful are the rows that tells when sound is detected and the peak frequency/strength for that sound. This information will also be stored in the file name of the recorded files, but it may differ if a stronger sound was detected later before the file was stored.

By pressing "Show status" some more info can be displayed in the info log table.

#### 4. Detector time

There is a button called "Set time". It is important to press this button to use the time from the client computer/mobile phone to set the detector time. The Raspberry Pi does not contain an internal clock module and must rely on external sources for that. If it is connected to internet, then the time will be set from internet at startup. If an USB GPS receiver is used, then time will be set automatically 30 sec after it has locked in the satellites. There is also an option to add a Real Time Clock, RTC, module to the Raspberry Pi for the advanced users.
If none of the above is in place, then you have to do this manually by pressing "Set time" each time after startup.

#### 5. Location and GPS

When collecting things from nature, like flowers or insects, it is important to tag them with time and location. The same is valid when collecting sound from bats, and therefore the detector has support for GPS receivers. This is optional, but recommended, and it solves the problem with the missing internal clock module in the Raspberry Pi since the GPS signals also includes timestamps.

Each recorded file has a filename that contains both time and location. This makes it easy to find recordings on your hard disks by searching for parts of the date or latitude/longitude strings. This feature also makes it easy to use the detector for transekt monitoring.

There are some different modes available:

- **Not used**

Latitude and longitude are both set to zero. The scheduler is then not available. 

- **Manually entered**

Use this if you want to use the scheduler and/or tag the files without using a GPS receiver.

- **GPS**

Scheduler is only available when there are GPS satellites detected.

- **GPS or Manually entered**

This is an useful option if GPS is not always attached. It is recommended to use one or two decimals for manually entered positions to distinguish them from the more exact GPS received positions.

- **GPS or Last found GPS or Manually**

This alternative is useful if you have many detectors, but only one GPS receiver. Connect the GPS receiver during deployment and wait until the position is found. Then the same GPS receiver can be used to deploy the next detector.

## User interface for settings

![WURB v0.9 UI-2](../images/WURBv0.9-UI-2-User-manual-basic.jpg?raw=true  "WURB v0.9 User interface - settings")

#### 6. Settings - Audio feedback

There are three major techniques traditionally used to transform ultrasound into something we can hear. They are Heterodyne, Frequency division and Time expansion. This detector uses another technique called Pitch shifting. (This implementation is experimental and will be evaluated during the 2021 years bat season.)

There are two sliders used to control the Pitch shifting. One is the volume control and the other is the factor that the sound pitch should be shifted down. Valid factors are 1/10 - 1/50. The factor 1/30 means that a sound at 30 kHz will be shifted down to 1 kHz. 

#### 7. Settings - Basic

This basic part contains settings that normally are modified at each deployment. You can modify:

- The name of the directory where recorded files are stored.
- If date should automatically be added to that directory.
- The prefix for each sound file.
- The lower limit in kHz for the sound detection algorithm.
- The sensitivity level in dBFS  for the sound detection algorithm.

#### 8. Settings - More

This set of settings are normally not modified that often. Available settings are:

- Which detection algorithm to use. (At the moment there is only one.)
- The length of the recorded sound files. Valid values are 4 - 60 sec.
- Recorded file type; Full Spectrum (FS) or Time Expansion (TE). Note: Both alternatives contains the exact same amount of samples, the only difference is in the header part that tells which sampling frequency that was used. For example 384 kHz in FS mode and 38.4 kHz in TE mode.
- Audio feedback can be turned on or off.
- There are also filter limits for the audio feedback to reduce noise or unwanted low or high frequency sounds.

Finally there are two buttons and a possibility to select the start-up configuration. The buttons "User default" and "Start-up" are used to save settings that are easily available in the detectors mode selection list.

#### 9. Settings - Scheduler

The scheduler needs proper time and position to be able to calculate when the sun goes down and up. It is activated when the detector mode is either "Scheduler - Recording on" or "Scheduler - Auto detection" and the values for latitude and longitude differ from zero. Be sure that the time also is properly set.

It is possible to define one start event and one stop event each day. Either at fixed times or in relation to sunset, dusk, dawn and sunrise.

The "Post action" part is not implemented, reserved for future use.


## Accessing the detectors internal files

Sometimes it can be handy to access the detectors internal files, as well as the USB memory files when it still is attached to the detector. This can be done over SFTP. There are many client software alternatives that support SFTP, for example FileZilla that is available for Windows, macOS and Linux. 

If the detector is up and running and accessible via either WiFi or internet, then the recorded files can be downloaded and analysed at the same time as the detector is recording new files.

Access via SFTP is also useful if you want to:

- Get recorded files that are stored internally instead of on a USB memory.
- Remove recorded files that accidentally was stored internally in the detector.
- Check internal log files and settings files.

#### How to connect

If you are connected to the detectors shared WiFi then connect by setting Transfer protocol: "SFTP", Host: "10.3.141.1", User "pi" and Password "chiroptera".

If the detector is connected to your local network then you can try to use Host: "wurb.local" instead. 

If that doesn't work then you probably have to figure out the IP address for the detector and use that in the Host field. One way to find out the IP address is to install the mobile app "Fing" on your mobile phone and let it scan your local network.

It is also possible to access the detector remotely from outside your local network, but that is outside the scope for this user manual...

#### Where are the internal files located?

The files of interest can be found here:

- /home/pi/wurb_recordings - Contains the recorded files.
- /home/pi/wurb_settings - Contains the files that store the settings used. 
- /home/pi/wurb_logging - Contains logging files.   

The path to the USB memory, where the recorded files normally are stored, can be found here:

- /media/pi/ - This path is followed by the name of the USB memory.

## Contact

Arnold Andreasson, Sweden.
info@cloudedbats.org
