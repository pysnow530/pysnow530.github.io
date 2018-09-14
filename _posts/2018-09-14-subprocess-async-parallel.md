---
layout: post
title: 使用subprocess模块异步并发执行远程命令
categories: 编程
tags: python
---

## 远程执行命令

运维自动化平台不可避免地会涉及到远程命令执行操作，主要分为两类主要做法：目标机器安装agent，或者使用ssh。

saltstack是一个典型的agent模式的远程控制工具，麻烦的地方是首先要在目标机器上安装saltstack的agent。

使用ssh的模块居多，fabric和ansible是此类工具中的典型，这类工具的优点是方便，不用在目标机安装agent。值得一提的是，这两个工具都是基于paramiko。

使用ssh执行的另一种做法是，直接调用本地的ssh来完成。缺点是针对每一台远程主机都需要开一个进程，比起在程序内建立连接要耗费更多的资源。优点也很明显，比如，公司最近在做ssh的改造，在改造的过程中，可能会出现明明ssh命令可以连接，使用第三方模块就是不灵的情况。ssh的命令和第三方模块在配置上毕竟有差异，需要维护两份配置。

这篇文章就是要使用进程来完成在批量远程机器上执行某个命令。

## subprocess模块大概

subprocess模块是python2中的一个官方模块，顾名思义，它主要用于操作子进程。

subprocess.Popen()用于创建一个子进程，它的第一个参数是列表，即创建进程所需要的参数，类似c语言中的argv。

需要注意的一点是，Popen是异步执行的，也就是说创建Popen后会立刻返回，子进程继续执行。关于异步，还有很多可以聊的地方，后面另开一篇文章写一下。

既然是异步的，我们就需要某种机制来跟它进行通信。Popen提供了多个方式来与子进程通信。

Popen.wait()将主程序挂起等待子进程的结束，结束后会返回子进程的返回码。

Popen.poll()可以检测子进程是否还在执行，并返回子进程的返回码。

下面我们将用几个小例子来不断扩展，最终实现一个可在多台远程机器并行执行命令的功能。

## 一个简单的远程执行示例

我们来写一个简单的示例，说明如何使用subprocess模块远程执行一条命令。

```python
import subprocess


cmd = 'echo hello'
cmd_arg = ['ssh', 'localhost', cmd]

process = subprocess.Popen(
    cmd_arg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
retcode = process.wait()            # 0
out = process.stdout.read()         # 'hello'
err = process.stderr.read()         # ''
```

我们首先创建了一个Popen对象，然后等待这个子进程的执行结束，获取返回值和输出。

这断代码很简单，注意stdout=subprocess.PIPE，我们想捕捉到子进程的输出，而不是直接打印到标准标出，所以要求Popen把输出打印到管道供我们读取。

## 同时在多个机器上执行命令

这里我们利用了Popen的异步特性，来加快多服务器任务的执行。

```python
import subprocess


cmd = 'sleep 3 && echo hello'
cmd_arg1 = ['ssh', 'localhost', cmd]
cmd_arg2 = ['ssh', '127.0.0.1', cmd]

process1 = subprocess.Popen(
    cmd_arg1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
process2 = subprocess.Popen(
    cmd_arg2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

retcode1 = process1.wait()
retcode2 = process1.wait()
```

这次，我们连接了两个机器并执行耗时3s的操作，由于Popen是异步的，这个脚本的实际执行时间仍然是3s。这个地方的操作是不是与多线程的操作有点类似，哈哈。

## 多个机器执行获取执行时间

由于网络环境和机器配置的不同，我们在不同机器的执行时间是有差别的。有时候，我们需要一个时间数据来了解哪个机器执行耗时比较久，以此做优化。

这时，我们需要Popen.poll()来异步检测命令是否执行完成，而不是将主进程挂起等待第一个子进程。如果第一个子进程执行时间比第二个子进程要长，我们就获取不到第二个子进程的执行时间。

为了更好的可读性，这里我们没有加入for循环之类的结束，放弃了部分逻辑上的灵活性。

```python
import time
import subprocess


cmd = 'sleep 3 && echo hello'
cmd_arg1 = ['ssh', 'localhost', cmd]
cmd_arg2 = ['ssh', '127.0.0.1', cmd]

process1 = subprocess.Popen(
    cmd_arg1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
process2 = subprocess.Popen(
    cmd_arg2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

process1_ok = False
process2_ok = False

start_time = time.time()
while True:
    if process1_ok and process2_ok:
        break

    if not process1_ok:
        if process1.poll() is not None:
            process1_ok = True
            print 'process 1 finished, delta time:', time.time() - start_time

    if not process2_ok:
        if process2.poll() is not None:
            process2_ok = True
            print 'process 2 finished, delta time:', time.time() - start_time

    time.sleep(1)       # 防止空跑导致cpu占用过高
```

执行输出为：

```
process 1 finished, delta time: 4.01682209969
process 2 finished, delta time: 4.01691508293
```

最后的执行时间多了1s，这是因为我们做了一个time.sleep(1)操作。由于我们考查的是哪台机器影响了整体的耗时，而且远程任务执行时间远不止1s，所以这里的1s不影响我们的判断。当然，适当缩小time.sleep()的参数也是可以的。

## 封闭一个可并行在多台服务器执行的函数

我们将上面的脚本封闭一下，形成一个可以复用的函数。有点长，但是只是在之前基础上做了一些简单的操作，并没有增加什么高深的东西。

```python
def run(hostname, command, user=None):
    """
    使用ssh执行远程命令

    hostname    字符串或数组，多个hostname使用数组
    """
    if not isinstance(hostname, list):
        hostname = [hostname]
    else:
        hostname = list(set(hostname))

    # 创建执行命令子进程
    processes = {}
    for h in hostname:
        if user is None:
            user_at_hostname = h
        else:
            user_at_hostname = '{0}@{1}'.format(user, h)

        cmd_args = ['ssh', user_at_hostname, command]
        processes[h] = subprocess.Popen(
            cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 等待子进程结束，获取结果
    start_time = time.time()
    result = {}
    while True:
        running_hostnames = set(processes.keys()) - set(result.keys())
        if len(running_hostnames) == 0:
            break

        for h in running_hostnames:
            process = processes[h]
            retcode = process.poll()

            if retcode is None:
                continue

            status = STATUS_SUCC if retcode == 0 else STATUS_FAIL
            out, err = process.stdout.read(), process.stderr.read()
            delta_time = time.time() - start_time

            result[h] = {
                'out': out,
                'err': err,
                'status': status,
                'delta_time': delta_time
            }

        time.sleep(1)

    r = {
        'ts': time.time(),
        'cmd': command,
        'result': result,
    }

    return r
```
