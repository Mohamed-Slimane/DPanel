#!/bin/bash

sudo apt update
sudo apt-get install postgresql
sudo systemctl start postgresql.service
sudo systemctl enable postgresql.service
