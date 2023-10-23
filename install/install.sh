#!/bin/bash

apt update
apt-get install -y unzip
apt-get install -y python3
apt-get install -y python3-venv
apt-get install -y python3-pip
ufw allow 8080

dpanel_url="https://dpanel.de-ver.com/dpanel.zip"
dpanel_dir="/var/server/dpanel/app/"
mkdir -p "$dpanel_dir"
wget -N "$dpanel_url" -P "$dpanel_dir" && unzip -oqq "$dpanel_dir/dpanel.zip" -d "$dpanel_dir"
rm $dpanel_dir/dpanel.zip
if [ $? -eq 0 ]; then
  echo "ZIP file downloaded and extracted successfully to '$dpanel_dir'."

  python3 -m venv /var/server/dpanel/venv
  /var/server/dpanel/venv/bin/pip install django
  /var/server/dpanel/venv/bin/pip install django_widget_tweaks

  dpanel_service="/etc/systemd/system/dpanel.service"
  if [ -f "$dpanel_service" ]; then
      echo "Service file already exists at $dpanel_service."
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
  echo "
  ----------------------------------------------------------------------------------------------
  Dpanel has been installed successfully.
  Login to your Dpanel at http://$local_ip:8080
  Username: admin
  Password: admin
  ----------------------------------------------------------------------------------------------
  "
else
  echo "Failed to install Dpanel."
fi