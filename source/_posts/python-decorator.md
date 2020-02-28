---
title: Python中的装饰器
date: 2016-05-26
tags: 设计模式
---

> 本文主要讲解python中decorator的历史，然后说明decorator在python中的实现，以帮助初识decorator的pythoner能够灵活运用decorator。

### 装饰器模式

装饰器模式来自GoF的23种设计模式。

在设计模式中，装饰器模式的意图描述如下：

> [Attach additional responsibilities to an object dynamically. Decorators provide a flexible alternative to subclassing for extending functionality.](http://c2.com/cgi/wiki?DecoratorPattern)

即将附加的职责动态添加到一个对象。在扩展功能时，它比子类继承的方式要来得灵活。它是面向切面编程的一种手段。

### python中的装饰器

#### 提出

在python中，decorator最早是在[PEP 318 -- Decorators for Functions and Methods](https://www.python.org/dev/peps/pep-0318/)被提出的。

#### 具体实现

decorator在python中形如@decorator，如：

    @log
    def foo():
        ...

我们将通过观察字节码，看一看添加decorator在字节码层带来了哪些变化。

首先来看函数定义产生的字节码：

    def foo():
        pass
    
    0 LOAD_CONST               0 (<code object foo at 0xb72508d8, file "<stdin>", line 1>)
    3 MAKE_FUNCTION            0
    6 STORE_NAME               0 (foo)

`foo`函数的定义对应三条字节码。

`LOAD_CONST`指令将`pass`对应的代码对象压入堆栈。

`MAKE_FUNCTION`将代码对象弹出堆栈，并创建一个PyFunctionObject对象，然后将函数压入堆栈。

`STORE_NAME`将函数弹出栈，并将它绑定到`foo`变量。

此时，`foo`变量即是一个函数。

然后我们看一下加了装饰器的函数定义对应的字节码：

    @log
    def foo():
        pass
        
     0 LOAD_NAME                0 (log) <---------- 1
     3 LOAD_CONST               0 (<code object foo at 0xb720e8d8, file "<stdin>", line 1>)
     6 MAKE_FUNCTION            0
     9 CALL_FUNCTION            1       < --------- 2
    12 STORE_NAME               1 (foo)
    
给`foo`函数添加一个装饰器时，对应的字节码多个两条。上面使用1、2标出。

`LOAD_NAME`命令是新增命令，将`log`函数（装饰器函数）压入堆栈。

`LOAD_CONST`命令将`foo`下的代码对象压入栈项。

`MAKE_FUNCTION`命令将代码对象弹出栈，并创建一个PyFunctionObject对象，并压入堆栈。

`CALL_FUNCTION`命令是新增命令，调用最开始压入堆栈的装饰器函数，然后将函数的返回值压入堆栈。

`STORE_NAME`将栈项装饰器函数的返回值绑定到`foo`变量。
    
也就是说，装饰器是一个函数，它将被装饰的函数作为输入，并将输出绑定到被装饰的函数名上。而装饰器的使用本质上就是一个语法糖。

#### 煮个粟子

知道了它的内部实现，我们就可以动手了。

例如，实现一个打印函数耗时的装饰器：

    import time
    
    def log(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            func(*args, **kwargs)
            end = time.time()
            waste_time = end - start
            print 'waste time:', waste_time
        return wrapper
    
    @log
    def hello():
        print 'hello, world'
    
    hello()
    hello, world
    waste time: 4.29153442383e-05


