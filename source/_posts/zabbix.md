---
title: zabbix监控方案
date: 2020-05-29 21:14:51
tags:
  - zabbix
  - 监控告警
---

### 概况

zabbix是一个老牌的开源分布式监控方案，它是由Alexei Vladishev在2000年左右创建（PS: 那时我刚好升初中 😀），最早主要用来监控网络和服务器的健康度和完整性。

如果按照中国的法律，到现在的2020年，zabbix已经成年。

经过近20年的发展，zabbix已由最初的网络和服务器监控扩展到应用监控和web监控等更丰富的监控目标，数据库支持已从mysql覆盖到了elasticsearch、oracle等更多的第三方数据库，告警函数也从最初的6个增加到了5.0版本的29个。

### 架构

zabbix的架构比较典型，分为采集端、展示端、告警端。采集端主要通过agent采集信息，并上报到server，数据存储在mysql等数据库中。

下面是zabbix数据采集端接入zabbix的架构图：

![zabbix-proxy](/images/zabbix-proxy.png)

为了性能的考虑，zabbix有类似elk等架构的典型特点，agent和server间支持加入一个proxy来均衡负载。

2019年的4.4版本中，官方开始提供基于golang的agent2作为上报端，性能和维护性上也会好很多。未来有望取代c版本的agent。

### agent2源码解读

这里以5.2.0alpha1为准，来分析一下agent2的核心实现。代码对应哈希86c3d82，agent2对应的代码在src/go下。

zabbix同时支持主动上报和被动请求两种，主动上报是agent主动发起的上报，而被动请求是由server端发起。

agent2代码量比较庞大，但是目录结构和处理逻辑比较清晰。核心代码主要集中在internal/agent中。

从agent2的总体设计来看，整个执行逻辑分为scheduler.Manager、server.Connector、ServerListener三个主要逻辑（goroutine启动），主程序对三个goroutine进行监控。

其中，SchedulerManager负责数据采集、配置更新的调度；ServerConnecter用于与server的连接，负责更新监控项配置；ServerListener主要监控server端发起的被动请求。

这里以三个小条目来分别讨论agent2的实现，分别是监控项同步、plugin机制以及一个简单的plugin实现。

#### 监控项同步

server端启动时会监听一个端口（默认10051），agent2会定期从该端口拉取监控项，默认每两分钟拉取一次。

前面说过，拉取是由server.Connector来做的，它从server端获取配置项后，做一些简单处理，并将其包装为updateRequest，然后将配置作为input输入到scheduler.Manager中。

scheduler.Manager的数据结构如下：

```go
type Manager struct {
	input       chan interface{}
	plugins     map[string]*pluginAgent
	pluginQueue pluginHeap
	clients     map[uint64]*client
	aliases     *alias.Manager
	// number of active tasks (running in their own goroutines)
	activeTasksNum int
	// number of seconds left on shutdown timer
	shutdownSeconds int
}
```

input是一个输入源，上面server.Connector即是将updateRequest发送到Manager.input。

Manager会一直监听Manager.input，检测到*updateRequest后，会将updateRequests中包含的配置更新到plugins字段中，后面会根据plugins做收集和上报。

额外补充个，input还有两类输入，`performer`、`*queryRequest`，`performer` 对应监控采集事件，而 `*queryRequest` 对应被动请求的事件。

需要注意的是，虽然agent2默认支持很多监控项，但是它们不会主动采集。只有server端配置了监控项的指标才会被采集上报。

#### plugin机制

agent2中，plugin机制为plugin预留了多种接口可供实现不同阶段和功能的逻辑，如下：

* Collector：定期收集指标。一般与Exporter结合，以便将收集的指标上报给server
* Exporter：上报指标数据到server。Exporter是这几个接口中唯一一个可以并行处理的接口
* Runner：可在该接口实现初始化和清理操作
* Watcher：可实现自定义的指标采集调度方式
* Configurator：处理配置内容，如配置的有效性判断

plugin可以选择实现其中的一组或多组接口，来提供不同功能的处理。

agent2提供了一个指标注册函数，来注册plugin及其支持的指标，接口定义如下：

```go
func RegisterMetrics(impl Accessor, name string, params ...string)
```

其中，impl即为实现了plugin接口的结构体，下面将使用一个例子来展示如何注册。

scheduler.Manager在初始化时，会将支持的plugins信息写入Manager.plugins。上面说的配置项也会更新到这里。plugins字段是一个核心字段。

### 插件示例

这里给出一个利用插件机制实现的简单插件，该插件提供了两个metric分别生成一个随机整数和一个随机浮点数。

该插件只实现了Exporter接口，并在init()中注册了该插件及两个监控项。

```go
type Plugin struct {
	plugin.Base
}

func (Plugin) Export(key string, params []string, context plugin.ContextProvider) (interface{}, error) {
	switch key {
	case "test.randint":
		return rand.Int(), nil
	case "test.randfloat":
		return rand.Float32(), nil
    default:
        return nil, errors.New(fmt.Sprintf("Unknown metric %s!", key))
	}
	return rand.Int(), nil
}

var impl Plugin

func init() {
	plugin.RegisterMetrics(&impl, "test",
		"test.randint", "Export random int.",
		"test.randfloat", "Export random float.")
}
```

plugins下有plugins_darwin.go、plugins_linux.go、plugins_windows，里面分别配置了不同操作系统下支持的监控项，把test插件记录进去即可支持该监控了。

### zabbix优缺点

作为一个老牌监控方案，zabbix提供的默认监控比较全面，而且技术上有一定积累，运行比较稳定。zabbix的部署相对比较简单。

zabbix的数据库多为mysql等结构型数据库或者elasticsearch等文档型数据库，缺少对时序数据库的支持。

虽然官网也有集成influxdb的方案（链接见参考部分），但都不是官方集成，且需要与其它平台结合使用。最受欢迎的方案3年也只有60个star，可见这种方式并不十分招人待见。

网上也有人提出使用postgresql的tsdb扩展，但是如果没有使用历史，而性能又比较关键的前提下，大家还是会比较关注数据落到何种db。

也有一些方案使用了混搭的方式来寻找出路，比如使用zabbix的采集端，使用grafana来作展示等，方案也是多种多样。这也可见监控相关产品的思路都已比较成熟，各有亮点，解耦也比较彻底。

### 参考

* Zabbix + InfluxDB：<https://www.zabbix.com/integrations/influxdb>
* Zabbix，时间序列数据和TimescaleDB: <https://zhuanlan.zhihu.com/p/66076630>
* Writing plugins: <https://www.zabbix.com/documentation/4.4/manual/concepts/agent2/writing_plugins>
