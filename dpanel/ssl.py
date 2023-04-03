import os
import subprocess


def has_certbot_cert(domain):
    cert_dir = f"/etc/letsencrypt/live/{domain}"
    return os.path.exists(cert_dir)


def create_domain_ssl(domain_name, wildcard=None):
    # Create a new SSL certificate for the domain using Certbot
    "sudo certbot --server https://acme-v02.api.letsencrypt.org/directory -d *.example.com --manual --preferred-challenges dns-01 certonly"
    if wildcard:
        certbot_cmd = f"sudo certbot certonly --manual --no-redirect --preferred-challenges=dns --email admin@{domain_name} --server https://acme-v02.api.letsencrypt.org/directory --agree-tos -d *.{domain_name}"
    elif has_certbot_cert(domain_name):
        certbot_cmd = f"sudo certbot renew --nginx --cert-name {domain_name}"
    else:
        certbot_cmd = f"sudo certbot --nginx --agree-tos --no-redirect --email admin@{domain_name} -d {domain_name}"

    subprocess.run(certbot_cmd, shell=True, check=True)

    # Create a symbolic link to enable the new Nginx configuration
    os.system(f"sudo ln -s /etc/nginx/sites-available/{domain_name}.conf /etc/nginx/sites-enabled/{domain_name}.conf")

    # Reload Nginx to apply the new configuration
    # subprocess.run("sudo systemctl reload nginx", shell=True, check=True)
