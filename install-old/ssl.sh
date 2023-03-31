#!/bin/bash

sudo apt update

sudo apt-get install certbot python3-certbot-nginx

sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow http
sudo ufw allow https