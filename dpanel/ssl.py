import os
import subprocess


def has_certbot_cert(domain):
    cert_dir = f"/etc/letsencrypt/live/{domain}"
    return os.path.exists(cert_dir)


def create_domain_ssl(domain_name):
    # Create a new SSL certificate for the domain using Certbot
    if has_certbot_cert(domain_name):
        certbot_cmd = f"sudo certbot renew --nginx --cert-name {domain_name}"
    else:
        certbot_cmd = f"sudo certbot --nginx --agree-tos --no-redirect --email admin@{domain_name} -d {domain_name}"

    subprocess.run(certbot_cmd, shell=True, check=True)

    # Create a symbolic link to enable the new Nginx configuration
    os.system(f"sudo ln -s /etc/nginx/sites-available/{domain_name}.conf /etc/nginx/sites-enabled/{domain_name}.conf")

    # Reload Nginx to apply the new configuration
    # subprocess.run("sudo systemctl reload nginx", shell=True, check=True)
