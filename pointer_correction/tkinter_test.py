# csdndemo.py
# python 3.1

from tkinter import *
from tkinter import ttk


def switchBtn1Status():
    if btn1.instate(['disabled']):
        btn1.state(['!disabled'])
        btn2.config(text='Disable Button1')
    else:
        btn1.state(['disabled'])
        btn2.config(text='Enable Button1')


root = Tk()

btn1 = ttk.Button(root, text='Button1')
btn1.pack(side=LEFT)

btn2 = ttk.Button(root, text='Disable Button1', command=switchBtn1Status)
btn2.pack(side=LEFT)

root.grab_set()
root.mainloop()