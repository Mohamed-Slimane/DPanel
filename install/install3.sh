#!/bin/bash

apt update
apt-get install python3
apt-get install python3-venv
apt-get install python3-pip
ufw allow 8080

dpanel_url="https://dpanel.de-ver.com/dpanel.zip"
dpanel_dir="/var/server/dpanel/app/"
mkdir -p "$dpanel_dir"
wget "$dpanel_url" -P "$dpanel_dir" && unzip "$dpanel_dir/dpanel.zip" -d "$dpanel_dir"

if [ $? -eq 0 ]; then
  echo "ZIP file downloaded and extracted successfully to '$dpanel_dir'."

  python3 -m venv /var/server/dpanel/venv
  /var/server/dpanel/venv/bin/pip install django
  /var/server/dpanel/venv/bin/pip install django_widget_tweaks

  dpanel_service="/etc/systemd/system/djpanel.service"
  if [ -f "$dpanel_service" ]; then
      echo "Service file already exists at $dpanel_service. Aborting."
      exit 1
  fi
  service_content="[Unit]
  Description=DPanel service
  After=network.target

  [Service]
  Group=www-data
  WorkingDirectory=/var/server/dpanel/app
  ExecStart=/var/server/dpanel/venv/bin/python /var/server/dpanel/app/manage.py runserver 0.0.0.0:8080
  Restart=always

  [Install]
  WantedBy=multi-user.target
  "
  echo "$service_content" | sudo tee "$dpanel_service"
  if [ -f "$dpanel_service" ]; then
      echo "Service file created successfully at $dpanel_service."

      systemctl enable dpanel
      systemctl start dpanel
  else
      echo "Failed to create the service file."
  fi

  local_ip=$(hostname -I)
  echo "Dpanel has been installed successfully."
  echo "Login to your Dpanel at http://$local_ip:8080"
  echo "Username: admin"
  echo "Password: admin"

else
  echo "Failed to install Dpanel."
fi


#sudo apt install libpq-dev
#sudo apt install python3-dev
#sudo apt-get install build-essential
#sudo apt-get install nginx

#sudo ufw allow 80
#sudo ufw allow 443
#sudo ufw allow http
#sudo ufw allow https
#sudo ufw allow 'Nginx Full'


#sudo systemctl start nginx
#sudo systemctl enable nginx

