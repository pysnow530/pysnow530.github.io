---
title: 更换ssh证书导致paramiko报No session existing错误
date: 2018-09-17
tags:
  - paramiko
  - 证书
---

## 问题出现

现在公司的发布系统使用了paramiko来执行远程操作，ssh连接用的证书被记录在配置文件里，是一个列表的形式。没错，我们的证书有很多，用来连接到不同的环境。

接到运维通知，由于安全原因，访问某台机器使用的证书做了更换。

随后没多久，就收到测试同学的反馈，发布代码时系统提示“No existing session”。

## 简单问题简单解决

这个问题乍看上去只要更新一下配置就可以了，简单的一批。

修改配置文件，重启系统，又重试了一次。结果，还是报这个错误。疯狂了疯狂了，配置也生效了，竟然还是不能连接吗？

## 问题初探

连接的代码很简单，就是单纯的连接远程机器。

```python
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, SSH_PORT, SSH_USER, SSH_PASSWORD, key_filename=SSH_KEYS)

# ...

client.close()
```

通过测试，发现用命令行连接远程机器是可以的，而且也没有使用ProxyCommand之类，但是通过paramiko就出问题。毫无疑问，问题出在paramiko或者配置上。

session关键字让这个问题看起来像是paramiko的锅，它没处理好自己的会话吗？

一番google，发现了这个链接：<https://stackoverflow.com/questions/6832248/paramiko-no-existing-session-exception>。这个哥们也是遇到了一样的错误提示，但是他用了密码而系统查找私钥导致出错，关掉密钥查找就解决了这个问题。

看来问题出在密钥的配置上。

## 开启paramiko日志

发布系统使用的是paramiko 2.1.2，在paramiko的源码里找到了打开日志的方法。

paramiko/util.py:238

```python
def log_to_file(filename, level=DEBUG):
```

通过该函数，可以将paramiko的日志打印到某个文件，比如`paramiko.util.log('/tmp/paramiko-debug.log')`。打印的日志如下所示：

```
.transport: starting thread (client mode): 0x8ab46350L
.transport: Local version/idstring: SSH-2.0-paramiko_2.1.2
.transport: Remote version/idstring: SSH-2.0-OpenSSH_5.3
.transport: Connected (version 2.0, client OpenSSH_5.3)
.transport: kex algos:[u'diffie-hellman-group-exchange-sha256', u'diffie-hellman-group-exchange-sha1', u'diffie-hellman-group14-sha1', u'diffie-hellman-group1-sha1'] server key:[
.transport: Kex agreed: diffie-hellman-group1-sha1
.transport: Cipher agreed: aes128-ctr
.transport: MAC agreed: hmac-sha2-256
.transport: Compression agreed: none
.transport: kex engine KexGroup1 specified hash_algo <built-in function openssl_sha1>
.transport: Switch to new keys ...
.transport: Adding ssh-rsa host key for [10.0.2.243]:36000: 2e3faf53075afccf09a3ac2q391dd5e8
.transport: Trying key 3a96e7e9e3f59963fbee693f44x8cf58 from /home/user/.ssh/id_rsa1
.transport: userauth is OK
.transport: Authentication (publickey) failed.
.transport: Trying key 8628c2021979e0e0302aac6bc8xcbcef from /home/user/.ssh/id_rsa2
.transport: userauth is OK
.transport: Authentication (publickey) failed.
.transport: Trying key 6e399bc162a737150e1bd643abx7737d from /home/user/.ssh/id_rsa3
.transport: userauth is OK
.transport: Authentication (publickey) failed.
.transport: Trying key 77d22314df154bfd5ca591bd16x19363 from /home/user/.ssh/id_rsa4
.transport: userauth is OK
.transport: Authentication (publickey) failed.
.transport: Trying key 77d22314df154bfd5ca591bd16x19363 from /home/user/.ssh/id_rsa5
.transport: userauth is OK
.transport: Authentication (publickey) failed.
.transport: Trying key c1909f00bf62c74eed5a3a9e5dxa73d1 from /home/user/.ssh/id_rsa6
.transport: userauth is OK
.transport: Disconnect (code 2): Too many authentication failures for user
.transport: Trying key c897a8e51a0d41facf7fa712a2xeace8 from /home/user/.ssh/id_rsa7
.transport: Trying discovered key 3a96e7e9e3f5996xfbee693f44b8cf58 in /home/user/.ssh/id_rsa1
```

我们几乎可以一眼看到最后的错误提示：“Disconnect (code 2): Too many authentication failures for user”。看起来像是失败次数过多被拒了。google后得到了这个链接：<https://superuser.com/questions/187779/too-many-authentication-failures-for-username>。“This is usually caused by inadvertently offering multiple ssh keys to the server.”，答主建议明确指定使用哪个证书来访问服务器。

我down了一份`OpenSSH_7.8`的源码下来，经过一番grep，找到了下面这几个代码片段。

ssh/auth.c:281

```c
void
auth_maxtries_exceeded(Authctxt *authctxt)
{
        struct ssh *ssh = active_state; /* XXX */

        error("maximum authentication attempts exceeded for "
            "%s%.100s from %.200s port %d ssh2",
            authctxt->valid ? "" : "invalid user ",
            authctxt->user,
            ssh_remote_ipaddr(ssh),
            ssh_remote_port(ssh));
        packet_disconnect("Too many authentication failures");
        /* NOTREACHED */
}
```

ssh/auth2.c:322

```c
void
userauth_finish(struct ssh *ssh, int authenticated, const char *method,
    const char *submethod)
{
    // ...
    if (authenticated == 1) {
        /* turn off userauth */
        // ...
    } else {
        /* Allow initial try of "none" auth without failure penalty */
        if (!partial && !authctxt->server_caused_failure &&
                (authctxt->attempt > 1 || strcmp(method, "none") != 0))
            authctxt->failures++;
        if (authctxt->failures >= options.max_authtries)
            auth_maxtries_exceeded(authctxt);
        // ...
    }
}
```

ssh/srvconf.h:39

```c
#define DEFAULT_AUTH_FAIL_MAX   6       /* Default for MaxAuthTries */
```

原来ssh默认允许尝试6个密钥，如果还没有成功，就会直接退出了。这么做的原因想来也显而易见了。

## 解决办法

我的临时解决办法是，将密钥文件的配置控制在6个以内。当然，更好点的办法是使用fabric来替代直接使用paramiko，并复用系统的`.ssh/config`配置，这就是后面需要考虑的了。
