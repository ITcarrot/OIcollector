import traceback, os, sys, time, shutil
from datetime import datetime
import socket, psutil
import json, re
import multiprocessing, threading
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
    data['start_time'] = datetime.strptime(data['start_time'], "%Y-%m-%d %H:%M:%S")
    data['end_time'] = datetime.strptime(data['end_time'], "%Y-%m-%d %H:%M:%S")

    return data

def Part2_handle_client(client_socket: socket.socket, client_id: int):
    try:
        # Step 1
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client_socket.sendall(f"{client_id}\n{current_time}".encode())
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
        time.sleep(max(0, wait_time) + 2 + utils.ACCEPT_MOD_TIME_DELTA * 2)
        communicate.extract_file(tar_file_path, tmp_dir)
        # Step 5
        recv_file_path = os.path.join(tmp_dir, f'GD-{client_id}', 'test', 'test.cpp')
        recv_file_mtime = utils.get_file_mtime(recv_file_path)
        recv_file_md5 = utils.get_file_md5(recv_file_path)
        client_socket.sendall(f'{recv_file_mtime}\n{recv_file_md5}'.encode())

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
    
    namelist = []
    with open(namelist_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue  # 忽略空行
            if not re.match(server_conf['regex'], line):
                console.print(f'选手 {line} 不符合设定的考号格式，请联系考点负责人\n', 'red')
                sys.exit()
            namelist.append(line)
    console.print(f'本考场应到 {len(namelist)} 人，请核对\n')
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

    return namelist

def Part4(server_addr: tuple, server_conf: dict):
    console.print('\n即将进入赛前学生机文件检查模式\n')
    console.wait_y()
    console.clear()
    # calc md5
    provided_file_dir = os.path.join(utils.app_dir, f"{server_conf['name']}下发文件")
    provided_files = os.listdir(provided_file_dir)
    for i in range(len(provided_files)):
        file_path = os.path.join(provided_file_dir, provided_files[i])
        file_md5 = utils.get_file_md5(file_path)
        provided_files[i] = (provided_files[i], file_md5)
    provided_files = '\n'.join(map(lambda x: f'{x[0]} {x[1]}', provided_files))
    assert len(provided_files) < 1000
    console.print('学生机下发文件清单：\n')
    console.print(provided_files + '\n')
    # server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(server_addr)
    server_socket.listen()
    console.print(f'服务器已经运行在 {server_addr[0]}:{server_addr[1]}\n')
    while True:
        client_socket, client_address = server_socket.accept()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client_socket.sendall(f'{current_time}\n{provided_files}'.encode())
        client_socket.close()
        console.print(f"{client_address} 于 {current_time} 接入\n")

screen_thread_alive = threading.Event()
def Part5_screen(server_addr: tuple, src_dir: str, namelist: list):
    global screen_thread_alive
    checksum_dir = os.path.join(src_dir, 'checksum')
    while screen_thread_alive.is_set():
        console.clear()
        console.print(f'代码收集服务器已经运行在 {server_addr[0]}:{server_addr[1]}\n')
        console.print('绿色：已收集 ', 'green')
        console.print('黄色：正在收集 ', 'yellow')
        console.print('白色：未收集 ')
        console.print('红色：存在问题\n', 'red')
        
        src_list = os.listdir(src_dir)
        checksum_list = os.listdir(checksum_dir)
        for i in range(len(namelist)):
            if i % 5 == 0:
                console.print('\n')
            user_id = namelist[i]
            checksum_file = os.path.join(checksum_dir, f'{user_id}.txt')
            try:
                if f'{user_id}.txt' in checksum_list:
                    if os.path.getsize(checksum_file) > 0:
                        console.print(user_id, 'green' if user_id in src_list else 'red')
                    else:
                        console.print(user_id, 'yellow')
                else:
                    console.print(user_id, 'red' if user_id in src_list else '')
            except:
                console.print(user_id, 'red')
            finally:
                console.print(' ' * 4)
        
        for dir in src_list:
            try:
                assert os.path.isdir(os.path.join(src_dir, dir))
                assert dir == 'checksum' or (dir in namelist)
            except:
                console.print(f'\n{src_dir} 下有多余文件 {dir}', 'red')
        for file in checksum_list:
            try:
                assert os.path.isfile(os.path.join(checksum_dir, file))
                assert file[:-4] in namelist
                assert file[-4:] == '.txt'
            except:
                console.print(f'\n{checksum_dir} 下有多余文件 {file}', 'red')
        time.sleep(3)

def Part5_handle_client(client_socket: socket.socket, header: list, src_dir: str):
    checksum_dir = os.path.join(src_dir, 'checksum')
    tmp_dir = os.path.join(utils.app_dir, 'tmp')
    user_id = header[0]
    user_dir = os.path.join(src_dir, user_id)
    user_checksum = os.path.join(checksum_dir, f'{user_id}.txt')
    tarfile_path = os.path.join(tmp_dir, f'{user_id}.tar.gz')
    
    try:
        tarfile_size = int(header[1])
        submit_files_md5 = header[2:]
        submit_files = list(map(lambda x: x.split(' ')[0], submit_files_md5))
        submit_md5 = list(map(lambda x: x.split(' ')[1], submit_files_md5))
        client_socket.sendall('yes'.encode())
        with open(tarfile_path, "wb") as f:
            received_data = 0
            while received_data < tarfile_size:
                data = client_socket.recv(1048576)
                f.write(data)
                received_data += len(data)
        communicate.extract_file(tarfile_path, src_dir)
        
        try:
            for i in range(len(submit_files)):
                if utils.get_file_md5(os.path.join(user_dir, submit_files[i])) != submit_md5[i]:
                    raise ValueError(f"{submit_files[i]} 校验不通过")
            for dirpath, dirnames, filenames in os.walk(user_dir):
                for filename in filenames:
                    full_path = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(full_path, user_dir)
                    if relative_path not in submit_files:
                        raise ValueError(f"存在多余文件 {relative_path}")
        except ValueError as e:
            client_socket.sendall(str(e).encode())
            raise
        with open(user_checksum, 'w') as f:
            f.write('\n'.join(submit_files_md5))
            f.write(f'\n{user_id}.txt {utils.get_str_list_md5(submit_files_md5)}')
        with open(user_checksum, 'r') as f:
            client_socket.sendall(''.join(f.readlines()).encode())
    except:
        shutil.rmtree(user_dir, True)
        os.remove(user_checksum)
    finally:
        client_socket.close()

def Part5(server_addr: tuple, server_conf: dict, namelist: list):
    console.print('\n即将进入赛后收代码模式\n')
    console.wait_y()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(server_addr)
    server_socket.listen()

    src_dir = os.path.join(utils.app_dir, server_conf['name'])
    checksum_dir = os.path.join(src_dir, 'checksum')
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(checksum_dir, exist_ok=True)
    screen_thread = threading.Thread(target=Part5_screen, args=(server_addr, src_dir, namelist), daemon=True)
    global screen_thread_alive
    screen_thread_alive.set()
    screen_thread.start()
    
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            header = client_socket.recv(1024).decode().split('\n')
            user_id = header[0]
            user_src = os.path.join(src_dir, user_id)
            user_checksum = os.path.join(checksum_dir, f'{user_id}.txt')
            
            response = ''
            if user_id not in namelist:
                response += f'{user_id} 不属于这个考场\n'
            if os.path.exists(user_src):
                response += f'考号重复，请核对选手考号或在服务器删除已有代码 {user_src}\n'
            if os.path.exists(user_checksum):
                response += f'考号重复，请核对选手考号或在服务器删除已有校验码 {user_checksum}\n'
            if response != '':
                client_socket.sendall(response.encode())
                client_socket.close()
                continue

            with open(user_checksum, 'w') as f:
                pass
            process = multiprocessing.Process(target=Part5_handle_client, args=(client_socket, header, src_dir))
            process.start()
    finally:
        screen_thread_alive.clear()
        screen_thread.join()

def main():
    try:
        os.makedirs(tmp_dir, exist_ok=True)

        server_addr = Part1()
        console.print(f'服务器将监听: {server_addr[0]}:{server_addr[1]}\n', 'green')
        try:
            server_conf = load_server_conf()
        except FileNotFoundError as e:
            console.print('没有比赛配置文件，即将进入系统校验模式\n')
            Part2(server_addr)
            sys.exit()
        namelist = Part3(server_addr, server_conf)
        if datetime.now() < server_conf['start_time']:
            Part4(server_addr, server_conf)
        elif datetime.now() > server_conf['end_time']:
            Part5(server_addr, server_conf, namelist)
        else:
            console.print('比赛期间开服务器干什么>_<\n', 'red')
            sys.exit()

    except Exception as e:
        console.print(traceback.format_exc())
        console.print("程序出现未知错误，请联系考点负责人\n", 'red')

if __name__ == '__main__':
    multiprocessing.freeze_support()
    console.start('Code Collector Server', main)
