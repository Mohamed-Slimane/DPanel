import os
import subprocess
from datetime import datetime
from django.utils.translation import gettext_lazy as _
from dpanel.functions import save_option


def has_certbot_cert(domain):
    cert_dir = f"/etc/letsencrypt/live/{domain}"
    return os.path.exists(cert_dir)


def create_ssl(domain):
    command = [
        "certbot",
        "certonly",
        "--nginx",
        "-d",
        domain.name,
        "--email",
        f"admin@{domain.name}",
        "--agree-tos"
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)

    if result.returncode == 0:
        for line in result.stdout.split('\n'):
            if "VALID:" in line:
                parts = line.split("VALID: ")
                expiration_date = parts[1].strip()
                expiration_date = datetime.strptime(expiration_date, "%B %d %Y %H:%M:%S %Z")
                return expiration_date
    # Create a symbolic link to enable the new Nginx configuration
    # os.system(f"ln -s /etc/nginx/sites-available/{app.serial}.conf /etc/nginx/sites-enabled/{app.serial}.conf")


def install_certbot():
    try:
        subprocess.run(["apt", "update"])
        subprocess.run(["apt", "install", "-y", "certbot"])
        subprocess.run(["apt", "install", "-y", "python3-certbot-nginx"])
        subprocess.run(['ufw', 'allow', 'https'])
        subprocess.run(['ufw', 'allow', '443'])
        success = True
        message = _("Certbot has been successfully installed")
        save_option('certbot_status', True)

    except subprocess.CalledProcessError as e:
        success = False
        message = _("An error occurred while installing Certbot: {}").format(e)

    return {
        'success': success,
        'message': message
    }