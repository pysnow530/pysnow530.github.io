---
title: emacs keymaps
date: 2019-03-16
tags:
  - emacs
---

# Table of Contents

1.  [emacs中的keymaps](#org3ccc4a1)
    1.  [keymap结构体](#orga3cd1b5)
    2.  [行为覆盖](#org78e4ee3)
    3.  [两个特化的问题](#org149d732)
        1.  [prefix keys](#org274f6e1)
        2.  [mode继承](#orgff2bd97)
    4.  [结束](#orgdeccdc1)


<a id="org3ccc4a1"></a>

# emacs中的keymaps

emacs具有很高的可配置性，从keybinding，customize，到UI，再到各种第三方package。

keybinding是学习emacs的过程中必经的一环，很难相信有人会不加修改地使用原生的emacs按键行为。

当然，keybinding由来以久。甚至在很多现代的软件中，给它取了一个更激动人心的名字，叫做快捷键，像是一项了不起的发明。其实在emacs里，是最最基础的一项功能。

在这篇文章里，我将尝试从底层的概念开始，讲解emacs里的键绑定机制，以让读者可以自由地定制emacs里的按键，并知其所以然。


<a id="orga3cd1b5"></a>

## keymap结构体

emacs的keybinding有一个基石，或者说设计原则，那就是每一个按键都绑定到了一个函数。从键盘输入，到鼠标，再到菜单，无一不在这个指导原则之下。

试想一下，如果我们来实现这样一个功能，必然是需要一个结构体来关联按键和功能函数的。这个结构体，可以帮助我们快速找到一个按键对应的功能函数。

emacs里使用的列表叫做keymap（大部分编辑器都使用这种称谓）。我们可以使用(keymapp)来检查一个结构是否是标准keymap，实际上它是通过检查列表的第一个元素是否是'keymap来判定的。

    (keymapp '(keymap xxxx))  ;; t

我们可以找一个keymap来看一下它的结构：

M-x describe-variable <ret> org-mode-map

    (keymap
     (25 . org-yank)
     (11 . org-kill-line)
     (5 . org-end-of-line)
     (1 . org-beginning-of-line)
     ;; ...
    )

如上面的代码片段所示，首元素以后的其它元素（cons），由按键和绑定的函数组成。如果我们对25求值，可以看到它对应的按键就是?\C-y。

当然，(key . func-map)只是一种最简形式。比如，我们还需要支持一些按键序列，例如C-x C-f，这个结构就需要扩展一下了。后面再说。

emacs为keymap操作提供了丰富的函数，可以使用下面的例子创建一个keymap，并添加C-;映射：

    (setq map (make-sparse-keymap))      ;; (keymap)
    (define-key map "\C-x" 'c-x-func)
    map  ;; (keymap (24 . c-x-func))  24 => ?C-x


<a id="org78e4ee3"></a>

## 行为覆盖

在上面的例子中，我们已经创建了一个keymap并绑定了C-x的行为。但是它现在只是一个值，如何将其应用到我们的emacs中呢？

不急，要回答这个问题，我们要首先了解，当一个按键按下后，emacs是如何找到它绑定的函数的。

我们知道，在vim中绑定一个按键，可以使用:map命令，如果首参给个<buffer>，它将会作用到当前buffer而不修改全局keymap。（插播一句，由于vimscript只是一个专一化的脚本语言，vim的map行为是在vim内部执行的。我们还不能在vimscript层面可以直观地获取它对应的map）

emacs也存在这种类似<buffer>的参数。当然，keymap的查找被定义为更严格的一个逻辑顺序。

说了这么多，emacs查找按键的顺序有三个：

1.  查找一个神秘但对我们并不重要的map。
2.  查找'minor-mode-map-alist。
3.  查找(current-local-map)。一般会由major-mode设定。
4.  查找(current-global-map)。一般会等于global-map变量，是emacs的默认全局配置。

好吧，如果你真的对1感兴趣，其实它是一个粒度更细的map，它会绑定到一个buffer里指定的某些文本。如果这个解释不能满足你，可以看一下text-property相关的手册。

2、3不言而喻了，需要说明的一点是，如果我们知道某个mode的名字，可以很方便地找到它对应的map变量，如org-mode对应的keymap为org-mode-map。

现在我们知道了keymap可以定义的多个层级，text-property -> minor-mode -> major-mode -> global-map。

上面我们讲到一个(define-key)函数，可用来修改keymap变量里的某个绑定。现在你应该已经知道网上某个家伙emacs配置里的代码片段是什么含义了：

    (define-key 'global-map "C-x C-e" 'func)


<a id="org149d732"></a>

## 两个特化的问题

主要的内容已经讲完了，下面再赠送两个额外的内容。


<a id="org274f6e1"></a>

### prefix keys

我想试着绕开这个内容，但是发现做不到。如果真正碰到了，会感觉很迷惑，不如两笔带一下。

我们上面提到，keymap的元素不一定是(key . map-func)的形式，比如C-x C-f，它实际上是两个序列的组合。在emacs中使用这样的形式来定义：(key . keymap2)，即它的map-func是另一个keymap。

举个例子，假设我们想在全局的keymap下，定义一个前缀输入为C-;的序列，让它在我们输入C-; 2时，在2的后面添加一个;（只是试验，毫无价值）。

    (defun append-semicolon ()
      (interactive)
      (self-insert-command 1)
      (insert ";"))
    
    (setq ctl-semicolon-map (make-sparse-keymap))
    (define-key ctl-semicolon-map "2" 'append-semicolon)
    
    (define-key global-map (kbd "C-;") ctl-semicolon-map)

这时，如果我们输入一个C-; 2时，编辑器里就会输入一个2;。

需要注意，此时，如果我们修改global-map的C-; 3，修改的实际上是ctl-semicolon-map。

    (define-key global-map (kbd "C-; 3") 'append-semicolon)
    ctl-semicolon-map  ;; => (keymap (51 . append-semicolon) (50 . append-semicolon))

emacs里的C-x等序列就是这样定义的。


<a id="orgff2bd97"></a>

### mode继承

emacs里的mode是有继承关系的，例如所有的编程语言mode都 **应该** 继承自 *prog-mode* ，所以针对编程语言的通用keymap，可以直接修改 *prog-mode-map* 。

具体的细节，可以查看mode设计的手册。


<a id="orgdeccdc1"></a>

## 结束

以上的内容就可以把整个keymap串起来了，如果有什么地方不了解，所有需要的知识都在 `C-h i` 里。尽情查阅吧。

