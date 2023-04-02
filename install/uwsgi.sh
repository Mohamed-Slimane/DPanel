#!/bin/bash

sudo apt update

sudo apt-get install uwsgi
#sudo apt-get install uwsgi-plugin-python3
sudo apt-get install python3-pip

python3 -m pip install uwsgi
python3 -m pip install django

sudo systemctl start uwsgi
sudo systemctl enable uwsgi