#!/usr/bin/env python3
"""Embed the pond renderer in xwinwrap and forward X11 pointer state."""
import ctypes
import os
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit('Uso: wallpaper-x11.py <xwinwrap WID>')

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GLib, WebKit2

base = Path(__file__).resolve().parent
if not (base / 'pond.js').exists():
    sys.exit('Manca pond.js: esegui ./setup.sh')

# XQueryPointer reads the global cursor position without stealing Nemo's clicks.
x11 = ctypes.CDLL('libX11.so.6')
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
x11.XDefaultRootWindow.restype = ctypes.c_ulong
x11.XQueryPointer.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
    ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_uint)]
x11.XQueryPointer.restype = ctypes.c_int
xdpy = x11.XOpenDisplay(None)
if not xdpy:
    sys.exit('Impossibile aprire il display X11')
root = x11.XDefaultRootWindow(xdpy)

plug = Gtk.Plug.new(int(sys.argv[1], 0))
plug.set_title('Koi Pond Interactive')
web = WebKit2.WebView()
web.set_can_focus(False)
settings = web.get_settings()
settings.set_enable_javascript(True)
plug.add(web)
plug.show_all()
loaded = [False]
def ready(_web, event):
    if event == WebKit2.LoadEvent.FINISHED:
        loaded[0] = True
web.connect('load-changed', ready)
web.load_uri((base / 'index.html').as_uri())

# Poll the pointer; root coordinates translate to the embedded window's position.
prev_down = False
counter = 0

def poll():
    global prev_down, counter
    rw = ctypes.c_ulong()
    cw = ctypes.c_ulong()
    rx = ctypes.c_int()
    ry = ctypes.c_int()
    wx = ctypes.c_int()
    wy = ctypes.c_int()
    mask = ctypes.c_uint()
    if not x11.XQueryPointer(xdpy, root, ctypes.byref(rw), ctypes.byref(cw),
          ctypes.byref(rx), ctypes.byref(ry), ctypes.byref(wx), ctypes.byref(wy), ctypes.byref(mask)):
        return True
    if not loaded[0]:
        return True
    # Gdk geometry is in X11 root coordinates, also with multi-monitor offsets.
    window = plug.get_window()
    if window is None:
        return True
    x0, y0 = window.get_origin()
    x, y = rx.value - x0, ry.value - y0
    buttons = mask.value
    left_down = bool(buttons & (1 << 8))
    alt_down = bool(buttons & (1 << 3))  # Mod1Mask, usually Alt
    feed = left_down and not prev_down and alt_down
    prev_down = left_down
    # At most 30 calls/s; WebKit uses JS side to compute speed and feed.
    js = f'window.pondExternalPointer&&window.pondExternalPointer({x},{y},{str(feed).lower()});'
    web.run_javascript(js, None, None, None)
    return True

GLib.timeout_add(33, poll)
plug.connect('destroy', Gtk.main_quit)
Gtk.main()
