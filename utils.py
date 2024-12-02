import sys, os
from datetime import datetime
import hashlib

if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(__file__)

def get_file_mtime(file_path) -> str:
    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

def get_file_md5(file_path) -> str:
    try:
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        ret = md5_hash.hexdigest()
    except Exception as e:
        ret = str(e)
    return ret

def get_str_list_md5(str_list: list) -> str:
    return hashlib.md5('\n'.join(str_list).encode()).hexdigest()
