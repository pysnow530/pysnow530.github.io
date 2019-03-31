
# Table of Contents

1.  [lisp论文《recursive》](#org8485cb3)
    1.  [lisp并非无所不能](#org4c03370)
    2.  [阅读这篇论文最大的障碍](#org6a4e274)
    3.  [lisp的基础是数学](#org18bba9b)
    4.  [关于波兰表达式](#org2aba115)
    5.  [声名式和命令式（declarative and imperative）](#org6f8f2a4)
    6.  [内存管理](#org87f196d)
    7.  [函数名的设计](#orgd6c8ec5)
    8.  [lisp中的数据结构](#orgc3b8729)
    9.  [lisp的学习成本](#org47cd5c3)
    10. [过程中遇到的一些小问题](#org5208a74)
    11. [附](#org5e33078)
        1.  [eval](#orgac04c10)
        2.  [引用](#orgb2fe6d3)


<a id="org8485cb3"></a>

# lisp论文《recursive》

论文的全称是《Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I》，是人工智能之父John McCarthy在1960年4月发表的。

之前读过一次，感觉很震撼。这次阅读下来，零零散散地加在一起，包括最后写的一个求值表达式的调试过程，总耗时大概有7个小时。

虽然时间已经过去60年，作者John McCarthy也已经离开我们7年，数学总归是数学，所以论文的语法，跟现在也不会有太大的差别。

重要的还是思想，借助文字来了解先驱所处的时代和想法，这也是我读这篇论文的初衷。

读到这样一篇踏实的论文还是很幸运的，虽然在最开始感到吃力。

这让我想起了《how to read a book》里讲到阅读的目的，比如看一则新闻，大多时候我们只是在获取更多的信息，对我们的理解能力并没有太大的提升。但是当阅读一篇在我们理解能力之外的文章时，虽然会有些吃力，但是它的回报是远远超过我们付出的。

系统的介绍论文的内容不是这篇文章的目的，且作者写的比我要详细准确一百万倍有余，我这里记录一下自己比较有感触的地方（意思就是跟这篇论文的内容关系不大 :-p）。


<a id="org4c03370"></a>

## lisp并非无所不能

刚上来就要泼一下冷水了。

lisp很强大，你可以看我最后从论文里摘抄出来的一个 *eval* 求值函数的实现，一个可以用自己重写自身的语言，已经不能用强大来形容了。

lisp最重要的是思想，当然它也支撑了一些很重要的软件，比如emacs、autocad，但它终归不能作为商用软件的语言。

原因有很多，说一点，它的生态就比一些主流语言差很多，假如出现了一款新型数据库，社区要做语言的第三方库支持，肯定不会优先想到一门非主流语言。

所以即使lisp很好很强大，它的使用场景也很局限。


<a id="org6a4e274"></a>

## 阅读这篇论文最大的障碍

我们记住一个东西或者学会一个东西很容易，但是要忘记就很难了。知识就是这样一个东西。

这是我最开始阅读时遇到最大的一个障碍，60年，还需要再过12年c语言才会被发明出来，至于java还要再等35年。

举个例子，如果我们熟悉了现在主流的语言设计，一开始可能会对 *S-expression* 、 *M-expression* 感到有些费解。

所以，我做的第一个尝试就是忘记之前所学的（表面）知识。

想起了张三丰跟张无忌的对话，这也算是我对这段对话的一个认识吧。


<a id="org18bba9b"></a>

## lisp的基础是数学

最开始有点难，但是当我理解了lisp设计的基础，一些东西就很容易理解了。

lisp的语言基础，是从数学的基本形式归纳出来的。如何将数学的逻辑和表达式抽象成一个统一的表达形式，是lisp要解决的一个问题。

有的人说lisp很美，大多时候指的并不是它的表现形式（当然，可能也有人觉得lisp的括弧很美），而是指它的底层结构。这也是它可以很方便地重写自身的原因。

这种古老的语言（而不是现代的语言），让我更加确信计算机科学是数学的一个分支。

现代语言的设计，基于计算机的比例变得越来越高。

一个原因是，数学是一门语言的核心，核心的东西一般都较小，而且现在语言支持的特性越来越庞大，不可避免会有越来越多的非核心的面向计算机的代码。比如，多核心，多线程，有越来越多的计算机术语被发明出来。


<a id="org2aba115"></a>

## 关于波兰表达式

波兰表达式（polish notation）和代数表达式（algebraic notation）是两个很典型的数学表达式（还有逆波兰表达式，如emacs的calc）。

最直观的方式是代数表达式，面向人类。

波兰表达式的优点在于它的结构更加统一，更易于流程化的处理。还有很重要的一点，它可以做到数据和运算分离，这可能是emacs的calc工具使用逆波兰表达式的原因。

比如，我们经常会计算一个月内的开销，有时就是一些小花费的总和，这时如果使用波兰表达式就很清楚明了，(+ 30.0 20.0 30.0 40.0)。


<a id="org6f8f2a4"></a>

## 声名式和命令式（declarative and imperative）

这两个概念在60年就已经存在了，不过现在有一些人还是不太清楚。

一句话，初级领导用命令式，高级领导用声明式。


<a id="org87f196d"></a>

## 内存管理

是的，内存管理在60年的lisp里就已经实现了。使用lisp的程序员们不需要关心内存释放，甚至都不需要知道存在内存这样的东西（当然，没人不知道）。

由于lisp的基础很简单，所以lisp内存的实现也很简单。这是一个良性循环。


<a id="orgd6c8ec5"></a>

## 函数名的设计

这在现在看来已经是理所当然的了。

但是在最开始的设计中，如何实现数学中的函数是一个值得被推敲的事情。

lisp使用了 *Church* 中定义的 *lambda* 的原型，把函数实现中的某些参数（形参）和实参绑定，以此为上下文对实现进行求值。

但是 *lambda* 不能解决递归的问题，比如辗转相除求最大公约数或者利用牛顿公式求解微分方程。

函数名的设计可以解决这个问题，即将名称与实现绑定，实现中就可以使用名称来递归自身了。


<a id="orgc3b8729"></a>

## lisp中的数据结构

所谓一生二，二生万物。

lisp中的基本数据结构只是一个包含两个元素的元组，但是元组可以互相组合，它的表达能力是无穷的（这里的表达能力指的不是可读性，而是表达的内容）。

而且在形式上有一个莫大的好处，就是它非常适合实现递归的思想。

这里插播一段代码，比如定义一个函数，将 *APPLE* 转换为 *BOY* 。

    (defun replace-apple-to-boy (x)
      (cond ((atom x) (or (and (eq x 'apple) 'boy) x))
    	(t (cons (replace-apple-to-boy (car x))
    		 (replace-apple-to-boy (cdr x))))))
    
    (replace-apple-to-boy '((apple foo) apple)) ;; => ((boy foo) boy)


<a id="org47cd5c3"></a>

## lisp的学习成本

是的，学习lisp几乎没有学习成本。主要成本在lisp的思想上，即递归，这几乎是学习所有语言必知必会的东西。

lisp的基础构建在几个原子操作上，学习的时间应该可以用分钟来计了。

所以emacs使用elisp来作为扩展语言，甚至很多非计算机专业的人来了兴致也可以敲上几行代码。

觉得lisp很难的人，很多都是有其它现代语言基础的人。


<a id="org5208a74"></a>

## 过程中遇到的一些小问题

html版本有个好处是组织结构更清晰，一章一个链接，不过公式排版差强人意。

pdf版好一些，但是在eval的定义一块格式还是有问题，特别是嵌套层次深了以后，很难一眼看出自己在哪里。最好是自己重新排版一下。

网络上还有一些排版更友好一些的版本，不过差别不会太大。


<a id="org5e33078"></a>

## 附


<a id="orgac04c10"></a>

### eval

这是lisp很强大的一个经典论证，即在语言之上实现该语言的求值器。

NOTE: 该代码使用了elisp，在其它lisp方言应该也可以正常运行。其中只使用了有限的几个函数（car cdr cons cond eq atom）。

    (defun assoc2 (x y)
      (cond ((null y) nil)
    	((eq x (caar y)) (cdar y))
    	(t (assoc2 x (cdr y)))))
    
    (defun append2 (x y)
      (cond ((null x) y)
    	(t (cons (car x) (append2 (cdr x) y)))))
    
    (defun evcon (c a)
      (cond ((eval2 (caar c) a) (eval2 (cadar c) a))
    	(t (evcon (cdr c) a))))
    
    (defun evlis (m a)
      (cond ((null m) nil)
    	(t (cons (eval2 (car m) a) (evlis (cdr m) a)))))
    
    (defun pair (x y)
      (cond ((and (null x) (null y)) nil)
    	((and (not (atom x)) (not (atom y))) (cons (cons (car x) (car y)) (pair (cdr x) (cdr y))))))
    
    (defun eval2 (e a)
      (cond ((atom e) (assoc2 e a))
    	((atom (car e))
    	 (cond ((eq (car e) 'QUOTE) (cadr e))
    	       ((eq (car e) 'ATOM) (atom (eval2 (cadr e) a)))
    	       ((eq (car e) 'EQ) (eq (eval2 (cadr e) a) (eval2 (caddr e) a)))
    	       ((eq (car e) 'COND) (evcon (cdr e) a))
    	       ((eq (car e) 'CAR) (car (eval2 (cadr e) a)))
    	       ((eq (car e) 'CDR) (cdr (eval2 (cadr e) a)))
    	       ((eq (car e) 'CONS) (cons (eval2 (cadr e) a) (eval2 (caddr e) a)))
    	       (t (eval2 (cons (assoc2 (car e) a) (evlis (cdr e) a)) a))))
    	((eq (caar e) 'LABEL) (eval2 (cons (caddar e) (cdr e)) (cons (cons (cadar e) (car e)) a)))
    	((eq (caar e) 'LAMBDA) (eval2 (caddar e) (append (pair (cadar e) (evlis (cdr e) a)) a)))))

下面这个例子使用了前面定义的 *eval2* ，来拼接两个参数里的首元素。

    (eval2 '((LAMBDA (x y) (CONS (CAR x) (CAR y))) (CONS (QUOTE A) (QUOTE B)) (CONS (QUOTE C) (QUOTE D))) nil)  ;; => (A . C)

这个函数有一个缺陷，在使用 *LABEL* 进行递归求值时，会再次对求值后的结果进行二次求值，导致错误。

论文中提到有一个修正版本，发布在91年的《Artificial and Mathematical Theory of Computation》。在sciencedirect.com上找到一个收费版的地址，没有继续下去了。地址在下方。

图书管可能有这类书？


<a id="orgb2fe6d3"></a>

### 引用

<http://www-formal.stanford.edu/jmc/recursive.html>
<https://www.sciencedirect.com/book/9780124500105/artificial-and-mathematical-theory-of-computation>

