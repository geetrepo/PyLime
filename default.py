#!/usr/bin/env python
# -*-coding:utf-8-*-
def F():
    a,b = 0,1
    yield a
    yield b
    while True:
        a, b = b, a + b
        yield b
        
def SubFib(startNumber, endNumber):
    for cur in F():
        if cur > endNumber: return
        if cur >= startNumber:
            yield cur

for i in SubFib(10, 200):
    print i