---
title: golang并行编程
date: 2020-05-22 22:39:40
tags:
  - golang
---

### 关于本文

本文主要阐述作者对golang并行编程设计的理解，重在讲解思路而非实际使用。读者可以通过阅读本文，来了解golang中并行设计的关键技术及其作用，知其所以然。

本文并不追求完整和严谨，重点是提供一个学习思路，理清基本概念。使用的细节仍需要参考官方文档。

由于作者没有专门研究过golang的核心实现，所以文中可能存在理解或表述不当之处，欢迎批评指正。

### 并行需求的背景

在计算机诞生之初，系统还是批处理的方式。彼时，碍于性能和基础工具的不完善，一台计算机同时只能跑一个任务。

后来出现了能在一台计算机上同时跑多个任务的多任务操作系统，*nix系统是典型代表。

但是多任务同时也只能有一个任务在运行，只是硬件性能足够高时，多任务切换快速，让人类看上去像是多个任务在并行处理。

再后来，硬件进一步升级，出现了多核CPU的技术，这时计算机真正具有了并行处理的能力。

伴随多核技术的出现的，还有相关的计算机编程语言。如何能便利地开发利用多核技术的程序，是这类编程语言要解决的核心问题之一。

golang标榜的即是该优势，它在语言层面提供了并行机制，并提供了相关语言工具，来简化多核心编程的过程。

### golang中的并行实现：goroutine

golang实现了一种轻量级的线程，即goroutine，来为用户提供并行编程的支持。

goroutine由golang的运行时管理，它使用go关键字创建，使用较为简单。

下面是一个例子：

```go
go func() {
    h1 := hash("hello")
    fmt.Printf("hello => %s\n", h1)
}()

doSomeThing()
```

如果CPU有多个核心，golang会将耗时的hash计算自动分配到单独的核心，以充分利用多核心的优势。

但是这里有一个很明显的问题，上例中我们只是把计算结果打印出来，大多时候这不是我们想要的。我们想把计算的结果返回到主进程，供后面使用。

这就涉及到多个逻辑单元间的通信问题，有这么几个类似的总是，函数间参数的传递，goroutine间的数据通信，及进程间的数据通信，其实说的是同一个问题。

当然实现手段是多样的，golang提供了一种channel技术来解决goroutine间通信的问题（关键字CSP）。

### goroutine间的通信：channel

我们先来考查一下编程语言函数中的数据通信，来更好的理解数据通信的方式。

1. 一个比较简单易得的方式是使用全局变量，在语言层面来说，这是一个可行的设计。但是当把它放到并行的场景下时，它的缺点就非常明显了，为了保证数据的一致性，需要引入锁机制或者一些其它的同步机制，这就使问题变得更为复杂。
2. 另一个可行的方式是把数据作为参数传递给具体的变量，类比于逻辑单元间的消息传递（实际上在object-c中即是把普遍意义上的函数调用定义为信号传递，本质类似，只是不同的看待方式）。这种方式的问题是，需要底层来提供支持，比如linux的管道。

下面我们再来看一下上面两种方式在golang多个goroutine间的实现：

全局变量必然是行得通的。我们使用锁机制来保证数据的一致性，下面是示例代码：

```go
package main

import (
	"fmt"
	"sync"
)

var mutex sync.RWMutex
var y int

func main() {
	mutex.Lock()
	go func() {
		y = 4
		mutex.Unlock()
	}()

	mutex.RLock()
	fmt.Println(y)
	mutex.RUnlock()
}
```

第二种方式即是golang中提供的channel工具，它的操作方式有点类似linux中的管道，数据从一端流入，另一端流出。它是一个内置的数据结构，基本使用如下：

```go
ch := make(chan int)
ch <- 3
i := <-ch
```

上面定义了具有1个元素的channel，写入元素时会阻塞当前goroutine，并等待其它goroutine读取该元素（还可以指定channel元素个数来为其添加缓存，这里不展开）。

使用channel工具来重写上面的代码会更为简洁，可读性更好。下面是重构后的代码：

```go
package main

import (
	"fmt"
)

func main() {
	y := make(chan int)
	go func() {
		y <- 4
	}()

	fmt.Println(<-y)
}
```

代码确实简洁了许多，需要注意的是，go func()中的 `y <- 4` 语句会阻塞该goroutine，直到最后 `<-y` 将数据读出后，go func()才会继续执行。

golang中有一个原则性的表述，可以看出其对使用channel来进行数据通信的倾向：

> Do not communicate by sharing memory; instead, share memory by communicating.

### goroutine协同：select

现在我们已经有了多个goroutine间通信的工具，但是这个工具是阻塞的，有时我们希望能更灵活地处理channel的状态，如指定3秒的超时时间。

goroutine提供了一个select工具来解决这类问题，这个select跟linux中的select有些类似，监控多个目标，如果监控到某个目标达到了我们期望的状态，就做某类操作。

golang中的select跟switch有着一样的结构，而且都使用case关键字来处理多分支，不同的是select处理的是channel的输入输出。

假如我们定义了两个channel，并由两个goroutine来分别写channel数据，select的处理结构类似下面这种：

```go
select {
case <-ch1:
    doSomeThing()
case <-ch2:
    doOtherThing()
default:
    allIsBlocking()
}
```

程序会检测ch1和ch2中是否有写入数据，并随机选择一个有写入数据的分支执行，注意这里是随机。如果没有，执行default分支。具体执行过程更复杂些，具体可点击文章底部的链接查看。

可以使用下面的例子来检测超时：

```go
package main

import (
	"fmt"
	"time"
)

func main() {
	blockCh := make(chan int)
	timeoutCh := make(chan int)

	go func() {
		time.Sleep(time.Second*3)  // 1
		blockCh <- 1
	}()

	go func() {
		time.Sleep(time.Second*1)  // 2
		timeoutCh <- 1
	}()

	select {
	case <-blockCh:
		fmt.Println("block routine is finished!")
	case <-timeoutCh:
		fmt.Println("block routine is timeout!")
	}
}
```

由于1处的goroutine执行太慢（3秒），程序将在等待一秒后，打印"block routine is timeout!"并退出。

case语句同时支持写入和读出，具体可以参考官方文档。

### 辅助工具

golang还为并行编程提供了更为丰富的工具，使并行编程的过程更为便利，下面列举一些比较常用的工具。这里省去了示例代码。

goroutine会在主进程退出时自动退出，如果我们想让主进程等待goroutine的运行，可以使用sync.WaitGroup()工具。

超时检测的情况比较多，time包借助运行时，实现了一个更为高效的超时检测，time.After()，另外，time.Tick()可以定期写channel配置for实现周期性任务。

### 参考资料

https://golang.org/ref/spec
https://golang.org/doc/effective_go.html