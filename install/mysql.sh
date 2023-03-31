#!/bin/bash

sudo apt update

sudo apt-get install mysql-server

sudo systemctl start mysql
sudo systemctl enable mysql

sudo mysql -e 'set global validate_password.policy = LOW;'
