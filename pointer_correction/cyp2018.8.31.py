#!/usr/bin/env python
# -*- coding:utf-8 -*-

import platform
from tkinter import *
import tkinter as tk
from tkinter import ttk
import threading
import time
import random
import serial
from struct import pack, unpack



# ser = serial.Serial('/dev/serial0', 115200, timeout=1)
# ser.parity = serial.PARITY_ODD


root = Tk()
root.title("Tkinter")
root.minsize(800, 600)
#root.geometry("800x600")
root.resizable(False, False)
n = random.randint(1, 100)
count = 0


def serial_port_open():
    #ser = serial.Serial('/dev/serial0', 115200, timeout=1)
    if ser.isOpen is False:
        ser.open()


def close():
    #ser = serial.Serial('/dev/serial0', 115200, timeout=1)
    if ser.isOpen is True:
        ser.close()


def segmentation():
    # Initialization: according to subsection, fill in entry
    nu = int(numberChosen.get())
    for x in firstlists:
        x['bg'] = 'gray'
        x.delete(0, END)

    for x in secondlists:
        x['bg'] = 'gray'
        x.delete(0, END)

    for j in range(nu + 1):
        firstlists[j]['bg'] = 'white'
        firstlists[j].insert(END, int(0 + 3240 / nu * j))

    for j in range(nu + 1):
        secondlists[j]['bg'] = 'white'
        secondlists[j].insert(END, int(0 + 3240 / nu * j))


def write2_data():
    # Initialization: communication format
    nu = int(numberChosen.get())
    cmd2_position3 = pack('b', nu)
    cmd2_head = b'UUUU3'
    if directionChosen.get() == 'right':
        cmd2_direct = b'\x52'
    else:
        cmd2_direct = b'\x4C'

    ser.write(cmd2_head)
    ser.write(b'\x03')
    ser.write(b'\x02')
    ser.write(cmd2_position3)
    ser.write(cmd2_direct)
    time.sleep(6)


def write2():
    # Initialization: send to serial_port and show in lb2
    global count
    lb2.delete(0, END)
    p = portChosen.get()
    b = burChosen.get()
    c = chbChosen.get()
    nu = numberChosen.get()
    d = directionChosen.get()
    lb2.insert(END, "1.Serial port setting")
    lb2.insert(END, '   serial_port: ' + ' ' + p)
    lb2.insert(END, '   baud_rate: ' + ' ' + b)
    lb2.insert(END, '   checkout_bit: ' + ' ' + c)
    lb2.insert(END, "2.Initialization")
    lb2.insert(END, '   subsection: ' + ' ' + nu)
    lb2.insert(END, '   direction: ' + ' ' + d)
    t = threading.Thread(target=segmentation)
    t.start()
    count = -1
    data1 = threading.Thread(target=write2_data)
    data1.start()


def function():
    ##Correction: highlight
    nu = int(numberChosen.get())
    if -1 < count <= nu:
        secondlists[count]['bg'] = 'red'


def make_data():
    #Correction: communication format

    '''
    meter_float = 0.0
    cmd3_position1 = pack('f', meter_float)
    cmd3_head = b'UUUU3'
    ser.write(cmd3_head)
    ser.write(b'\x05')
    ser.write(b'\x03')
    ser.write(cmd3_position1)
    time.sleep(6)
    '''

    meter_float = 0.0
    cmd3_position1 = pack('f', meter_float)
    cmd3_head = b'UUUU2'
    ser.write(cmd3_head)
    ser.write(b'\x01')
    ser.write(cmd3_position1)
    time.sleep(6)


def make_zero():
    # Correction: return to zero
    global n
    global count
    nu = int(numberChosen.get())
    count = 0
    n = 0
    en1.delete(0, END)
    en1.insert(1, n)
    for x in range(nu + 1):
        secondlists[x]['bg'] = 'white'
    th = threading.Thread(target=function)
    th.start()
    data2 = threading.Thread(target=make_data)
    data2.start()


def write3_data():
    # Correction: communication format
    global n
    n = 0
    for x in secondlists:
        if x['bg'] == 'red':
            n = int(x.get())

    '''
    cmd3_position2 = pack('>L', n)
    cmd3_head = b'UUUU3'
    ser.write(cmd3_head)
    ser.write(b'\x05')
    ser.write(b'\x03')
    ser.write(cmd3_position2)
    time.sleep(6)
    '''

    cmd3_position2 = pack('f', n)
    cmd3_head = b'UUUU2'
    ser.write(cmd3_head)
    ser.write(b'\x01')
    ser.write(cmd3_position2)
    time.sleep(6)


