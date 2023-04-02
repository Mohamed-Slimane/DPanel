import crypt
import os
import pwd
import uuid
import subprocess

try:
    pwd.getpwnam('dpuser')
    print(pwd.getpwnam('dpuser'))
except KeyError:

    p = str(uuid.uuid4()).replace('-', '')
    n = 'dpuser'

    encPass = crypt.crypt(p, "22")
    os.system(f"useradd {n} -p {encPass} -s /bin/bash -d /home/{n} -m --groups sudo --gid sudo ")

    try:
        os.remove('/var/.dpuser')
    except FileNotFoundError:
        pass

    cmd = f"sudo -u postgres createuser --superuser -W {p} {n}"
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p.communicate(input=f"{p}\n".encode())

    with open('/var/.dpuser', 'w') as fd:
        fd.write(f'{p}')
