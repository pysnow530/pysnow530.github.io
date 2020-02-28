---
title: celery使用fabric出现大量ssh -W进程
date: 2018-09-13
tags: python
---

公司的运维平台有很大一部分是python写的。

发布系统不可避免的要与远程机器做交互，我们选择了基于paramiko的fabric模块来完成这部分工作。

由于发布过程中存在大量耗时很久的任务，所以选用了celery来执行异步任务。有一部分远程操作是通过celery的任务调用fabric来完成的。

## 出现大量ssh -W

在某一天，突然接到运维同学的反馈，说生产环境存在大量ssh -W进程，希望可以查一下出现的原因。

通过定位，很快确认了是ssh连接远程时使用了ProxyCommand，导致出现了ssh -W进程，这些进程实际上是ssh连接到远端的代理。

但是奇怪的是，为什么任务执行完后仍然存在大量ssh -W不能正常退出。

后来通过阅读fabric的源代码，在代码里找到了答案。

fabric/state.py

```python
#
# Host connection dict/cache
#

connections = HostConnectionCache()
```

fabric/network.py

```python
class HostConnectionCache(dict):
    """
    ...
    """
    def connect(self, key):
        """
        Force a new connection to ``key`` host string.
        """
        from fabric.state import env

        user, host, port = normalize(key)
        key = normalize_to_string(key)
        seek_gateway = True
        # break the loop when the host is gateway itself
        if env.gateway:
            seek_gateway = normalize_to_string(env.gateway) != key
        self[key] = connect(
            user, host, port, cache=self, seek_gateway=seek_gateway)

    def __getitem__(self, key):
        """
        Autoconnect + return connection object
        """
        key = normalize_to_string(key)
        if key not in self:
            self.connect(key)
        return dict.__getitem__(self, key)


# ...


def disconnect_all():
    """
    Disconnect from all currently connected servers.

    Used at the end of ``fab``'s main loop, and also intended for use by
    library users.
    """
    from fabric.state import connections, output
    # Explicitly disconnect from all servers
    for key in connections.keys():
        if output.status:
            # Here we can't use the py3k print(x, end=" ")
            # because 2.5 backwards compatibility
            sys.stdout.write("Disconnecting from %s... " % denormalize(key))
        connections[key].close()
        del connections[key]
        if output.status:
            sys.stdout.write("done.\n")
```

原来，fabric默认会维护一个连接缓存，并且不会主动断开这些连接，直到脚本结束垃圾回收时自己断开。但是由于使用了celery，celery是常驻进程不会退出，导致fabric不能自己主动释放连接，所以连接一直在，ssh -W也一直在。

知道原因，就很好解决了。可以主动调用network.disconnect_all()来释放连接，或者干脆就保持着连接，以待下次使用。

需要注意的是，HostConnectionCache是一个全局变量，在celery这类常驻进程中使用还是存在一些坑的。

## cpu飙升到100%

知道原因后，我做了一个kill操作，手动将ssh -W杀死了。这时候，再次向之前的目标机发送命令时，ssh应该会报错，因为代理被干掉了。

意料之中，系统再次执行命令时果然提示“broken pipe”。

但是，奇怪的是，运行celery的机器，cpu占用率达到了100%。这就有点奇怪了。

查找原因无果，在github上提交了一个issue <https://github.com/paramiko/paramiko/issues/1277>。ploxiln提供了另一个关联issue，表明这是paramiko库的一个bug，通过链接可以查找到patch文件。

到此，问题都已解决。
