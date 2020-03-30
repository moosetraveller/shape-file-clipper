import os
import threading

from abc import ABC, abstractmethod

import tkinter as tk
from tkinter import ttk, filedialog

import windows

import tk_util as tku
import shape_file_clipper as sfc


class Validator(ABC):
    @abstractmethod
    def validate(self):
        pass


class ShapeFileClipperApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.style = ttk.Style(self)
        self.style.configure("sfc.validation.TLabel", foreground="red")

        self.title("Shape File Clipper")
        self.geometry("+100+100")

        self.indicator = Indicator(self, height=400, width=950)
        self.main_frame = ShapeFileClipperAppFrame(self)

        self.button_bar = ttk.Frame(self)
        self.buttons = ttk.Frame(self.button_bar)

        self.execute_button = ttk.Button(
            self.buttons,
            text="Execute",
            command=self.execute
        )
        self.execute_button.pack(side=tk.RIGHT)

        self.close_button = ttk.Button(
            self.buttons,
            text="Close",
            command=self.close
        )
        self.close_button.pack(side=tk.RIGHT)

        self.progress_bar = ttk.Progressbar(self.buttons, orient=tk.HORIZONTAL, length=100, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, padx=50)

        self.buttons.pack(side=tk.RIGHT, padx=10, pady=10)

        self.indicator.grid(row=0, column=0, sticky=tku.NEW)
        self.main_frame.grid(row=0, column=0, sticky=tku.NEW)
        self.button_bar.grid(row=1, column=0, sticky=tku.EW)
        
        self.resizable(False, False)

    def execute(self):

        messages = self.main_frame.validate()
        if len(messages) > 0:
            return

        self.__show_indicator()
        self.execute_button["state"] = tk.DISABLED

        # run in separate thread
        threading.Thread(target=self.__execute).start()

    def __show_indicator(self):
        self.progress_bar.step(0)
        self.indicator.tkraise()

    def __hide_indicator(self):
        self.progress_bar.stop()
        self.main_frame.tkraise()

    def __execute(self):

        clip_extent = self.main_frame.clip_extent_selector.get()
        output_path = self.main_frame.output_path_selector.get()
        output_file_name_postfix = self.main_frame.output_file_name_postfix_selector.get()

        clipper = sfc.ShapeFileClipper(clip_extent, output_path, output_file_name_postfix)

        shape_files = self.main_frame.shape_file_selector.get()
        epsg_code = self.main_frame.projection_selector.get()

        for index, shape_file in enumerate(shape_files):
            if not epsg_code or len(epsg_code.strip()) == 0:
                clipper.clip(shape_file)
            else:
                clipper.clip_and_project(shape_file, epsg_code)
            self.progress_bar.step(100/len(shape_files))

        self.__hide_indicator()
        self.execute_button["state"] = tk.NORMAL

    def close(self):
        self.quit()


class Indicator(ttk.Frame):

    def __init__(self, container, **kwargs):
        super().__init__(container, **kwargs)


