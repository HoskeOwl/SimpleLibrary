#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os.path
import tkinter

from tkinter import Tk, ttk, filedialog, StringVar, messagebox
from memory_storage import LIBRARY
from os import path as os_path

from fs_routines import parse_inpx, extract_books


class Application:
    def __init__(self, parent: Tk):
        self.parent = parent
        mainframe = ttk.Frame(parent, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))

        button_frame = ttk.Frame(mainframe, padding="3 3 5 5")
        button_frame.grid(column=0, row=0, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
        ttk.Button(button_frame, text="Открыть", command=self.open).grid(column=0, row=0, sticky=tkinter.W, padx=5)
        ttk.Button(button_frame, text="Экспорт", command=self.export).grid(column=1, row=0, sticky=tkinter.E, padx=5)

        self.status = StringVar()
        self.status.set("Откройте файл")
        ttk.Label(mainframe, textvariable=self.status).grid(column=0, row=1, columnspan=4,
                                                            sticky=(tkinter.W, tkinter.E))
        self.entry_choice_val = StringVar()
        entry = ttk.Entry(mainframe, textvariable=self.entry_choice_val)
        entry.grid(column=0, row=2, sticky=(tkinter.W, tkinter.E))
        entry.bind('<Return>', self.enter)

        # choise
        treeview_choice_frame = ttk.Frame(mainframe, padding="3 3 5 5")
        treeview_choice_frame.grid(column=0, row=3, columnspan=1, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
        self.treeview_choice = ttk.Treeview(treeview_choice_frame)
        self.treeview_choice.grid(column=0, row=0, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
        ysb = ttk.Scrollbar(treeview_choice_frame, orient=tkinter.VERTICAL, command=self.treeview_choice.yview)
        ysb.grid(column=1, row=0, sticky=(tkinter.N, tkinter.S))
        self.treeview_choice.configure(yscrollcommand=ysb.set)
        self.treeview_choice.bind("<<TreeviewSelect>>", self.selected_author)

        # result
        treeview_result_frame = ttk.Frame(mainframe, padding="3 3 5 5")
        treeview_result_frame.grid(column=1, row=3, columnspan=4, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
        self.treeview_result = ttk.Treeview(treeview_result_frame)
        self.treeview_result.grid(column=0, row=0, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
        ysb = ttk.Scrollbar(treeview_result_frame, orient=tkinter.VERTICAL, command=self.treeview_result.yview)
        ysb.grid(column=1, row=0, sticky=(tkinter.N, tkinter.S))
        self.treeview_result.configure(yscrollcommand=ysb.set)

        mainframe.rowconfigure(3, weight=1)
        mainframe.columnconfigure(0, weight=1)
        mainframe.columnconfigure(1, weight=1)
        mainframe.columnconfigure(2, weight=1)
        mainframe.columnconfigure(3, weight=1)
        treeview_choice_frame.rowconfigure(0, weight=1)
        treeview_choice_frame.columnconfigure(0, weight=1)
        treeview_result_frame.rowconfigure(0, weight=1)
        treeview_result_frame.columnconfigure(0, weight=1)
        self.mf = mainframe

    def progress_cb(self, value: int):
        self.status.set(f'Прогресс: {value}%')
        self.parent.update()

    def open(self):
        filename = filedialog.askopenfilename(filetypes=(("inpx files", "*.inpx"),))
        filename = os_path.realpath(filename)
        if filename and os.path.isfile(filename):
            ba, bg = parse_inpx(filename, self.progress_cb)
            LIBRARY.merge_by_autors(ba)
            LIBRARY.merge_by_genres(bg)
            self.status.set(f'Открыт файл: {filename}')

    def enter(self, event):
        self.treeview_choice.delete(*self.treeview_choice.get_children())
        self.treeview_result.delete(*self.treeview_result.get_children())
        authors = LIBRARY.get_authors(self.entry_choice_val.get().lower())
        for a in sorted(authors):
            self.treeview_choice.insert('', 'end', a, text=a.title())

    def selected_author(self, event):
        items = self.treeview_choice.selection()  # iid
        if len(items) == 1:
            self.treeview_result.delete(*self.treeview_result.get_children())
            books = LIBRARY.get_by_author(items[0])
            books.sort(key=lambda e: e.title)
            if books is None:
                return
            for book in books:
                try:
                    self.treeview_result.insert('', 'end', f'{book.uuid}', text=book.view_title)
                except tkinter.TclError as exc:
                    print(exc)

    def export(self):
        destination = filedialog.askdirectory()
        if not destination:
            return
        items = self.treeview_result.selection()  # iid
        if items:
            error = extract_books(items, destination)
            if error:
                messagebox.showerror(f"Can't extract", '\n'.join(error))
                self.status.set(f'Экспорт завершен с ошибками: {destination}')
            else:
                self.status.set(f'Экспорт завершен: {destination}')


def _run_form():
    root = Tk()
    root.title("Проверка inpx файла")
    root.geometry("1024x768")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    Application(root)
    root.mainloop()


if __name__ == '__main__':
    _run_form()
