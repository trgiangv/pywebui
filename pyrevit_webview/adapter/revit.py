# -*- coding: utf-8 -*-
"""Revit main-thread gate.

Callers use :class:`RevitContext`. ``RevitTask`` stays inside this module.
``Thread.ManagedThreadId`` is a ``System.Threading.Thread`` property on
.NET Framework 4.8 and on .NET 8.
"""

from __future__ import print_function, division

from pyrevit_webview.compat import TYPE_CHECKING, Callable, List, Optional, TypeVar, cast
from pyrevit_webview.loader import load_bin
from pyrevit_webview.log import debug_trace, get_logger

if TYPE_CHECKING:
    from Autodesk.Revit import ApplicationServices, DB, UI
    from Autodesk.Revit.UI import UIApplication
    from UIFramework import MainWindow

_R = TypeVar("_R")


class RevitContext(object):
    """Schedule work on the Revit main thread.

    ``post`` always raises a new external event and returns. ``invoke``
    waits for the result. The Revit UI thread of a modeless window shares
    ``ManagedThreadId`` with the API thread and is still outside an API
    context, so ``invoke`` does not run inline there.
    """

    def __init__(self):
        # type: () -> None
        self._main_thread_id = None  # type: Optional[int]
        self._depth = 0  # type: int
        self._application = None  # type: Optional[UIApplication]

    def initialize(self, application):
        # type: (UIApplication) -> None
        """Record the main thread and initialize Revit.Async.

        Pass the ``UIApplication``.
        """
        load_bin()
        from System.Threading import Thread
        from Revit.Async import RevitTask

        self._main_thread_id = Thread.CurrentThread.ManagedThreadId
        self._application = application
        RevitTask.Initialize(application)
        debug_trace(
            "RevitContext.initialize",
            "main_thread_id={0}".format(self._main_thread_id),
        )

    @property
    def uiapp(self):
        # type: () -> UIApplication
        """The ``UIApplication`` passed to :meth:`initialize`.

        Kept here so later calls do not need the application passed again.
        """
        if self._application is None:
            raise RuntimeError("RevitContext.initialize has not been called")
        return self._application

    @property
    def app(self):
        # type: () -> ApplicationServices.Application
        """``Autodesk.Revit.ApplicationServices.Application``."""
        return self.uiapp.Application

    @property
    def uidoc(self):
        # type: () -> Optional[UI.UIDocument]
        """Active ``UI.UIDocument``. Read it at call time: the active document changes."""
        return self.uiapp.ActiveUIDocument

    @property
    def doc(self):
        # type: () -> Optional[DB.Document]
        """Active ``Document``. Read it at call time, do not cache it."""
        return self.uidoc.Document if self.uidoc is not None else None

    @property
    def version(self):
        # type: () -> str
        """Revit version number, for example ``"2025"``."""
        return self.app.VersionNumber

    @property
    def main_window(self):
        # type: () -> MainWindow
        """Revit main window (a WPF ``Window``), for ``window.Owner``."""
        import clr

        clr.AddReference("UIFramework")
        from UIFramework import MainWindow

        return MainWindow.getMainWnd()

    def post(self, action):
        # type: (Callable[[], None]) -> None
        """Queue ``action`` on a new external event and return.

        Safe from the WebView callback. Also safe from inside a running
        action: the next event starts after this handler returns.
        """
        load_bin()
        from System import Func
        from Revit.Async import RevitTask

        def run():
            # type: () -> None
            self._depth += 1
            try:
                action()
            except Exception as exc:
                get_logger().error("RevitContext.post failed: %s", exc)
            finally:
                self._depth -= 1
            return None

        debug_trace("RevitContext.post", "schedule")
        RevitTask.RunAsync[object](Func[object](run))

    def invoke(self, action):
        # type: (Callable[[], _R]) -> _R
        """Run ``action`` inside an external event and return its result.

        Inline only while this gate's own event is already executing.
        On the Revit UI thread outside that event, waiting would deadlock
        and running inline would leave the API context.
        """
        load_bin()
        if self._depth > 0 and self._on_main_thread():
            debug_trace("RevitContext.invoke", "inline (inside external event)")
            return action()
        if self._on_main_thread():
            raise RuntimeError(
                "RevitContext.invoke is on the Revit UI thread outside an external event. Use post."
            )

        from System import Func
        from Revit.Async import RevitTask

        debug_trace("RevitContext.invoke", "marshal")
        result_box = [None]  # type: List[Optional[_R]]
        error_box = [None]  # type: List[Optional[BaseException]]

        def run():
            # type: () -> None
            debug_trace("RevitContext.invoke.run", "on main")
            self._depth += 1
            try:
                result_box[0] = action()
            except Exception as exc:
                error_box[0] = exc
            finally:
                self._depth -= 1
            return None

        # RunAsync(Action) is a method group on the stub and is not callable there.
        # The generic Func overload is the one the stub types, and its Task completes
        # only after the delegate returns. The Python result stays in result_box so it
        # does not have to cross the CLR boundary.
        RevitTask.RunAsync[object](Func[object](run)).GetAwaiter().GetResult()
        if error_box[0] is not None:
            raise error_box[0]
        return cast(_R, result_box[0])

    def _on_main_thread(self):
        # type: () -> bool
        from System.Threading import Thread

        return (
            self._main_thread_id is not None
            and Thread.CurrentThread.ManagedThreadId == self._main_thread_id
        )


REVIT_CONTEXT = RevitContext()