class ShapeFileClipperAppFrame(ttk.Frame):

    def __init__(self, root, **kwargs):
        super().__init__(root, **kwargs)

        self.input_frames = []

        self.columnconfigure(0, weight=1)

        self.input_frame = ttk.Frame(self, relief=tk.FLAT, borderwidth=1)
        self.input_frame.columnconfigure(0, weight=1)

        self.shape_file_selector = ShapeFileSelector(self.input_frame)
        self.input_frames.append(self.shape_file_selector)

        self.clip_extent_selector = ClipExtentSelector(self.input_frame)
        self.input_frames.append(self.clip_extent_selector)

        self.output_path_selector = OutputPathSelector(self.input_frame)
        self.input_frames.append(self.output_path_selector)

        self.projection_selector = ProjectionSelector(self.input_frame)
        self.input_frames.append(self.projection_selector)

        self.output_file_name_postfix_selector = OutputFileNamePostfixSelector(self.input_frame)
        self.input_frames.append(self.output_file_name_postfix_selector)

        self.shape_file_selector.grid(row=0, column=0, padx=5, pady=5, sticky=tku.EW)
        self.clip_extent_selector.grid(row=1, column=0, padx=5, pady=5, sticky=tku.EW)
        self.output_path_selector.grid(row=2, column=0, padx=5, pady=5, sticky=tku.EW)
        self.projection_selector.grid(row=3, column=0, padx=5, pady=5, sticky=tku.EW)
        self.output_file_name_postfix_selector.grid(row=4, column=0, padx=5, pady=5, sticky=tku.EW)

        self.input_frame.grid(row=1, column=0, padx=10, pady=10, sticky=tku.NSEW)

    def validate(self):
        messages = []
        for input_frame in self.input_frames:
            message = input_frame.validate()
            if message is not None:
                messages.append(message)
        return messages


class ShapeFileSelector(ttk.Frame, Validator):

    def __init__(self, container, **kwargs):
        super().__init__(container, **kwargs)

        self.list_frame = ttk.Frame(self)

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
        self.clear_button = ttk.Button(
            self.button_frame,
            text="Clear",
            command=self.__clear
        )
        self.clear_button.pack(fill=tk.X, expand=1)

        self.label = ttk.Label(self, text="Shape Files")

        self.validation_label_value = tk.StringVar()
        self.validation_label = ttk.Label(
            self,
            textvariable=self.validation_label_value,
            style="sfc.validation.TLabel"
        )

        self.columnconfigure(0, weight=1)

        self.label.grid(row=0, column=0, columnspan=2, padx=5, sticky=tk.W)
        self.list_frame.grid(row=1, column=0, padx=5, sticky=tku.NSW)
        self.button_frame.grid(row=1, column=1, padx=5, sticky=tku.NEW)
        self.validation_label.grid(row=2, column=0, columnspan=2, padx=5, sticky=tk.W)

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

    def __clear(self):
        self.list.delete(0, tk.END)
        self.__on_list_changed()

    def __on_list_changed(self):
        selection = self.list.curselection()
        remove_button_state = tk.NORMAL if selection else tk.DISABLED
        self.remove_button["state"] = remove_button_state

        clear_button_state = tk.NORMAL if len(self.get()) > 0 else tk.DISABLED
        self.clear_button["state"] = clear_button_state

    def get(self):
        return self.list.get(0, tk.END)

    def validate(self):
        if len(self.get()) > 0:
            self.validation_label_value.set("")
            return None
        message = "No shape file selected."
        self.validation_label_value.set(message)
        return message


class ClipExtentSelector(ttk.Frame, Validator):

    def __init__(self, container, **kwargs):
        super().__init__(container, **kwargs)

        self.input_field_value = tk.StringVar()

        self.label = ttk.Label(self, text="Clip Extend")

        self.input_field = ttk.Entry(
            self,
            width=90,
            textvariable=self.input_field_value
        )

        self.select_button = ttk.Button(
            self,
            text="Select",
            command=self.__select
        )

        self.validation_label_value = tk.StringVar()
        self.validation_label = ttk.Label(
            self,
            textvariable=self.validation_label_value,
            style="sfc.validation.TLabel"
        )

        self.columnconfigure(0, weight=1)

        self.label.grid(row=0, column=0, columnspan=2, padx=5, sticky=tk.W)
        self.input_field.grid(row=1, column=0, padx=5, sticky=tku.NW)
        self.select_button.grid(row=1, column=1, padx=5, sticky=tku.NEW)
        self.validation_label.grid(row=2, column=0, columnspan=2, padx=5, sticky=tk.W)

    def __select(self):
        file_name = filedialog.askopenfilename(
            title="Select Clip Extent",
            filetypes=(("Shape Files", "*.shp"), ("All Files", "*.*")),
            multiple=False
        )
        self.input_field_value.set(file_name)

    def get(self):
        return self.input_field_value.get()

    def validate(self):

        clip_extent = self.get()

        message = None

        if not clip_extent or len(clip_extent.strip()) == 0:
            message = "No clip extent selected."
        if not os.path.isfile(clip_extent):
            message = "Clip extent does not exist."

        self.validation_label_value.set(message if message is not None else "")
        return message


