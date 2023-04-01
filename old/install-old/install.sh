#!/bin/bash
cd /tmp

sudo apt update
sudo apt-get install python3
sudo apt-get install python3-venv
sudo apt-get install build-essential
sudo apt-get install nginx

sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 'Nginx Full'

sudo ufw allow 8080

sudo systemctl start nginx
sudo systemctl enable nginx

