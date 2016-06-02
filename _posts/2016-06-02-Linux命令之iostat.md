## Linux命令之iostat

> iostat来自sysstat工具包，可以查看CPU和系统磁盘IO的统计信息。本文主要介绍iostat的主要命令参数和输出的部分解释。意在帮助不熟悉的用户入境，高级用户可以直接查看man page。

### 用法

    iostat [ options ] [ <interval> [ <count> ] ]

* `opions` 选项
* `interval` 每隔多少秒统计一次
* `count` 连续统计多少次

**注意**：如果没有提供`interval`和`count`选项，则系统只统计一次。统计结果是上次统计（如果没有统计过，则是系统启动时间）到本次统计的数据。

### 输出

执行`iostat`的输出如下：

    Linux 3.16.0-4-586 (oogway) 	06/02/2016 	_i686_	(1 CPU)
    
    avg-cpu:  %user   %nice %system %iowait  %steal   %idle
               2.19    0.00    0.39    0.18    0.00   97.24
    
    Device:            tps    kB_read/s    kB_wrtn/s    kB_read    kB_wrtn
    sda               1.74        24.40         3.32     222286      30252

#### 第一行：系统信息

系统信息的输出和`uname -a`的输出类似。

* `Linux` 内核名称
* `3.16.0-4-586` 内核发行版本
* `oogway` 主机名
* `06/02/2016` 当天日期
* `_i686_` 机器硬件名
* `1 CPU` CPU个数

#### 第二行：CPU利用率

CPU利用率的信息和`top`里的CPUT信息类似。

* `%user` 没有修改nice的任务的用户态时间占比
* `%nice` 修改过nice的任务的用户态时间占比
* `%system` 系统态时间占比
* `%iowait` 等待IO的时间占比
* `%steal` 虚拟cpu等待supervisor的时间占比
* `%idle` 空闲时间占比

#### 第四行：设备的读写信息

* `tps` 每秒读写请求次数
* `kB_read/s` 读取速度
* `kB_wrtn/s` 写入速度
* `kB_read` 读取量
* `kB_wrtn` 写入量

### 常用参数

#### 统计次数及频率

如果我们希望每一秒统计一次数据，连续统计10次，可以`iostat 1 10`。

#### 查看扩展统计信息

可以使用`-x`参数查看扩展的统计信息。

如`iostat -x`输出如下：

    Linux 3.16.0-4-586 (oogway) 	06/02/2016 	_i686_	(1 CPU)
    
    avg-cpu:  %user   %nice %system %iowait  %steal   %idle
               2.65    0.00    0.39    0.18    0.00   96.79
    
    Device:         rrqm/s   wrqm/s     r/s     w/s    rkB/s    wkB/s avgrq-sz avgqu-sz   await r_await w_await  svctm  %util
    sda               0.56     0.37    1.21    0.30    20.00     3.66    31.28     0.01    3.79    2.85    7.63   1.74   0.26

统计信息多了的这几项分别是：

* `rrqm/s` 每秒读请求合并数
* `wrqm/s` 每秒写请求合并数
* `r/s` 每秒完成的读请求数
* `w/s` 每秒完成的写请求数
* `rkB/s` 读取速率，同`kB_read/s`
* `wkB/s` 写入速率，同`kB_write/s`
* `avgrq-sz` 请求的平均扇区数
* `avgqu-sz` 请求的平均队列长度
* `await` IO请求的平均耗时
* `r_await` 读请求的平均耗时（ms）
* `w_await` 写请求的平均耗时（ms）
* `svctm` IO请求的平均服务耗时（该指标在未来将被移除）
* `%util` IO请求发生时CPU时间占比。当达到100%时，说明系统IO已饱和
