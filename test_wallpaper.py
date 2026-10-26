import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from Xlib import X, error
from wallpaper import PondDesktop


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.desktop = PondDesktop.__new__(PondDesktop)
        self.desktop.root = Mock()
        self.desktop.x11 = Mock()
        self.desktop.stacking_atom = 1
        self.desktop.restack_atom = 2
        self.desktop.windows = [Mock(), Mock()]
        self.desktop.property = Mock(return_value=[])
        self.desktop.opaque_rect = Mock(return_value=None)
        self.desktop.update_activity = Mock()
        for window, wid in zip(self.desktop.windows, (30, 40)):
            window.get_window.return_value.get_xid.return_value = wid
            window.active = True
            window.loaded = True
            window.last_pointer = None
            window.get_allocated_width.return_value = 1920
            window.get_allocated_height.return_value = 1080
        self.desktop.x11.create_resource_object.return_value.get_wm_class.return_value = None

    def test_wallpapers_go_below_lowest_icon_window(self):
        self.desktop.root.get_full_property.return_value = SimpleNamespace(value=[10, 20, 30, 40])
        self.desktop.x11.create_resource_object.side_effect = lambda _, wid: Mock(
            get_wm_class=lambda: ('nemo-desktop', 'Nemo-desktop') if wid in (10, 20) else None)
        self.desktop.keep_below_icons()
        messages = [call.args[0] for call in self.desktop.root.send_event.call_args_list]
        self.assertEqual([msg.window for msg in messages], [30, 40])
        for msg in messages:
            self.assertEqual(list(msg.data[1]), [2, 10, X.Below, 0, 0])

    def test_correct_stacking_is_left_alone(self):
        self.desktop.root.get_full_property.return_value = SimpleNamespace(value=[30, 40, 10])
        self.desktop.x11.create_resource_object.side_effect = lambda _, wid: Mock(
            get_wm_class=lambda: ('nemo-desktop', 'Nemo-desktop') if wid == 10 else None)
        self.desktop.keep_below_icons()
        self.desktop.root.send_event.assert_not_called()

    def test_closed_windows_do_not_break_stacking(self):
        self.desktop.root.get_full_property.return_value = SimpleNamespace(value=[10])
        self.desktop.x11.create_resource_object.return_value.get_wm_class.side_effect = (
            error.BadWindow.__new__(error.BadWindow))
        self.assertTrue(self.desktop.keep_below_icons())

    def test_creates_a_window_for_each_monitor(self):
        self.desktop.display = Mock()
        self.desktop.display.get_n_monitors.return_value = 2
        monitors = [Mock(), Mock()]
        self.desktop.display.get_monitor.side_effect = monitors
        with patch('wallpaper.PondWindow') as window:
            self.desktop.refresh_monitors()
        self.assertEqual([call.args[0] for call in window.call_args_list], monitors)

    def test_pointer_coordinates_and_single_feed_on_second_monitor(self):
        self.desktop.display = Mock()
        self.desktop.left_down = False
        for window, x in zip(self.desktop.windows, (0, 1920)):
            window.loaded = True
            window.get_window.return_value.get_origin.return_value = (1, x, 0)
        from wallpaper import Gdk
        root = Mock()
        root.get_device_position.return_value = (
            None, 2000, 90, Gdk.ModifierType.BUTTON1_MASK | Gdk.ModifierType.MOD1_MASK)
        with patch('wallpaper.Gdk.get_default_root_window', return_value=root):
            self.desktop.poll_pointer()
            self.desktop.poll_pointer()
        calls = self.desktop.windows[1].web.run_javascript.call_args_list
        self.assertIn('(80,90,true)', calls[0].args[0])
        self.assertEqual(len(calls), 1)

    def test_covered_monitor_pauses_and_resumes_independently(self):
        first, second = self.desktop.windows
        first.workarea = (0, 0, 1920, 1020)
        second.workarea = (1920, 0, 3840, 1160)
        PondDesktop.update_activity(self.desktop, [(0, 0, 1920, 1020)])
        self.assertFalse(first.active)
        self.assertTrue(second.active)
        self.assertIn('false', first.web.run_javascript.call_args.args[0])
        first.web.run_javascript.reset_mock()
        PondDesktop.update_activity(self.desktop, [(0, 0, 1920, 1020)])
        first.web.run_javascript.assert_not_called()
        PondDesktop.update_activity(self.desktop, [])
        self.assertTrue(first.active)
        self.assertIn('true', first.web.run_javascript.call_args.args[0])

    def test_partial_coverage_keeps_animation(self):
        for window in self.desktop.windows:
            window.workarea = (0, 0, 1920, 1020)
        PondDesktop.update_activity(self.desktop, [(0, 0, 1800, 1020)])
        for window in self.desktop.windows:
            self.assertTrue(window.active)
            window.web.run_javascript.assert_not_called()

    def opaque_window(self, **properties):
        self.desktop.atoms = {'_NET_WM_STATE_HIDDEN': 1, '_NET_WM_WINDOW_TYPE_DESKTOP': 2,
                              '_NET_WM_WINDOW_TYPE_DOCK': 3}
        self.desktop.scale = 1
        self.desktop.property.side_effect = lambda _w, name: properties.get(name, [])
        window = self.desktop.x11.create_resource_object.return_value
        window.get_attributes.return_value.map_state = X.IsViewable
        window.get_geometry.return_value = SimpleNamespace(width=1920, height=983, depth=32)
        self.desktop.root.translate_coords.return_value = SimpleNamespace(x=0, y=37)
        return PondDesktop.opaque_rect(self.desktop, 10, 0)

    def test_opaque_window_includes_titlebar(self):
        rect = self.opaque_window(_NET_WM_OPAQUE_REGION=[0, 0, 1920, 983],
                                  _NET_FRAME_EXTENTS=[0, 0, 37, 0])
        self.assertEqual(rect, (0, 0, 1920, 1020))

    def test_transparent_minimized_or_other_workspace_cannot_pause(self):
        for props in ({}, {'_NET_WM_STATE': [1]}, {'_NET_WM_DESKTOP': [5]},
                      {'_NET_WM_WINDOW_OPACITY': [0x7fffffff]},
                      {'_NET_WM_WINDOW_TYPE': [2]}):
            with self.subTest(props=props):
                self.assertIsNone(self.opaque_window(**props))


if __name__ == '__main__':
    unittest.main()
