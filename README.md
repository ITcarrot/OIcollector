# OIcollector

为信息学竞赛（OI）设计的局域网工具。不止可以收集选手代码，还可以代监考员执行部分系统检测、清理、校对工作。

## Build
```bash
set CONDA_FORCE_32BIT=1
conda env create -f environment.yml
./build.ps1
```
生成的可执行文件位于 dist/ 目录下
