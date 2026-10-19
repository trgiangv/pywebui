# -*- coding: utf-8 -*-
"""UI thread of the window that owns the WebView2 control.

WPF: ``pyrevit_webview.host.wpf.WpfUi``.
WinForms: ``pyrevit_webview.host.winforms.WinFormsUi``.
"""

from __future__ import print_function, division

import threading

from pyrevit_webview.compat import Callable, List, Optional, TypeVar, cast
from pyrevit_webview.log import debug_trace

_R = TypeVar("_R")


class UiThread(object):
    """Posts work to the window thread and starts the browser once it can."""

    def post(self, action):
        # type: (Callable[[], None]) -> None
        """Queue ``action`` on the UI thread and return."""
        raise NotImplementedError

    def on_thread(self):
        # type: () -> bool
        """True when the caller is already on the UI thread."""
        raise NotImplementedError

    def call(self, action):
        # type: (Callable[[], _R]) -> _R
        """Run ``action`` on the UI thread and return its result.

        Runs inline when ``on_thread`` is already true.
        """
        if self.on_thread():
            return action()
        return _wait(self.post, action)

    def after_hosted(self, start):
        # type: (Callable[[], None]) -> Callable[[], None]
        """Run ``start`` once the control can create a browser.

        Returns a cancel function. WPF waits for ``Loaded``. WinForms waits
        for ``HandleCreated``.
        """
        raise NotImplementedError


def _wait(post, action):
    # type: (Callable[[Callable[[], None]], None], Callable[[], _R]) -> _R
    gate = threading.Event()
    result_box = [None]  # type: List[Optional[_R]]
    error_box = [None]  # type: List[Optional[BaseException]]

    def work():
        # type: () -> None
        debug_trace("UiThread.call", "running on UI")
        try:
            result_box[0] = action()
        except Exception as exc:
            debug_trace("UiThread.call", "error: {0!r}".format(exc))
            error_box[0] = exc
        finally:
            gate.set()

    debug_trace("UiThread.call", "post + wait")
    post(work)
    gate.wait()
    debug_trace("UiThread.call", "released error={0}".format(error_box[0] is not None))
    if error_box[0] is not None:
        raise error_box[0]
    return cast(_R, result_box[0])
