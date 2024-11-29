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

def get_file_md5(file_path):
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()
