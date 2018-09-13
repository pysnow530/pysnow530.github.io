#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 定义人类
class Person:
    name = ''
    birthday = ''

    def speak(self):
        print "Hello, I'm", self.name

    def write(self):
        pass

    def trivia(self):
        pass

# 具体化一个人，并写入老王的信息
mr_wang = Person()
mr_wang.name = '老王'
mr_wang.birthday = '1962-10-13'

# 让老王开口说话
mr_wang.speak()
