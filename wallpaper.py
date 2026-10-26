#!/usr/bin/env python3
"""WebKitGTK pond wallpaper for Cinnamon X11 (no external browser)."""
import os
import signal
import sys
from pathlib import Path

if os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland':
    sys.exit('Questo avvio supporta Cinnamon su X11. Sessione Wayland rilevata.')

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    gi.require_version('GdkX11', '3.0')
    try:
        gi.require_version('WebKit2', '4.1')
    except ValueError:
        gi.require_version('WebKit2', '4.0')
    from gi.repository import Gtk, Gdk, GdkX11, GLib, WebKit2
    from Xlib import X, display as xdisplay, error
    from Xlib.protocol import event
except (ImportError, ValueError) as exc:
    sys.exit(f'Dipendenze mancanti: {exc}\nServono python3-gi, python3-xlib, gir1.2-gtk-3.0 e gir1.2-webkit2-4.1 (oppure -4.0).')

base = Path(__file__).resolve().parent
if not (base / 'pond.js').is_file():
    sys.exit('Manca pond.js. Esegui prima ./setup.sh')

class PondWindow(Gtk.Window):
    def __init__(self, monitor, related_view=None):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title(f'DaoHo Pond Desktop — {monitor.get_model()}')
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_accept_focus(False)
        self.set_focus_on_map(False)
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_keep_below(True)
        self.stick()
        geo = monitor.get_geometry()
        self.move(geo.x, geo.y)
        self.set_default_size(geo.width, geo.height)
        self.set_resizable(False)
        self.loaded = False
        self.active = True
        self.last_pointer = None
        area = monitor.get_workarea()
        self.workarea = (area.x, area.y, area.x + area.width, area.y + area.height)
        self.web = (WebKit2.WebView.new_with_related_view(related_view)
                    if related_view is not None else WebKit2.WebView())
        self.web.set_can_focus(False)
        self.web.connect('load-changed', self.on_load)
        self.add(self.web)
        self.show_all()
        self.web.load_uri((base / 'index.html').as_uri())

    def on_load(self, _web, load_event):
        self.loaded = load_event == WebKit2.LoadEvent.FINISHED