class OutputPathSelector(ttk.Frame, Validator):

    def __init__(self, container, **kwargs):
        super().__init__(container, **kwargs)

        self.input_field_value = tk.StringVar()

        self.label = ttk.Label(self, text="Output Directory")

        self.input_field = ttk.Entry(
            self,
            width=90,
            textvariable=self.input_field_value
        )

        self.select_button = ttk.Button(
            self,
            text="Select",
            command=self.__select
        )

        self.validation_label_value = tk.StringVar()
        self.validation_label = ttk.Label(
            self,
            textvariable=self.validation_label_value,
            style="sfc.validation.TLabel"
        )

        self.columnconfigure(0, weight=1)

        self.label.grid(row=0, column=0, columnspan=2, padx=5, sticky=tk.W)
        self.input_field.grid(row=1, column=0, padx=5, sticky=tku.NW)
        self.select_button.grid(row=1, column=1, padx=5, sticky=tku.NEW)
        self.validation_label.grid(row=2, column=0, columnspan=2, padx=5, sticky=tk.W)

    def __select(self):
        output_path_name = filedialog.askdirectory(title="Select Output Directory")
        print(output_path_name)
        self.input_field_value.set(output_path_name)

    def get(self):
        return self.input_field_value.get()

    def validate(self):

        output_path = self.get()

        message = None

        if not output_path or len(output_path.strip()) == 0:
            message = "No output directory selected."
        if not os.path.isdir(output_path):
            message = "Output directory does not exist."

        self.validation_label_value.set(message if message is not None else "")
        return message


class ProjectionSelector(ttk.Frame, Validator):

    def __init__(self, container, **kwargs):
        super().__init__(container, **kwargs)

        self.input_field_value = tk.StringVar()

        self.label = ttk.Label(self, text="Projection/EPSG Code (optional)")

        self.input_field = ttk.Entry(
            self,
            width=90,
            textvariable=self.input_field_value
        )

        self.select_button = ttk.Button(
            self,
            text="Find",
            command=self.__find
        )
        self.select_button["state"] = tk.DISABLED

        self.columnconfigure(0, weight=1)

        self.label.grid(row=0, column=0, columnspan=2, padx=5, sticky=tk.W)
        self.input_field.grid(row=1, column=0, padx=5, sticky=tku.NW)
        # self.select_button.grid(row=1, column=1, padx=5, sticky=tku.NEW)

    def __find(self):
        pass

    def get(self):
        return self.input_field_value.get()

    def validate(self):
        return None


class OutputFileNamePostfixSelector(ttk.Frame, Validator):

    def __init__(self, container, **kwargs):
        super().__init__(container, **kwargs)

        self.input_field_value = tk.StringVar()
        self.input_field_value.set("_clipped")

        self.label = ttk.Label(self, text="Output File Postfix")

        self.input_field = ttk.Entry(
            self,
            width=90,
            textvariable=self.input_field_value
        )

        self.columnconfigure(0, weight=1)

        self.label.grid(row=0, column=0, columnspan=2, padx=5, sticky=tk.W)
        self.input_field.grid(row=1, column=0, columnspan=1, padx=5, sticky=tku.NW)

    def get(self):
        return self.input_field_value.get()

    def validate(self):
        return None


def start():

    # set dpi awareness for windows high resolution screens
    windows.set_dpi_awareness()

    sfc.init_logging()

    root = ShapeFileClipperApp()
    root.mainloop()


if __name__ == '__main__':
    start()
