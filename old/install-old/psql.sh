#!/bin/bash

sudo apt update
sudo apt-get install postgresql
sudo systemctl start postgresql.service
sudo systemctl enable postgresql.service

export password=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')

truncate -s 0 /var/.dppsql
echo $password >> /var/.dppsql

sudo -u postgres createuser --superuser --createdb --createrole --encrypted "dppsql"
sudo -u postgres psql -c "ALTER USER dppsql WITH PASSWORD '$password';"