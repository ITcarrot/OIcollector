import socket
import time, random, os
import tarfile

import console, utils

TIMEOUT = 60
RETRY_DELAY = 5

def connect_to_server(server_addr: tuple) -> socket.socket:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(TIMEOUT)

    time.sleep(random.randint(0, RETRY_DELAY))
    while True:
        try:
            client_socket.connect(server_addr)
            return client_socket
        except Exception as e:
            console.print(f"{e} 重试中...\n")
            time.sleep(RETRY_DELAY)

def compress_file(tarfile_path: str, files: list, start_path: str = utils.app_dir):
    with tarfile.open(tarfile_path, 'w:gz') as tarf:
        for file in files:
            tarf.add(file, os.path.relpath(file, start_path))

def extract_file(tarfile_path: str, dest_path: str):
    with tarfile.open(tarfile_path, 'r') as tarf:
        tarf.extractall(dest_path)
