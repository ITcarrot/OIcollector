pyinstaller -w --onefile collector.py
pyinstaller -w --onefile server.py
pyinstaller -w --onefile --uac-admin validator.py
cp .\build\validator\validator.exe.manifest ./
pyinstaller -w --onefile --uac-admin -r validator.exe.manifest,1 validator.py
