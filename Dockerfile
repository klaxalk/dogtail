FROM ubuntu:20.04

RUN apt-get -y update && apt-get -y install sudo

# workaround interractive prompts during apt installations
RUN echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install keyboard-configuration

RUN apt -y install python3-pip

RUN pip3 install docker

COPY log.py /

CMD ["python3", "-u", "/log.py"]
