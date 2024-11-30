import os, traceback
import hashlib, json

import console, utils

SALT = 'mz9WyvqESCQkiQmz'

def calc_md5(data: dict) -> str:
    json_str = json.dumps(data, sort_keys=True) + SALT
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()

def generate(server_addr: tuple, server_conf: dict):
    playload = {key: server_conf[key] for key in ['root_path', 'regex', 'problem', 'suffix', 'use_subdirectory', 'size_limit_kb']}
    playload['start_time'] = server_conf['start_time'].strftime('%Y-%m-%dT%H:%M:%S%z') + '+08:00'
    playload['end_time'] = server_conf['start_time'].strftime('%Y-%m-%dT%H:%M:%S%z') + '+08:00'
    playload['ip'], playload['port'] = server_addr
    conf_new = json.dumps({'content': playload, 'checksum': calc_md5(playload)}, sort_keys=True, indent=4)
    
    file_dir = os.path.join(utils.app_dir, f"{server_conf['name']}下发文件", 'collector.conf.json')
    try:
        with open(file_dir, 'r') as f:
            conf_exist = f.read()
    except:
        conf_exist = ''
    if conf_new != conf_exist:
        with open(file_dir, 'w') as f:
            f.write(conf_new)
        console.print(f"{server_conf['name']}下发文件已更新，请注意下发至学生机\n", 'yellow')
