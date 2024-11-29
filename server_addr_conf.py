import os
import socket

import console, utils

file_dir = os.path.join(utils.app_dir, 'server_addr.txt')

def read() -> tuple:
    console.print('正在读取服务器地址文件: ' + file_dir + '\n')
    with open(file_dir, 'r') as f:
        lines = f.readlines()
    if len(lines) != 2:
        raise ValueError("文件格式错误，应包含两行：IP地址和端口")
    ip = lines[0].strip()
    port = lines[1].strip()
    
    try:
        socket.inet_aton(ip)
    except socket.error:
        raise ValueError(f"无效的 IP 地址: {ip}")
    if ip == '0.0.0.0':
        raise ValueError(f"尚未设置 IP 地址")
    if not port.isdigit() or not (0 < int(port) <= 65535):
        raise ValueError(f"无效的端口号: {port}")

    return ip, int(port)

def write(ip: str, port: int):
    with open(file_dir, 'w') as f:
        f.write(f"{ip}\n{port}\n")
