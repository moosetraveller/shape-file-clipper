import tkinter as tk
from tkinter import ttk

import shape_file_clipper


class ShapeFileSelector(ttk.Frame):
    # label
    # list with scrollbar
    # add button
    # remove button
    # file chooser
    pass


class ClipExtendSelector(ttk.Frame):
    # label
    # text field (read only)
    # select button
    # file chooser
    pass


class OutputPathSelector(ttk.Frame):
    # label
    # text field (read only)
    # select button?
    # file chooser?
    pass


class ProjectionSelector(ttk.Frame):
    # label
    # number field (read only?)
    # find button
    # dialog with list to select from?
    pass


class OutputFileNamePostfixSelector(ttk.Frame):
    # label
    # text field
    pass


class ButtonBar(ttk.Frame):
    # execute button
    # close button
    pass


class ShapeFileClipperFrame(ttk.Frame):
    def __init__(self,container):
        super().__init__(container)