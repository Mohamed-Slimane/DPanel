#!/bin/bash

# Update packages
apt update

# Install required packages
apt-get install -y unzip python3 python3-venv python3-pip ufw wget

# Allow port 8752 through firewall
ufw allow 8752

# Define Dpanel variables
dpanel_url="https://dpanel.de-ver.com/api/download/dpanel.zip"
dpanel_dir="/var/server/dpanel/app/"
dpanel_venv="/var/server/dpanel/venv/"
dpanel_service="/etc/systemd/system/dpanel.service"

# Create directories
mkdir -p "$dpanel_dir"

# Download and extract Dpanel
wget -N "$dpanel_url" -P "$dpanel_dir" && unzip -oqq "$dpanel_dir/dpanel.zip" -d "$dpanel_dir" && rm "$dpanel_dir/dpanel.zip"

if [ $? -eq 0 ]; then
  echo "ZIP file downloaded and extracted successfully to '$dpanel_dir'."

  # Setup Python virtual environment
  python3 -m venv "$dpanel_venv"
  "$dpanel_venv/bin/pip" install django django_widget_tweaks

  # Run database migrations
  "$dpanel_venv/bin/python" "$dpanel_dir/manage.py" makemigrations
  "$dpanel_venv/bin/python" "$dpanel_dir/manage.py" migrate

  # Create superuser
  dpanel_password=$(python3 -c "import random; print(''.join([str(random.randint(0, 9)) for _ in range(10)]))")
  "$dpanel_venv/bin/python" "$dpanel_dir/manage.py" shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@localhost', '$dpanel_password')"

  # Create systemd service
  echo "[Unit]
Description=DPanel service
After=network.target

[Service]
Group=www-data
WorkingDirectory=$dpanel_dir
ExecStart=$dpanel_venv/bin/python $dpanel_dir/manage.py runserver 0.0.0.0:8752
Restart=always

[Install]
WantedBy=multi-user.target" | sudo tee "$dpanel_service" >/dev/null
  echo "Service file created successfully at $dpanel_service."
  systemctl enable dpanel
  systemctl start dpanel

  # Get publick server ip
  local_ip=$(hostname -I | awk '{print $1}')
  echo "
  ----------------------------------------------------------------------------------------------
  Dpanel has been installed successfully.
  Login to your Dpanel at http://$local_ip:8752
  Username: admin
  Password: $dpanel_password
  Please change the password after first login to prevent unauthorized access to your panel.
  ----------------------------------------------------------------------------------------------
  "
else
  echo "Failed to install Dpanel."
fi
