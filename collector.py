import traceback, sys, os
from datetime import datetime, timedelta
import re

import console, utils
import collector_conf
import communicate

def Part1() -> dict:
    try:
        return collector_conf.load()
    except Exception as e:
        console.print(traceback.format_exc())
        console.print("读取配置文件失败，请联系监考员\n", 'red')
        console.print(f"{utils.app_dir}下collector开头的文件是代码收集系统的一部分，严禁擅自移动、篡改、删除\n")
        console.print("如违反该要求导致代码漏收、错收，后果由考生自行承担\n")
        sys.exit()

def Part2(collector_conf: dict):
    if utils.app_dir != collector_conf['root_path']:
        console.print('程序不在配置文件指定的目录下，下发文件位置可能不正确！\n', 'yellow')
    console.print('开始进行下发文件完整性检查\n')
    client_socket = communicate.connect_to_server((collector_conf['ip'], collector_conf['port']))
    data = client_socket.recv(1024).decode()
    client_socket.close()

    server_time = data.split('\n')[0]
    console.print(f"服务器时间: {server_time}\n")
    system_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"本机时间: {system_time}\n")
    time_diff = abs((datetime.strptime(system_time, "%Y-%m-%d %H:%M:%S") - datetime.strptime(server_time, "%Y-%m-%d %H:%M:%S")).total_seconds())
    if time_diff > 30:
        console.print("本机和服务器时间相差过大！\n", 'red')
        sys.exit()
    else:
        console.print("时间误差在容许范围内\n", 'green')

    provided_files_md5 = data.split('\n')[1:]
    provided_files = []
    for file in provided_files_md5:
        filename, expected_md5 = file.split(' ')
        provided_files.append(filename)
        try:
            file_path = os.path.join(utils.app_dir, filename)
            file_md5 = utils.get_file_md5(file_path)
        except:
            file_md5 = '文件不存在'
        if expected_md5 == file_md5:
            console.print(f'{filename} 被正确下发\n', 'green')
        else:
            console.print(f'{filename} 应是 {expected_md5} 但实际是 {file_md5}\n', 'red')
    
    exists_files = os.listdir(utils.app_dir)
    for file in exists_files:
        if file not in provided_files:
            console.print(f'检测到多余文件 {file}\n', 'yellow')

def Part3(collector_conf: dict) -> tuple:
    # find dir
    try:
        dirs_files = os.listdir(collector_conf['root_path'])
    except:
        console.print('配置文件指定的目录无法访问，请联系监考员\n', 'red')
        sys.exit()
    dirs = []
    for dir in dirs_files:
        if re.match(collector_conf['regex'], dir) and os.path.isdir(os.path.join(collector_conf['root_path'], dir)):
            dirs.append(dir)
    if len(dirs) == 0:
        console.print('没有找到有效的选手目录. 请阅读考生须知\n', 'red')
        sys.exit()
    if len(dirs) > 1:
        console.print(f'找到多个选手目录 {dirs}，请删除或重命名多余目录\n', 'red')
        sys.exit()
    user_id = dirs[0]
    user_dir = os.path.join(collector_conf['root_path'], user_id)
    console.print(f"找到选手目录： {user_id}, 请确认是否与准考证号一致.\n", 'yellow')
    
    submit_files = []
    submit_files_md5 = []
    for problem in collector_conf['problem']:
        console.print(f"题目 {problem}:\n")
        file_found = False
        file_dir = user_dir
        if collector_conf['use_subdirectory']:
            file_dir = os.path.join(file_dir, problem)
        for suffix in collector_conf['suffix']:
            file_path = os.path.join(file_dir, f'{problem}.{suffix}')
            if os.path.isfile(file_path):
                file_found = True
                console.print(f'\t找到文件 {file_path}\n')
                file_size = os.path.getsize(file_path)
                if file_size <= collector_conf['size_limit_kb'] * 1024:
                    console.print(f'\t\t文件大小 {file_size} 字节\n')
                else:
                    console.print(f'\t\t文件过大！文件大小 {file_size} 字节\n', 'yellow')
                file_mtime = utils.get_file_mtime(file_path)
                file_mtime_datetime = datetime.strptime(file_mtime, "%Y-%m-%d %H:%M:%S")
                if collector_conf['start_time'] <= file_mtime_datetime and file_mtime_datetime <= collector_conf['end_time']:
                    console.print(f'\t\t修改时间有效 {file_mtime}\n')
                else:
                    console.print(f'\t\t修改时间不在比赛时间内！{file_mtime}\n', 'yellow')
                file_md5 = utils.get_file_md5(file_path)
                console.print(f'\t\t校验码 {file_md5}\n')
                submit_files.append(file_path)
                submit_files_md5.append(f'{os.path.relpath(file_path, user_dir)} {file_md5}')
        
        if not file_found:
            console.print('\t未找到源代码文件\n', 'yellow')
    return submit_files, submit_files_md5, user_id

def Part4(collector_conf: dict, submit_files: list, submit_files_md5: list, user_id: str):
    if len(submit_files) == 0:
        console.print('没有代码可上传\n', 'red')
        sys.exit()
    console.print('开始上传代码\n')

    tarfile_path = os.path.join(collector_conf['root_path'], f'{user_id}.tar.gz')
    communicate.compress_file(tarfile_path, submit_files, collector_conf['root_path'])
    tarfile_size = os.path.getsize(tarfile_path)
    playload = (f'{user_id}\n{tarfile_size}\n' + '\n'.join(submit_files_md5)).encode()
    assert len(playload) <= 1000

    client_socket = communicate.connect_to_server((collector_conf['ip'], collector_conf['port']))
    client_socket.send(playload)
    response = client_socket.recv(1024).decode()
    if response != 'yes':
        console.print(response, 'red')
        client_socket.close()
        sys.exit()
    with open(tarfile_path, "rb") as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            client_socket.sendall(data)
    server_files_md5 = client_socket.recv(1024).decode().split('\n')
    client_socket.close()

    submit_files_md5.append(f'{user_id}.txt {utils.get_str_list_md5(submit_files_md5)}')
    max_len = max(len(submit_files_md5), len(server_files_md5))
    submit_files_md5 += ['<空行>'] * (max_len - len(submit_files_md5))
    server_files_md5 += ['<空行>'] * (max_len - len(server_files_md5))
    for i in range(max_len):
        console.print(f'本  地 {submit_files_md5[i]}\n服务器 {server_files_md5[i]}\n\n', 'green' if submit_files_md5[i] == server_files_md5[i] else 'red')

def main():
    try:
        collector_conf = Part1()
        if datetime.now() < collector_conf['start_time'] - timedelta(minutes=5):
            Part2(collector_conf)
            return
        submit_files, submit_files_md5, user_id = Part3(collector_conf)
        if datetime.now() > collector_conf['end_time'] + timedelta(minutes=5):
            Part4(collector_conf, submit_files, submit_files_md5, user_id)
    except Exception as e:
        console.print(traceback.format_exc())
        console.print("程序出现未知错误，请联系监考员\n", 'red')

if __name__ == '__main__':
    console.start('Code Collector', main)
