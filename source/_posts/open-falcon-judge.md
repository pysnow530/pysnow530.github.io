---
title: open-falcon 告警判定
date: 2020-05-26 20:24:04
tags:
  - open-falcon
  - 监控告警
---

### 引子

上一篇文章 《[open-falcon 监控上报](/2020/05/25/open-falcon-agent/)》中讲了open-falcon的设计以及监控上报的逻辑，这篇文章呈接上篇，继续探讨告警判定的逻辑。

监控数据是一个写多读少的数据，几乎每时每刻都在写，但是查看的时间一般很短。用户不可能一直盯着它，告警即是做为另一个入口补充进来的。告警如何配置、如何触发，如何优雅的通知到接收人，是告警要解决的问题。

在设计告警时，可能会存在几个坑，一是告警过多，如阈值设置太低，而没有做告警收敛就会遇到这种情况，既耗费了用户的精力，还有可能把告警通道阻塞；二是告警失效，如果后端发送如短信超载被禁就会出现该种情况。

第一种情况，告警过多一般会设置告警收敛，如一条告警告了几次就不要再告了，或者过一段时间再告，防止接收人被告警信息淹没；同时，一些不重要的告警可以设置告警屏蔽，先屏蔽它一小时，一小时后再来处理。

第二种情况，在确保告警通道稳定的情况下，最好提供多种方案，短信、微信、邮箱、钉钉，一个挂了还有另外的补全。同时，可发送多个相关人员，A没注意到B也可以处理。

下面主要从以下几个方面说一下open-falcon的告警逻辑：

* 数据链路：agent 采集的数据是如何流转到告警判定模块的
* 判定规则：judge 如何判定一份监控数据是否异常
* 告警配置：open-falcon 中是如何管理告警配置的

### 数据链路

上篇文章中讲到，agent 组件会以多种方式（builtins、plugin、push）采集监控数据。open-falcon组件间多以rpc协议通信，agent通过rpc把采集到的数据上传到transfer，再由transfer分发给judge。

这里judge可以部署多个节点来分担负载，transfer会通过一致性哈希来决定将信息分发到哪个judge节点。

judge即是告警判定组件，它会从hbs中获取portal的监控规则配置，然后判断推送过来的数据是否应该告警，并将告警信息写入redis。

后端的alarm从redis中取告警信息，并通过不同的告警通道转发出去。

### 判定规则

judge 的判定条件有两种，一种是 strategy，它通过绑定告警模板到某个主机组生效；另一种是 expression，它可以监控非主机的情况。

这两种方式的实现核心是一样的，这里以机器监控为例。

假设我们希望定义一个告警规则，某个主机组中的主机，如果负载连续3次上报均大于4，则告警。我们会在该主机组绑定的告警模板下，添加一条判定规则：load.1min all(#3) > 4。

其中all为聚合函数，all(#3) > 4 意思是最近三次的值均大于4。open-falcon 提供了多种聚合函数，目前可以支持的聚合函数有：max, min, all, sum, avg, diff, pdiff, lookup, stddev。

该规则下发到judge后，被 `ParseFuncFromString()` 函数解析为一个包含判定逻辑的结构体：

```go
type Function interface {
	Compute(L *SafeLinkedList) (vs []*model.HistoryData, leftValue float64, isTriggered bool, isEnough bool)
}
```

all聚合函数对应的逻辑结构体如下所示：

```go
type AllFunction struct {
	Function
	Limit      int
	Operator   string
	RightValue float64
}

func (this AllFunction) Compute(L *SafeLinkedList) (vs []*model.HistoryData, leftValue float64, isTriggered bool, isEnough bool) {
	vs, isEnough = L.HistoryData(this.Limit)
	if !isEnough {
		return
	}

	isTriggered = true
	for i := 0; i < this.Limit; i++ {
		isTriggered = checkIsTriggered(vs[i].Value, this.Operator, this.RightValue)
		if !isTriggered {
			break
		}
	}

	leftValue = vs[0].Value
	return
}
```

该函数可以判定历史数据是否触发告警规则，触发则生成一条 event，event 结构如下：

```go
// 机器监控和实例监控都会产生Event，共用这么一个struct
type Event struct {
	Id          string            `json:"id"`
	Strategy    *Strategy         `json:"strategy"`
	Expression  *Expression       `json:"expression"`
	Status      string            `json:"status"` // OK or PROBLEM
	Endpoint    string            `json:"endpoint"`
	LeftValue   float64           `json:"leftValue"`
	CurrentStep int               `json:"currentStep"`
	EventTime   int64             `json:"eventTime"`
	PushedTags  map[string]string `json:"pushedTags"`
}
```

### 告警管理

前面提到过，open-falcon的告警规则是绑定到主机组的，这也是为了简化告警的配置。数台机器怎么配都不是问题，但是当机器增长到上千上万台，不分组管理是不现实的。

上面还提到一个 expression 的告警配置，这个配置比较适合于业务告警的场景，摆脱了主机组等实体的限制，更为灵活机动。

### 一些补充

值得一提的是，transfer 的后端支持比较丰富，目前还支持 tsdb 和 influxdb 数据库，可灵活使用后端来完成定制化的功能。

judge 的判定规则是基于阈值的，难以做一些同比环比类的告警，不过可以通过其它方式来自主实现，应该不是很大的问题。
