#!/bin/bash

sudo apt update

sudo apt-get install mysql-server

sudo systemctl start mysql
sudo systemctl enable mysql

sudo mysql -e 'set global validate_password.policy = LOW;'

username="dpmysql"
export password=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')

truncate -s 0 /var/.dpmysql
echo $password >> /var/.dpmysql

sudo mysql << EOF
DROP USER '$username'@'localhost';
FLUSH PRIVILEGES;
EOF

sudo mysql << EOF
CREATE USER '$username'@'localhost' IDENTIFIED BY '$password';
GRANT ALL PRIVILEGES ON *.* TO '$username'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF
