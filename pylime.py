#!/usr/bin/python
# -*- coding: utf-8 -*-
# PyLime - Sublime like Python Text Editor 
# License: GPL v3
#
# Raster Ron (c) 2014 - 2015
# http://github.com/rasteron
#
import keyword
import re
from string import ascii_letters, digits, punctuation, join
import codecs

import os
import sys
from Tkinter import *
from PIL import Image, ImageDraw, ImageTk, ImageFont

from Dialog import Dialog
import fileinput

import tkFont

import tkMessageBox
import tkFileDialog
from tkFileDialog import askopenfilename

import Tkinter as tk

current_file = ''

root = Tk()
root.tk.call('wm', 'iconbitmap', root, '-default', 'icon.ico')
ed = ''


class StatusBar(tk.Frame):

    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.label = tk.Label(
            self,
            bd=0,
            relief=tk.SUNKEN,
            anchor=tk.E,
            textvariable=status,
            font=('Meslo LG L', 9, 'normal'),
            background='#404040',
            foreground='#ffffff',
            padx=10,
            pady=5,
            )
        status.set('Ready')
        self.label.pack(fill=tk.X)
        self.pack(side='left')


class EditorClass(object):

    UPDATE_PERIOD = 100  # ms

    editors = []
    updateId = None

    def __init__(self, master):

        self.__class__.editors.append(self)

        self.lineNumbers = ''

        # A frame to hold the three components of the widget.

        self.frame = Frame(master, bd=0, relief=SUNKEN)

        # The widgets vertical scrollbar

        self.vScrollbar = Scrollbar(self.frame, orient=VERTICAL)
        self.vScrollbar.pack(fill='y', side=RIGHT)

        self.customFont = tkFont.Font(family='Meslo LG L', size=10)

        # The Text widget holding the line numbers.

        self.lnText = Text(
            self.frame,
            width=5,
            padx=5,
            highlightthickness=0,
            takefocus=0,
            bd=0,
            background='#454949',
            foreground='#8F908A',
            state='disabled',
            font=self.customFont,
            )
        self.lnText.pack(side=LEFT, fill='y')

        # The Main Text Widget

        self.text = Text(
            self.frame,
            width=150,
            bd=0,
            padx=4,
            undo=True,
            background='#272822',
            foreground='#f8f8f8',
            insertbackground='#ffffff',
            font=self.customFont,
            tabs='1c',
            )

        self.text.tags = {
            'kw': '#DA2731',
            'int': '#AE81FF',
            'str': '#E6DB74',
            'brace': '#E6DB74',
            'comment': '#75715E',
            }

        # self.text.config_tags(self)

        for (tag, val) in self.text.tags.items():
            self.text.tag_config(tag, foreground=val)

        self.text.characters = ascii_letters + digits + punctuation

        self.text.bind('<Key>', self.key_press)

        self.text.pack(side=LEFT, fill=BOTH, expand=1)

        self.text.bind('<Control-Key-a>', self.select_all)

        # self.text.bind("<KeyPress>", self.hilight)

        self.text.bind('<Control-Key-s>', self.save_file)

        self.text.config(yscrollcommand=self.vScrollbar.set)

        self.vScrollbar.config(command=self.text.yview)

        filemenu.add_command(label='Save', command=self.save_file_menu,
                             accelerator='Ctrl+S')
        filemenu.add_command(label='Exit', command=self.onExit,
                             accelerator='Alt+F4')
        root.config(menu=menubar)

        if self.__class__.updateId is None:
            self.updateAllLineNumbers()

    def config_tags(self):
        print tag
        for (tag, val) in self.text.tags.items():
            self.text.tag_config(tag, foreground=val)

    def remove_tags(self, start, end):
        for tag in self.text.tags.keys():
            self.text.tag_remove(tag, start, end)

    def key_press(self, key):
        cline = self.text.index(INSERT).split('.')[0]

        # print cline

        lastcol = 0
        char = self.text.get('%s.%d' % (cline, lastcol))
        while char != '\n':
            lastcol += 1
            char = self.text.get('%s.%d' % (cline, lastcol))

        buffer = self.text.get('%s.%d' % (cline, 0), '%s.%d' % (cline,
                               lastcol))
        tab = len(buffer) - len(buffer.lstrip())
        tokenized = buffer.split(' ')

        self.remove_tags('%s.%d' % (cline, 0), '%s.%d' % (cline,
                         lastcol))

        (start, end) = (0, 0)
        for token in tokenized:
            end = start + len(token)
            if re.findall(r':?//+', buffer):
                for match in re.finditer('//', buffer):
                    self.text.tag_add('comment', '%s.%d' % (cline,
                            match.start()), '%s.%d' % (cline, end))
            elif token in keyword.kwlist:
                self.text.tag_add('kw', '%s.%d' % (cline, start),
                                  '%s.%d' % (cline, end))
            elif re.findall(r"['\"](.*?)['\"]", buffer):
                quoted = re.findall(r"['\"](.*?)['\"]", buffer,
                                    re.DOTALL)
                for t in quoted:
                    s = t
                    t = "'" + t + "'"
                    for match in re.finditer(t, buffer):
                        self.text.tag_add('str', '%s.%d' % (cline,
                                match.start()), '%s.%d' % (cline,
                                match.end()))
                    s = '"' + s + '"'
                    for match in re.finditer(s, buffer):
                        self.text.tag_add('str', '%s.%d' % (cline,
                                match.start()), '%s.%d' % (cline,
                                match.end()))
            else:
                for index in range(len(token)):
                    try:
                        int(token[index])
                    except ValueError:
                        pass
                    else:
                        self.text.tag_add('int', '%s.%d' % (cline,
                                start + index))

            start += len(token) + 1

    def getLineNumbers(self):

        x = 0
        line = '0'
        col = ''
        ln = ''

        # assume each line is at least 6 pixels high

        step = 6

        nl = '\n'
        lineMask = '    %s\n'
        indexMask = '@0,%d'

        for i in range(0, self.text.winfo_height(), step):

            (ll, cc) = self.text.index(indexMask % i).split('.')

            # Get Line and Column number

            (texty, textx) = self.text.index(INSERT).split('.')

            # text = int(texty)+1

            status.set('Line %s, Column %s' % (texty, textx))

            if line == ll:
                if col != cc:
                    col = cc
                    ln += nl
            else:
                (line, col) = (ll, cc)
                ln += (lineMask % line)[-6:]

        return ln

    def select_all(self, event):
        self.text.tag_add(SEL, '1.0', END)
        self.text.focus_set()
        return 'break'

    # def hilight(self,event):
        # print "!"

    def save_file(self, event):
        global current_file
        save = self.text.get('1.0', END)
        file = codecs.open(current_file, 'w', 'utf-8')
        file.write(save)
        file.close()

    def save_file_menu(self):
        global current_file
        save = self.text.get('1.0', END)
        file = codecs.open(current_file, 'w', 'utf-8')
        file.write(save)
        file.close()

    def updateLineNumbers(self):

        tt = self.lnText
        ln = self.getLineNumbers()
        if self.lineNumbers != ln:
            self.lineNumbers = ln
            tt.config(state='normal')
            tt.delete('1.0', END)
            tt.insert('1.0', self.lineNumbers)
            tt.config(state='disabled')

    @classmethod
    def updateAllLineNumbers(cls):

        if len(cls.editors) < 1:
            cls.updateId = None
            return

        for ed in cls.editors:
            ed.updateLineNumbers()

        cls.updateId = ed.text.after(cls.UPDATE_PERIOD,
                cls.updateAllLineNumbers)

    def onExit(self):
        root.quit()


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start + len(needle))
        n -= 1
    return start


def about():
    tkMessageBox.showinfo('PyLime', 'Raster Ron (c) 2014 - 2015\rgithub.com/rasteron')


def demo(
    noOfEditors,
    noOfLines,
    fileName,
    reload=None,
    empty=None,
    ):
    global pane2, bottom, separator, current_file, menubar, filemenu

    if empty:
        reload = True

    if reload:
        pane2.pack_forget()
        pane2.destroy()
        bottom.pack_forget()
        bottom.destroy()
        separator.pack_forget()
        separator.destroy()

    menubar = Menu(root)

    if os.path.isfile(fileName):
        current_file = os.path.abspath(fileName)

    # create a pulldown menu, and add it to the menu bar

    aboutmenu = Menu(menubar, tearoff=0)
    aboutmenu.add_command(label='About', command=about)

    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label='New', command=new_file,
                         accelerator='Ctrl+N')
    filemenu.add_command(label='Open', command=load_file,
                         accelerator='Ctrl+O')

    # filemenu.add_command(label="Save",command=save_file)

    filemenu.add_separator()

    menubar.add_cascade(label='File', menu=filemenu)

    menubar.add_cascade(label='Edit')
    menubar.add_cascade(label='Selection')
    menubar.add_cascade(label='Help', menu=aboutmenu)

    root.config(menu=menubar)

    pane2 = PanedWindow(root, orient=VERTICAL, opaqueresize=True,
                        sashpad=0, bd=0)
    pane2.pack(fill='both', expand=1)

    for e in range(noOfEditors):
        ed = EditorClass(root)
        pane2.add(ed.frame)

    s = ''
    subtitle = ''

    try:
        if os.path.isfile(fileName):
            fp = open(fileName)
            subtitle = os.path.abspath(fileName) + ' - '
            while 1:
                line = fp.readline()
                if not line:
                    break
                s = s + line
            fp.close()
    except IOError:
        print 'Error'
        s = ''

    for ed in EditorClass.editors:
        ed.text.insert(END, s)
        ed.text.focus_set()
        ed.text.mark_set(INSERT, 1.0)

    separator = Frame(height=1, bd=0, relief=SUNKEN,
                      background='#7e7e7e')
    separator.pack(fill=X, padx=0, pady=0)

    status.set('1')
    bottom = StatusBar(root)

    root.title('%sPyLime' % subtitle)
    root.configure(background='#404040')


def new_file():
    demo(1, 99, '', 1)


def load_file():
    fname = tkFileDialog.askopenfilename(filetypes=(('Text File',
            '*.txt'), ('AngelScript File', '*.as'), ('XML Files',
            '*.xml'), ('All files', '*.*')))
    if fname:
        try:

            if os.path.isfile(fname):
                demo(1, 99, fname, 1)
        except ValueError:

            print 'Error'.sys.exc_info()[0]
        return


if __name__ == '__main__':

    status = tk.StringVar()
    demo(1, 10, 'default.py')

    mainloop()

			