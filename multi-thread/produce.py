#!/usr/bin/env python3

from atexit import register
from random import randint
from threading import BoundedSemaphore, Lock, Thread
from time import sleep, ctime

lock = Lock()
INIT_VALUE = 5
s = BoundedSemaphore(INIT_VALUE)


def produce():
    lock.acquire()
    print('producing...')
    try:
        s.release()
    except ValueError as e:
        print('full, skipping...')
    else:
        print('after producing, now is:', s._value)
    lock.release()


def consume():
    lock.acquire()
    print('consuming...')
    if s.acquire(False):    # False表示非阻塞
        print('after consuming, now is:', s._value)
    else:
        print('empty, skipping...')
    lock.release()


def producer(loops):
    for i in range(loops):
        produce()
        sleep(randint(0, 3))


def consumer(loops):
    for i in range(loops):
        consume()
        sleep(randint(0, 3))


def main():
    print('starting at:', ctime())
    nloops = randint(2, 6)
    print('INIT_VALUE is', INIT_VALUE)
    Thread(target=consumer, args=(
        randint(nloops, nloops + INIT_VALUE + 2), )).start()
    Thread(target=producer, args=(nloops, )).start()


@register
def _atexit():
    print('ending at:', ctime())

if __name__ == '__main__':
    main()