FROM python:3.7.2-stretch

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update -y
RUN apt install libgl1-mesa-glx -y
RUN apt-get install 'ffmpeg'\
    'libsm6'\
    'libxext6'  -y
RUN pip install --upgrade pip

RUN mkdir /webapp
ADD entrypoint.sh /webapp
ADD ./src/requirements.txt /webapp

WORKDIR /webapp

RUN pip install --upgrade --no-cache-dir pip && pip install --no-cache-dir -r requirements.txt

ADD ./src /webapp

#EXPOSE 5000
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