def add():
    global n
    m = int(numChosen.get())
    for x in secondlists:
        if x['bg'] == 'red':
            n = int(x.get())
            if n < 3240:
                n += m
                x.delete(0, END)
                x.insert(END, n)
    data3 = threading.Thread(target=write3_data)
    data3.start()


def minus():
    global n
    m = int(numChosen.get())
    for x in secondlists:
        if x['bg'] == 'red':
            n = int(x.get())
            if n > 0:
                n -= m
                x.delete(0, END)
                x.insert(END, n)
    data3 = threading.Thread(target=write3_data)
    data3.start()


def next():
    global count
    nu = int(numberChosen.get())
    count += 1
    if count <= nu:
        for j in range(nu):
            secondlists[j]['bg'] = 'white'
            th = threading.Thread(target=function)
            th.start()
    else:
        count -= 1
        lb2.insert(END, '##########The number is right-beyond!!')

    data3 = threading.Thread(target=write3_data)
    data3.start()


def last():
    global count
    nu = int(numberChosen.get())
    count -= 1
    if count >= 0:
        for j in range(nu + 1):
            secondlists[j]['bg'] = 'white'
            th = threading.Thread(target=function)
            th.start()
    elif count <= -2:
        count = 0
        for j in range(nu + 1):
            secondlists[j]['bg'] = 'white'
            th = threading.Thread(target=function)
            th.start()
    else:
        count += 1
        lb2.insert(END, '##########The number is left-beyond!!')

    data3 = threading.Thread(target=write3_data)
    data3.start()


def write_data():
    # Correction: communication format
    nu = int(numberChosen.get())
    cmd_head = b'UUUU3'
    cmd_len = nu * 4 + 5
    cmd_position1 = pack('b', cmd_len)
    ser.write(cmd_head)
    ser.write(cmd_position1)
    # ser.write(b'\x05')
    ser.write(b'\x03')

    for j in range(nu + 1):
        x = int(secondlists[j].get())
        #lb1.insert(END, x)
        cmd_position2 = pack('f', x)
        ser.write(cmd_position2)
    time.sleep(3)


def write():
    # Write: send array and show in lb2
    lb2.delete(7, END)
    nu = int(numberChosen.get())
    for j in range(nu+1):
        #flists = [firstlists[j].get()]
        slists = [secondlists[j].get()]
        lb2.insert(END, slists)
        #lb2.insert(END, flists + slists)
    data4 = threading.Thread(target=write_data)
    data4.start()

# step 1:Serial
sps = Label(root, text='1.Serial port setting')
sps.place(x=10, y=20, width=130, height=30)

sep = Label(root, text='serial_port')
sep.place(x=10, y=60, width=70, height=30)
port = tk.StringVar()
portChosen = ttk.Combobox(root, width=5, height=30, textvariable=port, state='readonly')
portChosen['values'] = ('COM3', 'COM6', 'COM8')
portChosen.place(x=80, y=60)
portChosen.current(0)

sub = Label(root, text='baud_rate')
sub.place(x=10, y=100, width=70, height=30)
bur = tk.StringVar()
burChosen = ttk.Combobox(root, width=5, height=30, textvariable=bur, state='readonly')
burChosen['values'] = (9600, 19200, 38400, 57600, 115200, 'Custom')
burChosen.place(x=80, y=100)
burChosen.current(4)

drt = Label(root, text='checkout')
drt.place(x=10, y=140, width=70, height=30)
chb = tk.StringVar()
chbChosen = ttk.Combobox(root, width=5, height=30, textvariable=chb, state='readonly')
chbChosen['values'] = ('None', 'Even', 'Odd', 'Mark', 'Space')
chbChosen.place(x=80, y=140)
chbChosen.current(2)

btn7 = Button(root, text="Open",  command=serial_port_open)
btn7.place(x=30, y=180, width=40, height=25)

btn8 = Button(root, text="Close",  command=close)
btn8.place(x=85, y=180, width=40, height=25)


# step 2:Initialization
itz = Label(root, text='2.Initialization')
itz.place(x=10, y=220, width=130, height=30)

sub = Label(root, text='subsection')
sub.place(x=10, y=260, width=70, height=30)