class PondDesktop:
    def __init__(self):
        self.display = Gdk.Display.get_default()
        self.x11 = xdisplay.Display()
        self.root = self.x11.screen().root
        self.stacking_atom = self.x11.intern_atom('_NET_CLIENT_LIST_STACKING')
        self.restack_atom = self.x11.intern_atom('_NET_RESTACK_WINDOW')
        self.atoms = {name: self.x11.intern_atom(name) for name in (
            '_NET_WM_STATE', '_NET_WM_STATE_HIDDEN', '_NET_WM_DESKTOP',
            '_NET_CURRENT_DESKTOP', '_NET_WM_WINDOW_TYPE', '_NET_WM_WINDOW_TYPE_DESKTOP',
            '_NET_WM_WINDOW_TYPE_DOCK', '_NET_WM_OPAQUE_REGION', '_NET_WM_WINDOW_OPACITY',
            '_NET_FRAME_EXTENTS')}
        self.scale = Gdk.get_default_root_window().get_scale_factor()
        self.windows = []
        self.left_down = False
        self.refresh_monitors()
        Gdk.Screen.get_default().connect('monitors-changed', self.refresh_monitors)
        GLib.timeout_add(1000, self.keep_below_icons)
        GLib.timeout_add(125, self.poll_pointer)

    def refresh_monitors(self, *_args):
        for window in self.windows:
            window.destroy()
        self.windows = []
        for i in range(self.display.get_n_monitors()):
            related = self.windows[0].web if self.windows else None
            self.windows.append(PondWindow(self.display.get_monitor(i), related))

    def property(self, window, name):
        prop = window.get_full_property(self.atoms[name], X.AnyPropertyType)
        return list(prop.value) if prop is not None else []

    def opaque_rect(self, wid, workspace):
        window = self.x11.create_resource_object('window', wid)
        if window.get_attributes().map_state != X.IsViewable:
            return None
        if self.atoms['_NET_WM_STATE_HIDDEN'] in self.property(window, '_NET_WM_STATE'):
            return None
        types = self.property(window, '_NET_WM_WINDOW_TYPE')
        if any(self.atoms[name] in types for name in (
                '_NET_WM_WINDOW_TYPE_DESKTOP', '_NET_WM_WINDOW_TYPE_DOCK')):
            return None
        desktops = self.property(window, '_NET_WM_DESKTOP')
        if desktops and desktops[0] not in (workspace, 0xffffffff):
            return None
        opacity = self.property(window, '_NET_WM_WINDOW_OPACITY')
        if opacity and opacity[0] != 0xffffffff:
            return None
        geo = window.get_geometry()
        regions = self.property(window, '_NET_WM_OPAQUE_REGION')
        rectangles = zip(regions[0::4], regions[1::4], regions[2::4], regions[3::4])
        if geo.depth != 24 and not any(
                x <= 0 and y <= 0 and x + w >= geo.width and y + h >= geo.height
                for x, y, w, h in rectangles):
            return None
        origin = self.root.translate_coords(window, 0, 0)
        left, right, top, bottom = self.property(window, '_NET_FRAME_EXTENTS') or [0] * 4
        return ((origin.x - left) / self.scale, (origin.y - top) / self.scale,
                (origin.x + geo.width + right) / self.scale,
                (origin.y + geo.height + bottom) / self.scale)

    def update_activity(self, covers):
        for window in self.windows:
            if not window.loaded:
                continue
            x0, y0, x1, y1 = window.workarea
            # shortcut: require one opaque covering window; keep animating for partial coverage.
            active = not any(a <= x0 and b <= y0 and c >= x1 and d >= y1
                             for a, b, c, d in covers)
            if active != window.active:
                window.active = active
                window.last_pointer = None
                window.web.run_javascript(f'window.pondSetActive({str(active).lower()});',
                                          None, None, None)

    def keep_below_icons(self):
        prop = self.root.get_full_property(self.stacking_atom, X.AnyPropertyType)
        if prop is None:
            return True
        stacking = list(prop.value)
        icons = []
        covers = []
        workspace = self.property(self.root, '_NET_CURRENT_DESKTOP')
        for wid in stacking:
            try:
                wm_class = self.x11.create_resource_object('window', wid).get_wm_class()
                if wm_class and 'nemo-desktop' in wm_class:
                    icons.append(wid)
                rect = self.opaque_rect(wid, workspace[0] if workspace else 0)
                if rect is not None:
                    covers.append(rect)
            except error.BadWindow:
                continue
        if icons:
            sibling = icons[0]
            for window in self.windows:
                wid = window.get_window().get_xid()
                if wid in stacking and stacking.index(wid) > stacking.index(sibling):
                    # Muffin accepts pager restacks; GTK's initial lower races mapping.
                    message = event.ClientMessage(window=wid, client_type=self.restack_atom,
                                                  data=(32, [2, sibling, X.Below, 0, 0]))
                    self.root.send_event(message, event_mask=X.SubstructureRedirectMask |
                                         X.SubstructureNotifyMask)
            self.x11.flush()
        self.update_activity(covers)
        return True

    def poll_pointer(self):
        pointer = self.display.get_default_seat().get_pointer()
        _, x, y, mask = Gdk.get_default_root_window().get_device_position(pointer)
        left_down = bool(mask & Gdk.ModifierType.BUTTON1_MASK)
        feed = left_down and not self.left_down and bool(mask & Gdk.ModifierType.MOD1_MASK)
        self.left_down = left_down
        for window in self.windows:
            if not window.loaded or not window.active:
                continue
            _, x0, y0 = window.get_window().get_origin()
            local = (x - x0, y - y0)
            if not (0 <= local[0] < window.get_allocated_width() and
                    0 <= local[1] < window.get_allocated_height()):
                local = (-1, -1)
            if local == window.last_pointer and not feed:
                continue
            window.last_pointer = local
            js = ('window.pondExternalPointer&&window.pondExternalPointer'
                  f'({local[0]},{local[1]},{str(feed).lower()});')
            window.web.run_javascript(js, None, None, None)
        return True


if __name__ == '__main__':
    desktop = PondDesktop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signum, Gtk.main_quit)
    Gtk.main()
    desktop.x11.close()
