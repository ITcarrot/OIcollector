import traceback, os, sys, time
from datetime import datetime
import socket, psutil
import json
from dateutil import parser
import multiprocessing

import console, utils
import server_addr_conf
import communicate

tmp_dir = os.path.join(utils.app_dir, 'tmp')

def Part1() -> tuple:
    try:
        if os.path.exists(server_addr_conf.file_dir):
            return server_addr_conf.read()
        else:
            console.print('没有服务器地址配置文件，正在自动检测网卡\n')
            net_interfaces = psutil.net_if_addrs()
            ipv4_addresses = []
            for interface, addrs in net_interfaces.items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and addr.address != '127.0.0.1':
                        ipv4_addresses.append(addr.address)
                        console.print(addr.address + '\n')
            
            if len(ipv4_addresses) == 1:
                ip = ipv4_addresses[0]
                console.print('成功获取本机 IP 地址: ' + ip + '\n', 'green')
                server_addr_conf.write(ip, 80)
                return ip, 80
            else:
                server_addr_conf.write('0.0.0.0', 80)
                raise ValueError('自动确定本机 IP 地址失败')

    except Exception as e:
        console.print(traceback.format_exc())
        console.print(str(e) + '\n', 'red')
        console.print('请设置好服务器地址后重新启动服务器')
        sys.exit()

def load_server_conf() -> dict:
    file_path = os.path.join(utils.app_dir, 'server.conf.json')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['start_time'] = parser.isoparse(data['start_time'])
    data['end_time'] = parser.isoparse(data['end_time'])

    return data

def Part2_handle_client(client_socket: socket.socket, client_id: int):
    try:
        # Step 1
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client_socket.send(f"{client_id}\n{current_time}".encode())
        # Step 2
        file_size, file_mtime = client_socket.recv(1024).decode().split('\n')
        file_size = int(file_size)
        # Step 3
        tar_file_path = os.path.join(tmp_dir, f"GD-{client_id}.tar.gz")
        with open(tar_file_path, "wb") as f:
            received_data = 0
            while received_data < file_size:
                data = client_socket.recv(1048576)
                f.write(data)
                received_data += len(data)
        # Step 4
        wait_time = (datetime.strptime(file_mtime, "%Y-%m-%d %H:%M:%S") - datetime.now()).total_seconds()
        time.sleep(max(0, wait_time) + 2)
        communicate.extract_file(tar_file_path, tmp_dir)
        # Step 5
        recv_file_path = os.path.join(tmp_dir, f'GD-{client_id}', 'test', 'test.cpp')
        recv_file_mtime = utils.get_file_mtime(recv_file_path)
        recv_file_md5 = utils.get_file_md5(recv_file_path)
        client_socket.send(f'{recv_file_mtime}\n{recv_file_md5}'.encode())

    finally:
        # Step 6
        client_socket.close()
        # Step 7
        os.remove(tar_file_path)
        os.remove(recv_file_path)
        os.rmdir(os.path.join(tmp_dir, f'GD-{client_id}', 'test'))
        os.rmdir(os.path.join(tmp_dir, f'GD-{client_id}'))

def Part2(server_addr: tuple):
    console.print('\n加载服务器配置文件失败，即将进入系统校验模式\n')
    console.print('即将核对系统时间，请提前打开手机时钟\n')
    console.wait_y()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f'系统时间为 {current_time}，请和北京时间核对\n')
    console.wait_y()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(server_addr)
    server_socket.listen()
    console.clear()
    console.print(f'系统检测服务器已经运行在 {server_addr[0]}:{server_addr[1]}\n')

    client_id = 0
    while True:
        client_socket, client_address = server_socket.accept()
        client_id += 1
        console.print(f"{client_address} 接入，编号为 {client_id}\n")

        process = multiprocessing.Process(target=Part2_handle_client, args=(client_socket, client_id))
        process.start()

def main():
    try:
        os.makedirs(tmp_dir, exist_ok=True)

        server_addr = Part1()
        console.print(f'服务器将监听: {server_addr[0]}:{server_addr[1]}\n', 'green')
        try:
            server_conf = load_server_conf()
            print(server_conf)
            print(server_conf['root_path'])
            print(server_conf['regex'])
        except Exception as e:
            console.print(traceback.format_exc())
            Part2(server_addr)
            sys.exit()
    except Exception as e:
        console.print(traceback.format_exc())
        console.print("程序出现未知错误，请联系考点负责人\n", 'red')

if __name__ == '__main__':
    multiprocessing.freeze_support()
    console.start('Code Collector Server', main)