number = tk.IntVar()
numberChosen = ttk.Combobox(root, width=5, height=30, textvariable=number, state='readonly')
numberChosen['values'] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
numberChosen.place(x=80, y=260)
numberChosen.current(5)

drt = Label(root, text='direction')
drt.place(x=10, y=300, width=70, height=30)
direction = tk.StringVar()
directionChosen = ttk.Combobox(root, width=5, height=30, textvariable=direction, state='readonly')
directionChosen['values'] = ('left', 'right')
directionChosen.place(x=80, y=300)
directionChosen.current(1)

btn1 = Button(root, text='write', bg='red', command=write2)
btn1.place(x=65, y=340, width=40, height=25)


# step 3:Correction
crt = Label(root, text='3.Correction')
crt.place(x=10, y=380, width=130, height=30)

btn2 = Button(root, text='zero', command=make_zero)
btn2.place(x=65, y=420, width=40, height=25)


sus = Label(root, text='subsection')
sus.place(x=10, y=460, width=70, height=30)
btn3 = Button(root, text='<-', bg='white', command=last)
btn3.place(x=80, y=460, width=30, height=25)
btn4 = Button(root, text='->', bg='white', command=next)
btn4.place(x=110, y=460, width=30, height=25)

ajs = Label(root, text='adjustment')
ajs.place(x=10, y=500, width=70, height=30)
btn5 = Button(root, text='+', bg='white', command=add)
btn5.place(x=80, y=500, width=30, height=25)
btn6 = Button(root, text='-', bg='white', command=minus)
btn6.place(x=110, y=500, width=30, height=25)

num = tk.StringVar()
numChosen = ttk.Combobox(root, width=4, height=30, textvariable=num, state='readonly')
numChosen['values'] = (5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
numChosen.place(x=140, y=505)
numChosen.current(0)

# Write
btn10 = Button(root, text="Write", bg='red', command=write)
btn10.place(x=75, y=540, width=50, height=30)

# Exit
btn9 = Button(root, text="Exit", bg='red', command=root.quit)
btn9.place(x=640, y=540, width=50, height=30)


a = 200
en11 = Entry(root)
en11.place(x=a, y=50, width=50, height=30)
en12 = Entry(root)
en12.place(x=a+50, y=50, width=50, height=30)
en13 = Entry(root)
en13.place(x=a+100, y=50, width=50, height=30)
en14 = Entry(root)
en14.place(x=a+150, y=50, width=50, height=30)
en15 = Entry(root)
en15.place(x=a+200, y=50, width=50, height=30)
en16 = Entry(root)
en16.place(x=a+250, y=50, width=50, height=30)
en17 = Entry(root)
en17.place(x=a+300, y=50, width=50, height=30)
en18 = Entry(root)
en18.place(x=a+350, y=50, width=50, height=30)
en19 = Entry(root)
en19.place(x=a+400, y=50, width=50, height=30)
en20 = Entry(root)
en20.place(x=a+450, y=50, width=50, height=30)
en22 = Entry(root)
en22.place(x=a+500, y=50, width=50, height=30)
firstlists = [en11, en12, en13, en14, en15, en16, en17, en18, en19, en20, en22]

en1 = Entry(root)
en1.place(x=a, y=80, width=50, height=30)
en2 = Entry(root)
en2.place(x=a+50, y=80, width=50, height=30)
en3 = Entry(root)
en3.place(x=a+100, y=80, width=50, height=30)
en4 = Entry(root)
en4.place(x=a+150, y=80, width=50, height=30)
en5 = Entry(root)
en5.place(x=a+200, y=80, width=50, height=30)
en6 = Entry(root)
en6.place(x=a+250, y=80, width=50, height=30)
en7 = Entry(root)
en7.place(x=a+300, y=80, width=50, height=30)
en8 = Entry(root)
en8.place(x=a+350, y=80, width=50, height=30)
en9 = Entry(root)
en9.place(x=a+400, y=80, width=50, height=30)
en10 = Entry(root)
en10.place(x=a+450, y=80, width=50, height=30)
en21 = Entry(root)
en21.place(x=a+500, y=80, width=50, height=30)
secondlists = [en1, en2, en3, en4, en5, en6, en7, en8, en9, en10, en21]

#lb1 = Listbox(root)
# lb1.place(x=a, y=170, width=200, height=350)

lb2 = Listbox(root)
lb2.place(x=a, y=170, width=550, height=350)

root.mainloop()


