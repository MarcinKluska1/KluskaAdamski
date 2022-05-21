## Install requirements
1. [Install Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/)

2. Get our project. 
```Shell
git clone https://github.com/MarcinKluska1/KluskaAdamski.git
```

3. Build docker image

4. Run docker session

## Application features

Our application allows user to detect people on images and videos. There are two endpoints:

1. /Przetwarzanie/wideo/ - used to upload video and  after a short period of time time download the same video with people marked and tracked.

2. /Przetwarzanie/zdjęcia/ - used to upload an image and mark all people on it.