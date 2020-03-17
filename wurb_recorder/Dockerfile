FROM python:3

RUN apt-get -y update 
RUN apt-get -y upgrade 
RUN apt-get -y install git 
RUN pip install --upgrade pip 

EXPOSE 19594

RUN apt-get -y install libportaudio2

# Get software and install libraries.
COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Our code. After install 
COPY ./ /wurb_recorder

RUN mkdir /recorded_files
