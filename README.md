# OIcollector

为信息学竞赛（OI）设计的局域网工具。不止可以收集选手代码，还可以代监考员执行部分系统检测、清理、校对工作。

## Build
```bash
set CONDA_FORCE_32BIT=1
conda env create -f environment.yml
./build.ps1
```
生成的可执行文件位于 dist/ 目录下

## Usage
写在前面：使用程序遇到按y确认时，务必关闭中文输入法

### 下发题目前
1. 在教师机运行server.exe，获取教师机IP
  - 服务器运行的IP和端口将会保存在和server.exe相同目录下的server_addr.txt
  - 如果教师机只有一个网卡，则可以自动确定服务器IP
  - 如果教师机有多个网卡，将会提示获取IP失败。需要自行将server_addr.txt的0.0.0.0改为教师机在教室局域网的IP
2. 将validator.exe和上一步生成的server_addr.txt下发至学生机的**C盘**
3. 在教师机启动server.exe，校对好教师机时间后，按y继续直到显示`服务器将监听：xxx.xxx.xxx.xxx:xx`
4. 使用极域在学生机批量运行validator.exe
  - 应用程序：`cmd.exe`
  - 参数：`/C "Path\To\validator.exe"`
4. 正常情况下，程序会自动运行至`即将进行电脑格式化...`
5. 在每一台电脑上按y确认进行格式化
6. 程序会显示将要格式化的分区，再按y确认
7. 程序输出`格式化结束，请自行检查格式化效果`时即为结束
8. 程序结束时，如果输出左侧只有绿色提示，即为完成：
  - 检查电脑时间是否正确
  - 模拟使用本套件收集代码，代码修改时间不变
  - **列出的磁盘**都已清空，但是程序只会尽力但**不保证**能检测到所有分区
