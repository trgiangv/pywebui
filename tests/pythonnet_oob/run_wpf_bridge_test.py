# -*- coding: utf-8 -*-
"""Out-of-process pythonnet WPF + WebView2 bridge latency harness (no Revit).

Why this exists
---------------
In-Revit CPython logs showed:
  - GetGreeting handler finishes quickly
  - GetDocumentInfo stalls on RevitTask while UI drains ExecuteScript
  - Parallel RunMethod workers pile up (race / head-of-line blocking)

This script isolates the bridge (postMessage ↔ MessageRouter ↔ bridge-response)
on a dedicated STA WPF thread with pythonnet — no Revit.Async.

Prereqs
-------
- Windows + WebView2 Runtime
- pythonnet installed into the interpreter you use
- ``pyrevit_webview/bin/`` populated via ``scripts/sync-bin.ps1``

Run
---
:: from repo root
  py -3 -m pip install pythonnet
  ./scripts/sync-bin.ps1
  py -3 tests/pythonnet_oob/run_wpf_bridge_test.py

Optional env:
  PYREVIT_WEBVIEW_TRACE=1   (default on via log.TRACE_ENABLED)
  OOB_AUTO_CLOSE=1          close window after AUTO_DONE (default 1)
  OOB_TIMEOUT_SEC=120
"""

from __future__ import print_function, division

import os
import sys
import time
import traceback


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _prepare_sys_path():
    root = _repo_root()
    if root not in sys.path:
        sys.path.insert(0, root)


def _add_wpf_references(clr_module):
    # type: (object) -> None
    """Load WPF assemblies by path — bare names fail under some pythonnet/netfx setups."""
    import os

    candidates = [
        os.path.join(
            os.environ.get("WINDIR", r"C:\Windows"),
            "Microsoft.NET",
            "Framework64",
            "v4.0.30319",
            "WPF",
        ),
        os.path.join(
            os.environ.get("WINDIR", r"C:\Windows"),
            "Microsoft.NET",
            "Framework",
            "v4.0.30319",
            "WPF",
        ),
    ]
    wpf_dir = None
    for path in candidates:
        if os.path.isdir(path):
            wpf_dir = path
            break
    if wpf_dir is None:
        raise IOError("WPF framework folder not found under %WINDIR%\\Microsoft.NET")

    for name in ("WindowsBase", "PresentationCore", "PresentationFramework"):
        dll = os.path.join(wpf_dir, name + ".dll")
        clr_module.AddReference(dll)


