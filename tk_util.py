import tkinter as tk


def set_dpi_awareness():
    """ Enables DPI Awareness on Windows. Ignores any errors. """

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass


NS = tk.N + tk.S
NW = tk.N + tk.W
NE = tk.N + tk.E
SW = tk.S + tk.W
SE = tk.S + tk.E
EW = tk.E + tk.W

NSW = tk.N + tk.S + tk.W
NSE = tk.N + tk.S + tk.E
NEW = tk.N + tk.E + tk.W
SEW = tk.S + tk.E + tk.W

NSEW = tk.N + tk.S + tk.E + tk.W
