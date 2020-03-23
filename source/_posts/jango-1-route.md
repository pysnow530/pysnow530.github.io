---
title: django核心处理流程 1. 路由
date: 2020-03-22 18:00:45
tags:
  - django
  - url
---

> 路由的设计是每一个 web 框架都必须优先考虑的问题，它决定了资源地址在代码中的组织方式。

### 数据结构

从本质上讲，路由表维护了 url 地址到业务逻辑代码的映射关系。

在 django 中，为了使 url 规则更为灵活，采用了正则表达式的方式来匹配 url 地址。

正则表达式是一种模糊匹配，同一个 url 可能会对应多个正则表达式。所以 django 中的路由是一个列表配置。列表中的每一项是一个 `(pattern, view)` 对。

为了便于模块化，django 还提供了第二种配置项 `(pattern, conf_module)`，用于将一组 url 映射到某个前缀下。所以整个路由设计的结构上是一棵树。

下面是一个例子：

```python
# urls.py
urlpatterns = [
    ['/welcome', views.welcome],
    ['/api/suburls', 'suburls'],  # 以/api/suburls作为url前缀，suburls模块中的其它项作为剩余部分
]

# suburls.py
urlpatterns = [
    ['/url1', views.url1],   # 实际访问地址为/api/suburls/url1
    ['/url2', views.url2],   # 实际访问地址为/api/suburls/url2
]
```

假如 suburls 是一个成熟的模块，我们就可以使用这种方式给该模块分配一个前缀，如此就可以投入使用了。

下面是一个很经典的例子，将 django 内置的后台管理模块配置到 `/admin` 下：

```python
urlpatterns = [
    path('admin/', admin.site.urls),
]
```

### 查找算法

上面提到，django 中的路由实质上是一棵树的结构，所以查找上也是树的遍历算法。由于我们想借助列表结构来说明优先级，这里必然要使用深度遍历。

我们首先会从 settings 配置找到根 url 模块，然后遍历模块中的 urlpatterns 列表，如果匹配到的是一个模块，就继续匹配模块中的列表。如果最后没有找到可执行的逻辑，就是我们常见的 404 了。

```python
# demo/settings.py
ROOT_URLCONF = 'demo.urls'

# jango/url.py
def resolve(path_info, urlconf):
    """匹配请求url，返回匹配项"""
    urlconf_module = import_module(urlconf)
    urlpatterns = urlconf_module.urlpatterns

    for pattern in urlpatterns:
        regex = pattern[0]
        re_matched = re.match(regex, path_info)

        # ['hello/', view]
        if re_matched and callable(pattern[1]):
            callback = pattern[1]
            callback_kwargs = re_matched.groupdict()
            groups = re_matched.groups()
            callback_args = groups[:len(groups) - len(callback_kwargs)]
            return callback, callback_args, callback_kwargs

        # ['api/', 'demo.urls']
        elif re_matched and isinstance(pattern[1], str):
            resolve_match = resolve(path_info[re_matched.end():], pattern[1])
            if resolve_match:
                return resolve_match

    return None
```

其中，参数 `path_info` 是需要解析的url。解析后，我们可以获取执行的函数，及前端传过来的 url 参数。后面就可以调用具体函数执行了。

代码地址可参考 <https://github.com/pysnow530/jango>。

### 一些重要细节

当然，上面的模型只是一个简化，这里提一下原生 django 几个比较重要的细节。

第一，我们说匹配规则是一个正则表达式，但是 django 已对正则表达式做了封装，提供了更简单直白的用法，比如 `/welcome/<name>`。更多的限制，必然是一种发展趋势，它让我们更好的关心逻辑代码而非技术。

第二，为减少封装了解本质，我们把路由中的每一个配置项定义为一个列表，实际 django 中是以一个类来替换的，作用类似，只是抽象程度更高。

第三，django 支持给路由配置项命名，并在需要时支持将名称反转为 url。如在模板中的 `{% url 'api_welcome' 'name' %}` 或代码中使用 `reverse('api_welcome', args=('name',))`，这让修改 url 几乎零成本，是一个优秀的设计。

说了这么多，路由的核心简单且简洁，就是一个映射表。通过它，我们能找到资源地址对应的逻辑代码。

下一篇文章，我们来看一下逻辑代码是如何组织及工作的。