def _run_sta():
    _prepare_sys_path()

    # WPF requires .NET Framework. pythonnet 3 defaults to CoreCLR without WPF.
    try:
        from pythonnet import load as pythonnet_load

        pythonnet_load("netfx")
    except Exception:
        # Already loaded, or older pythonnet that binds netfx by default.
        pass

    import clr  # noqa: F401

    _add_wpf_references(clr)

    from System import Action
    from System.Threading import ManualResetEventSlim
    from System.Windows import Application, Window, WindowStartupLocation
    from System.Windows.Threading import DispatcherTimer
    from System import TimeSpan

    from pyrevit_webview import Bindable, bridge_callable
    from pyrevit_webview.host import (
        PackagedContent,
        WebViewControl,
        WebViewSession,
        WebViewSettings,
        wpf_invoke,
    )
    from pyrevit_webview.host.wpf import WebView2
    from pyrevit_webview.log import debug_trace

    ui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
    start_uri = "https://oob.bridge.local/index.html"
    done_event = ManualResetEventSlim(False)
    result_box = {"status": "timeout", "error": None}
    auto_close = os.environ.get("OOB_AUTO_CLOSE", "1").strip() not in ("0", "false", "False")

    class DemoBinding(Bindable):
        name = "demo"

        def __init__(self, window):
            self._window = window
            self._t0 = time.perf_counter()

        @bridge_callable("Ping")
        def ping(self, n):
            # Pure CPU / no UI — measures bridge overhead only.
            return {
                "pong": n,
                "python": sys.version.split()[0],
                "thread": _clr_thread_id(),
                "uptime_ms": int((time.perf_counter() - self._t0) * 1000),
            }

        @bridge_callable("Echo")
        def echo(self, text, number):
            return {"text": text, "number": number}

        @bridge_callable("Log")
        def log(self, message):
            print("[ui] {0}".format(message))
            sys.stdout.flush()
            return True

        @bridge_callable("NotifyDone")
        def notify_done(self, status):
            result_box["status"] = str(status)
            debug_trace("OOB.NotifyDone", status)
            print("[oob] NotifyDone: {0}".format(status))
            sys.stdout.flush()
            if auto_close:
                def close():
                    try:
                        self._window.Close()
                    finally:
                        done_event.Set()

                self._window.Dispatcher.BeginInvoke(Action(close))
            else:
                done_event.Set()
            return True

        @bridge_callable("SetTitle")
        def set_title(self, title):
            # UI touch — must marshal; measures Dispatcher cost without Revit.
            window = self._window
            text = str(title)
            box = {"ok": False, "error": None}

            def work():
                try:
                    window.Title = text
                    box["ok"] = True
                except Exception as exc:
                    box["error"] = exc

            dispatcher = window.Dispatcher
            if dispatcher.CheckAccess():
                work()
            else:
                dispatcher.Invoke(Action(work))
            if box["error"] is not None:
                raise box["error"]
            return box["ok"]

    class TestWindow(Window):
        def __init__(self):
            Window.__init__(self)
            self.Title = "pythonnet OOB bridge test"
            self.Width = 900
            self.Height = 640
            self.WindowStartupLocation = WindowStartupLocation.CenterScreen

            self._webview = WebView2()
            self.Content = self._webview

            session = WebViewSession(
                content=PackagedContent(start_uri=start_uri, content_root=ui_dir),
                app_name="pyrevit-webview-oob",
                settings=WebViewSettings(
                    dev_tools_enabled=True,
                    built_in_error_page_enabled=True,
                ),
            )
            self._control = WebViewControl(
                self._webview,
                session,
                bindings=[DemoBinding(self)],
                invoke_on_ui=wpf_invoke(self),
            )
            self.Closed += self._on_closed

        def _on_closed(self, sender, args):
            try:
                self._control.dispose()
            finally:
                done_event.Set()

    def boot():
        debug_trace("OOB.boot", "creating window")
        win = TestWindow()
        win.Show()

        # Failsafe timeout
        timeout_sec = float(os.environ.get("OOB_TIMEOUT_SEC", "120"))
        timer = DispatcherTimer()
        timer.Interval = TimeSpan.FromSeconds(timeout_sec)

        def on_timeout(sender, args):
            result_box["status"] = "timeout"
            print("[oob] TIMEOUT after {0}s".format(timeout_sec))
            sys.stdout.flush()
            try:
                win.Close()
            except Exception:
                done_event.Set()

        timer.Tick += on_timeout
        timer.Start()

    app = Application()
    app.Startup += lambda *_: boot()
    app.Run()
    return result_box["status"]


def _clr_thread_id():
    try:
        from System.Threading import Thread

        return Thread.CurrentThread.ManagedThreadId
    except Exception:
        return -1


def main():
    try:
        from pythonnet import load as pythonnet_load

        pythonnet_load("netfx")
    except Exception:
        pass

    import clr  # noqa: F401
    from System.Threading import ApartmentState, Thread, ThreadStart

    box = {"status": "error", "exc": None}

    def entry():
        try:
            box["status"] = _run_sta()
        except Exception as exc:
            box["exc"] = exc
            traceback.print_exc()
            box["status"] = "error"

    t = Thread(ThreadStart(entry))
    t.SetApartmentState(ApartmentState.STA)
    t.Start()
    t.Join()

    if box["exc"] is not None:
        print("[oob] FAILED: {0!r}".format(box["exc"]))
        return 1
    status = box["status"]
    print("[oob] finished status={0}".format(status))
    if status == "ok":
        return 0
    return 2


if __name__ == "__main__":
    # Allow ``py -3 path/to/run_wpf_bridge_test.py`` without installing package.
    raise SystemExit(main())
