# -*- coding: utf-8 -*-
"""Revit main-thread gate.

Callers use :class:`RevitContext`. ``RevitTask`` stays inside this module.
``Thread.ManagedThreadId`` is a ``System.Threading.Thread`` property on
.NET Framework 4.8 and on .NET 8.
"""

from __future__ import print_function, division

from pyrevit_webview.compat import TYPE_CHECKING, Callable, List, Optional, TypeVar, Union, cast
from pyrevit_webview.loader import load_bin
from pyrevit_webview.log import debug_trace, get_logger

if TYPE_CHECKING:
    from Autodesk.Revit.UI import UIApplication, UIControlledApplication

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

    def initialize(self, application):
        # type: (Union[UIApplication, UIControlledApplication]) -> None
        """Record the main thread and initialize Revit.Async.

        Pass ``UIControlledApplication`` or ``UIApplication`` (pyRevit: ``__revit__``).
        """
        load_bin()
        from System.Threading import Thread
        from Revit.Async import RevitTask

        self._main_thread_id = Thread.CurrentThread.ManagedThreadId
        RevitTask.Initialize(application)
        debug_trace(
            "RevitContext.initialize",
            "main_thread_id={0}".format(self._main_thread_id),
        )

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
