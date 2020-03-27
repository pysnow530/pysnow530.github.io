---
title: django核心处理流程 3. wsgi
date: 2020-03-26 21:28:00
tags:
  - django
  - wsgi
---

wsgi 是 python 服务器与 web 应用间交互的通用接口，实现该接口的应用可以通过任何实现了该接口的服务器部署。

### wsgi 诞生的背景

我们知道，接口可以有效地解耦调用方与被调方。

拿 cmq 举例，如果我们实现了它所规定的相关接口，就可以提供给调用方使用，而不必关心它是否是原生的 cmq。

最开始的 web 框架花样繁多，服务的部署多种多样，往往框架的选择就已经限制了服务器的选择。而 wsgi 的目标，就是将框架的选择与Web服务器的选择解耦。

### 需要做哪些工作

我们先思考一下，如何分离这两者，提供一个统一的界面接口。

首先，在我们的框架里，是不需要关心 http 细节的，这就需要把 http 的相关信息以一种通用的格式打包过来。一种比较直观的结构是一维字典，或者是一个元组列表。

拿到处理的信息后，我们可以对其进行解析，然后执行处理逻辑，返回 http 响应。

响应当然可以直接返回一个 http 协议文本，但是 web 应用不该过多参与 http 细节。这里将返回分解为了三部分，返回状态说明、响应头、响应体。

我们知道，响应头是必须先于响应体的，那么在技术上如何保证呢？

wsgi 给出一个 start_response 参数，这是一个可调用函数，以返回状态说明和响应头为参数。如此我们便可以判断其与响应体的顺序了。

另外还有一个问题，一个请求的响应体可能会分多段返回，比如我们要对一个列表的每个元素做计算，由于计算量很大，我希望每算得一个结果就返回一个结果。所以这里我希望能以 yield 的方式来做返回。

跟据上面一些问题的考量，我们就可以得到一个近似 wsgi 的接口了：

```python
def simple_app(environ, start_response):
    """Simplest possible application object"""
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    
    yield 'hello\n'
    time.sleep(3)
    yield 'world\n'
```

实际返回的 headers 跟这里的 response_headers 并不完全一致，应用只负责它关心的 header，剩下的就交给 wsgi 服务器了。

### wsgiref 模块

python 的 wsgiref 模块实现了一个简单的 wsgi 服务器，我们可以借助它来让我们前面写的一些代码变为运行时。

首先，我们把之前的逻辑包装为一个标准的 wsgi 应用：

```python
def get_wsgi_application(root_urlconf):
    """
    将ROOT_URLCONF中配置的路由，包装为一个wsgi应用
    :param root_urlconf: 字符串，根url模块位置
    :return:
    """
    def wsgi_application(environ, start_response):
        """标准wsgi程序"""
        request = HttpRequest(environ)
        response = handle_view(request, root_urlconf)

        status = STATUS_TO_DISPLAY[response.status_code]
        headers = []
        start_response(status, headers)

        ret = [response.content.encode('utf-8')]
        return ret

    return wsgi_application
```

然后，我们将该应用传递给 wsgi 服务器，让它把这个应用运行起来：

```python
wsgi_application = get_wsgi_application(settings.ROOT_URLCONF)

with make_server(host, port, wsgi_application) as httpd:
    print(f"Serving on port http://{host}:{port}...")
    httpd.serve_forever()
```

此时，我们访问 http://127.0.0.1:5302/welcome/oog 就可以看到下面的提示了：

```text
Hello oog, welcome to jango.
```

### 发挥 wsgi 的优势

我们前面说，wsgi 可以解耦应用和服务器，也就是说，我们的应用同样可以部署在其它 wsgi 服务器下。

这里我们尝试使用 gunicorn 来验证该服务是否可以在其它 wsgi 服务器下正常运行。

首先我们创建一个脚本来生成一个 wsgi 接口的函数：

```python
# demo/wsgi.py
settings = importlib.import_module('demo.settings')
application = get_wsgi_application(settings.ROOT_URLCONF)
```

然后，我们在命令行启动 gunicorn，并将该 application 传递给它：

```shell script
gunicorn -b 127.0.0.1:5302 -w 4 demo.wsgi:application
```

这里我们借助 gunicorn 的支持，启动了 4 个 worker，一切运行正常。wsgi 做得很好。

到这里，我们就已经成功把静态代码部署为一个服务器了。相关代码可以在 <https://github.com/pysnow530/jango> 找到。

虽然这里只有一些核心逻辑，但是已经看到了一些 django 的脉络。

当然，django 的能力不止于此，它实际上是一个框架的框架，中间件、灵活的配置系统、第三方模块，使得它可以在系统层面做进一步的抽象。它的思想远不及此，不过这些已超出本文的范围，就此打住了。

这只是旅途的一个开始，想要的答案，让我们去 django 的源码里找吧。

### 一些重要细节

上面的响应体使用了 yield 和 list 两种返回形式，本质上所有的可迭代对象都可以作为响应体返回使用。

同样的，这里所说的函数，也可以替换为其它可执行对象，包括实现了 `__call__` 方法的类。

### 扩展资料

wsgi 协议可参考

* v1.0 <https://www.python.org/dev/peps/pep-0333/>
* v1.0.1 <https://www.python.org/dev/peps/pep-3333/>。
