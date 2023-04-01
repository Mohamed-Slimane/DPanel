import os
import subprocess


def create_domain_ssl(domain_name):
    # Create a new SSL certificate for the domain using Certbot
    certbot_cmd = f"sudo certbot --nginx --agree-tos --redirect --hsts --staple-ocsp --email admin@{domain_name} -d {domain_name}"
    subprocess.run(certbot_cmd, shell=True, check=True)

    # Create a new Nginx configuration file for the domain with SSL settings
    ssl_config = f"""
    server {{
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name {domain_name};
        ssl_certificate /etc/letsencrypt/live/{domain_name}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/{domain_name}/privkey.pem;
        ssl_trusted_certificate /etc/letsencrypt/live/{domain_name}/chain.pem;
    }}
    """
    with open(f"/etc/nginx/sites-available/{domain_name}.conf", "w") as f:
        f.write(ssl_config)

    # Create a symbolic link to enable the new Nginx configuration
    os.symlink(f"/etc/nginx/sites-available/{domain_name}.conf", f"/etc/nginx/sites-enabled/{domain_name}.conf")

    # Reload Nginx to apply the new configuration
    subprocess.run("sudo systemctl reload nginx", shell=True, check=True)
