import traceback, os, sys, time
from datetime import datetime
import socket, psutil
import json, re
from dateutil import parser
import multiprocessing
import zipfile

import console, utils
import server_addr_conf, collector_conf
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

def Part3(server_addr: tuple, server_conf: dict) -> list:
    # Step 2
    console.print(f"比赛名称：{server_conf['name']}\n")
    collector_conf.generate(server_addr, server_conf)
    # Step 3
    namelist_file = [f for f in os.listdir(utils.app_dir) if re.match(r'^namelist.*\.txt$', f)]
    console.print(f'找到选手名单文件：{namelist_file}\n')
    if len(namelist_file) != 1:
        console.print(f'没有发现唯一的选手名单文件！\n', 'red')
        sys.exit()
    namelist_path = os.path.join(utils.app_dir, namelist_file[0])
    
    contestant_count = 0
    with open(namelist_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue  # 忽略空行
            if not re.match(server_conf['regex'], line):
                console.print(f'选手 {line} 不符合设定的考号格式，请联系考点负责人\n', 'red')
                sys.exit()
            contestant_count += 1
    console.print(f'本考场应到 {contestant_count} 人，请核对\n')
    # Step 4
    provided_file_dir = os.path.join(utils.app_dir, f"{server_conf['name']}下发文件")
    problem_file = [f for f in os.listdir(provided_file_dir) if re.match(server_conf['problem_archive'], f)]
    console.print(f'找到题目压缩包：{problem_file}\n')
    if len(problem_file) != 1:
        console.print(f'没有发现唯一的题目压缩包！\n', 'red')
        sys.exit()
    problem_path = os.path.join(provided_file_dir, problem_file[0])

    with zipfile.ZipFile(problem_path, 'r') as zip_file:
        file_names = zip_file.namelist()
        problem_found = set()
        for file_name in file_names:
            directory = os.path.basename(os.path.dirname(file_name))
            if file_name[-3:] == '.in':
                problem_found.add(directory)
    console.print(f"设置了要收集的题目：{server_conf['problem']}\n")
    console.print(f"压缩包中发现的题目：{problem_found}\n")
    if(set(server_conf['problem']) != problem_found):
        console.print(f'题目配置不一致，请和考点负责人确认\n', 'yellow')
        console.wait_y()

def main():
    try:
        os.makedirs(tmp_dir, exist_ok=True)

        server_addr = Part1()
        console.print(f'服务器将监听: {server_addr[0]}:{server_addr[1]}\n', 'green')
        try:
            server_conf = load_server_conf()
        except Exception as e:
            console.print(traceback.format_exc())
            console.print('\n加载服务器配置文件失败，即将进入系统校验模式\n')
            Part2(server_addr)
            sys.exit()
        namelist = Part3(server_addr, server_conf)
        
    except Exception as e:
        console.print(traceback.format_exc())
        console.print("程序出现未知错误，请联系考点负责人\n", 'red')

if __name__ == '__main__':
    multiprocessing.freeze_support()
    console.start('Code Collector Server', main)
