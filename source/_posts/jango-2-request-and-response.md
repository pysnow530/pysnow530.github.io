---
title: django核心处理流程 2. 请求响应逻辑
date: 2020-03-25 20:13:23
tags:
  - django
---

web 框架的设计，将每一个资源地址映射到一个处理逻辑。这篇文章将讲述 django 中对请求的解析处理，及处理结果的返回。

### 视图函数

资源地址对应的处理逻辑，在 django 中叫做视图（view）。

视图是一个可调用对象，一般为函数。

请求的上下文被打包到一个叫做 HttpRequest 的对象中，并传入视图函数。函数处理后，将结果打包到一个 HttpResponse 对象，并返回给主调方。

这里的主调方，其实就是我们的框架了。

下面是一个比较典型的视图函数：

```python
def welcome(request, nickname):
    content = f'Hello {nickname}, welcome to jango.'
    response = HttpResponse(content=content)
    return response
```

这个示例函数的结构比较清晰。需要注意的是，参数里有一个 nickname，django 会把资源地址中的匹配参数一并作为视图参数传递过来。

与该函数绑定的 url 为：

```python
[r'/welcome/(?P<nickname>\w+)', views.welcome]
```

可以看到 nickname 的来源及解析方式。

### 请求上下文

那么请求的上下文是如何构造出来的呢，下面就是构造的过程：

```python
class HttpRequest:

    def __init__(self, environ):
        self.method = environ['REQUEST_METHOD']
        self.path_info = environ['PATH_INFO']
        self.environ = environ
```

我们可以看到，HttpRequest 是通过解析一个 environ 字典生成的。environ 字典里包含了请求的上下文信息。至于 environ 从何而来，它实际上是 wsgi 接口定义。我们在下篇文章展开。

environ 里包含了所有请求相关的信息，上例中的 path_info 实际上就是我们的请求地址了，比如前面的 `'/welcome/oog'`。

HttpResponse 也会解析请求参数及 COOKIE 等，这样我们就可以很方便的获取需要的信息了。

### http 响应

请求被处理完后，视图函数需要返回一个 HttpResponse 对象。该对象包含了需要返回的信息。

一个 http 请求返回的结果，比较典型的有下面几项：

1. status code，它定义了请求被处理的结论，比如 200 表示成功，302 表示该资源需要跳转到其它资源地址等
2. body，比如一段 html 代码，或者是一个故事的文本描述
3. content type，标识 body 的类型，以方便资源请求方正确理解它。比如 text/html、text/plain 等类型

HttpResponse类的定义如下：

```python
class HttpResponse:

    def __init__(self, content, content_type='plain/text', status_code=200):
        self.content = content
        self.content_type = content_type
        self.status_code = status_code
```

### 请求、响应流程

现在我们已经有请求解析和响应对象的构造，一个请求过来是如何发生的呢？

我们先来看 8 行代码：

```python
def wsgi_application(environ, start_response):
    """标准wsgi程序"""
    request = HttpRequest(environ)
    response = handle_view(request, root_urlconf)

    status = STATUS_TO_DISPLAY[response.status_code]
    headers = []
    start_response(status, headers)

    ret = [response.content.encode('utf-8')]
    return ret
```

代码中，得到 request 后，调用函数并获取 response，然后把关键信息按需要的格式返回即可。

其中 handle_view() 是一个 10 行函数，功能是根据 url 找到视图函数并执行。具体参见 jango 的源码 <https://github.com/pysnow530/jango>。

这里的结果渲染部分初看会有点奇怪，这里其实是 wsgi 定义的规范，后面的文章会讲到。

到这里，我们就已经完成了一个 url 从请求匹配，到视图执行，最后到请求响应的完整过程。文章里讲到的 wsgi 将会在下一篇文章细说。

### 一些重要细节

我们上面看到的视图，都是一些函数的形式。如果看 django 的官方文档，会发现 django 也提供了一种类的方式，类名对应请求名。

```python
class Welcome(View):

    def get(self):
        """GET方法"""

    def post(self):
        """POST方法"""
```

但是不要被外在形式迷惑，类形式的视图本质也是一个可调用对象，只是通过 Welcome.as_view() 包装的语法糖方便使用。具体可参考 django 源码。

另外一点，http 比例子中讲到的功能要更为丰富，它还涉及了文件的上传下载等功能。具体可参考扩展资源给出的 rfc 文档。

### 扩展资料

http 协议可参考 <https://tools.ietf.org/html/rfc2616>。
