import time

import paramiko
import os
import stat
import configparser

# --- Load credentials ---
config = configparser.ConfigParser()
config.read("config.cfg")

joc1_server_ip = "IT106570.users.bris.ac.uk"
joc1_server_user = config["SSH"]["farm_server_user"]
joc1_server_password = config["SSH"]["farm_server_password"]

# Remote and local base directories
remote_base_dir = "/mnt/storage/frontend"
local_base_dir = "/mnt/storage/frontend"

def sftp_recursive_download(sftp, remote_path, local_path):
    os.makedirs(local_path, exist_ok=True)
    for item in sftp.listdir_attr(remote_path):
        remote_item = f"{remote_path}/{item.filename}"
        local_item = os.path.join(local_path, item.filename)
        if stat.S_ISDIR(item.st_mode):
            sftp_recursive_download(sftp, remote_item, local_item)
        else:
            print(f"Downloading: {remote_item}")
            sftp.get(remote_item, local_item)

def main():
    print("Connecting to joc1 server...")
    transport = paramiko.Transport((joc1_server_ip, 22))
    transport.connect(username=joc1_server_user, password=joc1_server_password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    print(f"Downloading everything from {remote_base_dir}...")
    sftp_recursive_download(sftp, remote_base_dir, local_base_dir)

    sftp.close()
    transport.close()
    print(f"✅ Download completed. Local directory mirrors {remote_base_dir}")

if __name__ == "__main__":
    while True:
        try:
            main()
            time.sleep(60)
        except paramiko.ssh_exception.AuthenticationException as e:
            print(e)
