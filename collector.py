import traceback, sys, os
from datetime import datetime, timedelta

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

def main():
    try:
        collector_conf = Part1()
        if datetime.now() < collector_conf['start_time'] - timedelta(minutes=5):
            Part2(collector_conf)
    except Exception as e:
        console.print(traceback.format_exc())
        console.print("程序出现未知错误，请联系监考员\n", 'red')

if __name__ == '__main__':
    console.start('Code Collector', main)
