
# TODO: At the moment it is not possible 
# to access the sound routines in libportaudio2
# from inside the container. 
# Therefore "wurb_rec" must be deployed outside
# docker. This part is for test only.

FROM python:3

RUN apt-get -y update 
RUN apt-get -y upgrade 
RUN apt-get -y install git 
RUN pip install --upgrade pip 

EXPOSE 8000

RUN apt-get -y install libportaudio2

# Get software and install libraries.
COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Our code. After install 
COPY ./ /wurb_rec

# RUN mkdir /recorded_files
