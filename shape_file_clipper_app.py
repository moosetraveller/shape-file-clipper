import tkinter as tk
from tkinter import ttk, filedialog

import windows

import tk_util as tku
import shape_file_clipper


class ShapeFileClipperApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Shape File Clipper")
        self.geometry("950x400+100+100")

        self.main_frame = MainFrame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=1)
        
        self.resizable(False, False)


class MainFrame(ttk.Frame):

    def __init__(self, container):
        super().__init__(container)

        self.columnconfigure(0, weight=1)

        self.shape_file_selector = ShapeFileSelector(self)
        self.shape_file_selector.grid(row=0, column=0, padx=5, pady=5, sticky=tku.EW)

        self.clip_extent_selector = ClipExtentSelector(self)
        self.clip_extent_selector.grid(row=1, column=0, padx=5, pady=5, sticky=tku.EW)

        self.button_bar = ButtonBar(self)
        self.button_bar.grid(row=6, column=0, padx=5, pady=5, sticky=tku.EW)


class ShapeFileListFrame(ttk.Frame):

    def __init__(self, container):
        super().__init__(container)


class ShapeFileSelector(ttk.Frame):

    def __init__(self, container):
        super().__init__(container)

        self.list_frame = ShapeFileListFrame(self)

        self.scrollbar = ttk.Scrollbar(
            self.list_frame,
            orient=tk.VERTICAL
        )
        self.list = tk.Listbox(
            self.list_frame,
            width=90,
            height=3,
            yscrollcommand=self.scrollbar.set
        )
        self.scrollbar.config(command=self.list.yview)

        self.list.bind("<<ListboxSelect>>", lambda event: self.__on_list_changed())

        self.list.grid(row=0, column=0, sticky=tku.NSW)
        self.scrollbar.grid(row=0, column=1, sticky=tku.NS)

        self.button_frame = ttk.Frame(self)

        self.add_button = ttk.Button(
            self.button_frame,
            text="Add File",
            command=self.__add
        )
        self.add_button.pack(fill=tk.X, expand=1)
        self.remove_button = ttk.Button(
            self.button_frame,
            text="Remove",
            command=self.__remove
        )
        self.remove_button.pack(fill=tk.X, expand=1)

        self.label = ttk.Label(self, text="Shape Files")

        self.columnconfigure(0, weight=1)

        self.label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.list_frame.grid(row=1, column=0, padx=5, pady=5, sticky=tku.NSEW)
        self.button_frame.grid(row=1, column=1, padx=5, pady=5, sticky=tku.NEW)

        self.__on_list_changed()

    def __add(self):
        file_names = list(filedialog.askopenfilename(
            title="Select Shape Files",
            filetypes=(("Shape Files", "*.shp"), ("All Files", "*.*")),
            multiple=True
        ))
        file_names.sort()
        for file_name in file_names:
            self.list.insert(tk.END, file_name)
        self.__on_list_changed()

    def __remove(self):
        selection = self.list.curselection()
        if selection:
            self.list.delete(selection)
        self.__on_list_changed()

    def __on_list_changed(self):
        selection = self.list.curselection()
        remove_button_state = tk.NORMAL if selection else tk.DISABLED
        self.remove_button["state"] = remove_button_state

    def get_shape_files(self):
        return self.list.get(0, tk.END)


class ClipExtentSelector(ttk.Frame):

    def __init__(self, container):
        super().__init__(container)

        self.input_field_value = tk.StringVar()

        self.label = ttk.Label(self, text="Clip Extend")

        self.input_field = ttk.Entry(
            self,
            width=90,
            textvariable=self.input_field_value
        )
        self.input_field["state"] = tk.DISABLED

        self.select_button = ttk.Button(
            self,
            text="Select",
            command=self.__select
        )

        self.columnconfigure(0, weight=1)

        self.label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.input_field.grid(row=1, column=0, padx=5, pady=5, sticky=tku.NEW)
        self.select_button.grid(row=1, column=1, padx=5, pady=5, sticky=tku.NEW)

    def __select(self):
        file_name = filedialog.askopenfilename(
            title="Select Shape Files",
            filetypes=(("Shape Files", "*.shp"), ("All Files", "*.*")),
            multiple=False
        )
        self.input_field_value.set(file_name)

    def get_clip_extent(self):
        return self.input_field_value.get()


class OutputPathSelector(ttk.Frame):
    # label
    # text field (read only)
    # select button?
    # file chooser?

    def __init__(self, container):
        super().__init__(container)


class ProjectionSelector(ttk.Frame):
    # label
    # number field (read only?)
    # find button
    # dialog with list to select from?

    def __init__(self, container):
        super().__init__(container)


class OutputFileNamePostfixSelector(ttk.Frame):
    # label
    # text field

    def __init__(self, container):
        super().__init__(container)


class ButtonBar(ttk.Frame):
    # execute button
    # close button

    def __init__(self, container):
        super().__init__(container)

        self.execute_button = ttk.Button(self, text="Execute")
        self.execute_button.pack(side=tk.RIGHT)

        self.close_button = ttk.Button(self, text="Close")
        self.close_button.pack(side=tk.RIGHT)


def start():

    # set dpi awareness for windows high resolution screens
    windows.set_dpi_awareness()

    root = ShapeFileClipperApp()
    root.mainloop()


if __name__ == '__main__':
    start()
