import traceback, os, sys
import socket, psutil
import json
from dateutil import parser

import console, server_addr_conf

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
        exit()

def load_server_conf() -> dict:
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(__file__)
    file_path = os.path.join(app_dir, 'server.conf.json')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['start_time'] = parser.isoparse(data['start_time'])
    data['end_time'] = parser.isoparse(data['end_time'])

    return data

def main():
    try:
        server_addr = Part1()
        console.print(f'服务器将监听: {server_addr[0]}:{server_addr[1]}\n', 'green')
        try:
            server_conf = load_server_conf()
            print(server_conf)
            print(server_conf['root_path'])
            print(server_conf['regex'])
        except Exception as e:
            console.print(traceback.format_exc())
            console.print('加载服务器配置文件失败，即将进入系统校验模式\n')
            console.wait_y()
            quit()
    except Exception as e:
        console.print(traceback.format_exc())
        console.print("程序出现未知错误，请联系考点负责人\n", 'red')

if __name__ == '__main__':
    console.start('Code Collector Server', main)
