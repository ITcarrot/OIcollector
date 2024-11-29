import traceback, os, sys, time
from datetime import datetime

import console, utils
import server_addr_conf
import communicate

def main():
    try:
        # Step 1
        server_addr = server_addr_conf.read()
        client_socket = communicate.connect_to_server(server_addr)
        # Step 2
        client_id, server_time = client_socket.recv(1024).decode().split('\n')
        console.print(f"获得客户端编号: {client_id}, 服务器时间: {server_time}\n")
        # Step 3
        system_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"本机时间: {system_time}\n")
        time_diff = abs((datetime.strptime(system_time, "%Y-%m-%d %H:%M:%S") - datetime.strptime(server_time, "%Y-%m-%d %H:%M:%S")).total_seconds())
        if time_diff > 30:
            console.print("本机和服务器时间相差过大！\n", 'red')
            client_socket.close()
            sys.exit()
        else:
            console.print("时间误差在容许范围内\n", 'green')
        # Step 4
        test_dir = os.path.join(utils.app_dir, f'GD-{client_id}', 'test')
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, 'test.cpp')
        with open(test_file, 'w') as f:
            f.write(f"没有彩蛋")
        # Step 5
        file_mtime = utils.get_file_mtime(test_file)
        file_md5 = utils.get_file_md5(test_file)
        tarfile_path = os.path.join(utils.app_dir, f'GD-{client_id}.tar.gz')
        time.sleep(2)
        communicate.compress_file(tarfile_path, [test_file])
        # Step 6
        tarfile_size = os.path.getsize(tarfile_path)
        client_socket.send(f"{tarfile_size}\n{file_mtime}".encode())
        # Step 7
        with open(tarfile_path, "rb") as f:
            client_socket.sendfile(f)
        # Step 8
        server_file_mtime, server_file_md5 = client_socket.recv(1024).decode().split('\n')
        client_socket.close()
        os.remove(tarfile_path)
        os.remove(test_file)
        os.rmdir(test_dir)
        os.rmdir(os.path.join(utils.app_dir, f'GD-{client_id}'))

        console.print(f'本机的文件修改时间 {file_mtime}\n')
        console.print(f'服务器文件修改时间 {server_file_mtime}\n')
        if file_mtime != server_file_mtime:
            console.print("文件修改时间发送变化！\n", 'red')
            sys.exit()
        else:
            console.print("文件修改时间没有变化\n", 'green')
        console.print(f'本机的文件md5 {file_md5}\n')
        console.print(f'服务器文件md5 {server_file_md5}\n')
        if file_md5 != server_file_md5:
            console.print("文件md5发送变化！\n", 'red')
            sys.exit()
        else:
            console.print("文件md5没有变化\n", 'green')

    except Exception as e:
        console.print(traceback.format_exc())
        console.print("程序出现未知错误，请联系考点负责人\n", 'red')

if __name__ == '__main__':
    console.start('System Validator', main)
