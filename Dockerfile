FROM python:3

ADD . /KluskaAdamski
WORKDIR /KluskaAdamski

COPY requirements.txt ./

RUN apt-get -qq update && apt-get -qq install --no-install-recommends -y python3.9 \
 python3-dev \
 python-pil \
 python-lxml \
 python-tk \
 build-essential \
 cmake \
 git \
 libgtk2.0-dev \
 pkg-config \
 libavcodec-dev \
 libavformat-dev \
 libswscale-dev \
 libtbb2 \
 libtbb-dev \
 libjpeg-dev \
 libpng-dev \
 libtiff-dev \
 libjasper-dev \
 libdc1394-22-dev \
 x11-apps \
 wget \
 vim \
 ffmpeg \
 unzip \
 libcanberra-gtk-module \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -U tensorflow
RUN apt-get update && apt-get install -y python3-opencv
RUN pip install opencv-python
RUN apt-get install ffmpeg libsm6 libxext6  -y


COPY . .

CMD [ "python", "./main.py" ]