import os

import tkinter as tk
from tkinter import ttk, filedialog

import windows

import tk_util as tku
import shape_file_clipper as sfc


class ShapeFileClipperApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Shape File Clipper")
        self.geometry("980x400+100+100")

        self.main_frame = MainFrame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=1)
        
        self.resizable(False, False)


class MainFrame(ttk.Frame):

    def __init__(self, container):
        super().__init__(container)

        self.input_frames = []

        self.columnconfigure(0, weight=1)

        self.input_frame = ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        self.input_frame.columnconfigure(0, weight=1)

        self.shape_file_selector = ShapeFileSelector(self.input_frame)
        self.shape_file_selector.grid(row=0, column=0, padx=5, pady=5, sticky=tku.EW)
        self.input_frames.append(self.shape_file_selector)

        self.clip_extent_selector = ClipExtentSelector(self.input_frame)
        self.clip_extent_selector.grid(row=1, column=0, padx=5, pady=5, sticky=tku.EW)
        self.input_frames.append(self.clip_extent_selector)

        self.output_path_selector = OutputPathSelector(self.input_frame)
        self.output_path_selector.grid(row=2, column=0, padx=5, pady=5, sticky=tku.EW)
        self.input_frames.append(self.output_path_selector)

        self.projection_selector = ProjectionSelector(self.input_frame)
        self.projection_selector.grid(row=3, column=0, padx=5, pady=5, sticky=tku.EW)
        self.input_frames.append(self.projection_selector)

        self.output_file_name_postfix_selector = OutputFileNamePostfixSelector(self.input_frame)
        self.output_file_name_postfix_selector.grid(row=4, column=0, padx=5, pady=5, sticky=tku.EW)
        self.input_frames.append(self.output_file_name_postfix_selector)

        self.input_frame.grid(row=1, column=0, padx=10, pady=10, sticky=tku.NSEW)

        self.rowconfigure(2, weight=1)

        self.button_bar = ttk.Frame(self)

        self.execute_button = ttk.Button(
            self.button_bar,
            text="Execute",
            command=self.execute
        )
        self.execute_button.pack(side=tk.RIGHT)

        self.close_button = ttk.Button(self.button_bar, text="Close")
        self.close_button.pack(side=tk.RIGHT)

        self.button_bar.grid(row=2, column=0, padx=10, pady=10, sticky=tku.EW)

    def execute(self):

        for input_frame in self.input_frames:
            input_frame.validate()

        clip_extent = self.clip_extent_selector.get()
        output_path = self.output_path_selector.get()
        output_file_name_postfix = self.output_file_name_postfix_selector.get()

        clipper = sfc.ShapeFileClipper(clip_extent, output_path, output_file_name_postfix)

        shape_files = self.shape_file_selector.get()
        epsg_code = self.projection_selector.get()

        for shape_file in shape_files:
            if not epsg_code or len(epsg_code.strip()) == 0:
                clipper.clip(shape_file)
            else:
                clipper.clip_and_project(shape_file, epsg_code)


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

        self.label.grid(row=0, column=0, columnspan=2, padx=5, sticky=tk.W)
        self.list_frame.grid(row=1, column=0, padx=5, sticky=tku.NSW)
        self.button_frame.grid(row=1, column=1, padx=5, sticky=tku.NEW)

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

    def get(self):
        return self.list.get(0, tk.END)

    def validate(self):
        pass


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
        # self.input_field["state"] = tk.DISABLED

        self.select_button = ttk.Button(
            self,
            text="Select",
            command=self.__select
        )

        self.columnconfigure(0, weight=1)

        self.label.grid(row=0, column=0, columnspan=2, padx=5, sticky=tk.W)
        self.input_field.grid(row=1, column=0, padx=5, sticky=tku.NW)
        self.select_button.grid(row=1, column=1, padx=5, sticky=tku.NEW)

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
        if not clip_extent or len(clip_extent.strip()) == 0:
            return "No clip extent selected."
        if not os.path.isfile(clip_extent):
            return "Clip extent {} does not exist.".format(clip_extent)
        return None


class OutputPathSelector(ttk.Frame):

    def __init__(self, container):
        super().__init__(container)

        self.input_field_value = tk.StringVar()

        self.label = ttk.Label(self, text="Output Directory")

        self.input_field = ttk.Entry(
            self,
            width=90,
            textvariable=self.input_field_value
        )
        # self.input_field["state"] = tk.DISABLED

        self.select_button = ttk.Button(
            self,
            text="Select",
            command=self.__select
        )

        self.columnconfigure(0, weight=1)

        self.label.grid(row=0, column=0, columnspan=2, padx=5, sticky=tk.W)
        self.input_field.grid(row=1, column=0, padx=5, sticky=tku.NW)
        self.select_button.grid(row=1, column=1, padx=5, sticky=tku.NEW)

    def __select(self):
        output_path_name = filedialog.askdirectory(title="Select Output Directory")
        self.input_field_value.set(output_path_name)

    def get(self):
        return self.input_field_value.get()

    def validate(self):
        pass


class ProjectionSelector(ttk.Frame):

    def __init__(self, container):
        super().__init__(container)

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
        self.select_button.grid(row=1, column=1, padx=5, sticky=tku.NEW)

    def __find(self):
        pass

    def get(self):
        return self.input_field_value.get()

    def validate(self):
        pass


class OutputFileNamePostfixSelector(ttk.Frame):

    def __init__(self, container):
        super().__init__(container)

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
        pass


def start():

    # set dpi awareness for windows high resolution screens
    windows.set_dpi_awareness()

    root = ShapeFileClipperApp()
    root.mainloop()


if __name__ == '__main__':
    start()
