# -*- coding: utf-8 -*-
"""WebView2 control - OOP host wiring with bindings and dispose."""

from __future__ import division, print_function

import io
import os
import shutil

from pyrevit_webview.bridge.binding import Bindable
from pyrevit_webview.bridge.message_bindings import register_message_bindings
from pyrevit_webview.bridge.message_router import MessageRouter
from types import TracebackType

from pyrevit_webview.compat import Callable, List, Optional
from pyrevit_webview.dotnet import bootstrap_clr
from pyrevit_webview.log import debug_trace
from pyrevit_webview.serialize import serialize

bootstrap_clr()

from Microsoft.Web.WebView2.Core import (
    CoreWebView2,
    CoreWebView2EnvironmentOptions,
    CoreWebView2InitializationCompletedEventArgs,
    CoreWebView2NavigationCompletedEventArgs,
    CoreWebView2NavigationStartingEventArgs,
    CoreWebView2WebMessageReceivedEventArgs,
)
from pyrevit_webview.dotnet import (
    Action,
    CoreWebView2Environment,
    CoreWebView2HostResourceAccessKind,
)
from pyrevit_webview.host.session import (
    PackagedContent,
    RemoteContent,
    WebViewSession,
    WebViewSettings,
)
from pyrevit_webview.types import InvokeOnUi

_UNIQUE_WINDOW_CLASS_ARGUMENT = "--edge-webview-unique-window-class"

OnBrowserReady = Callable[["WebViewControl"], None]
WhenReady = Callable[[Callable[[], None]], Callable[[], None]]
WebMessageHandler = Callable[
    [CoreWebView2, CoreWebView2WebMessageReceivedEventArgs], None
]
NavigationStartingHandler = Callable[
    [CoreWebView2, CoreWebView2NavigationStartingEventArgs], None
]
NavigationCompletedHandler = Callable[
    [CoreWebView2, CoreWebView2NavigationCompletedEventArgs], None
]


class WebViewControl(object):
    """Wire WebView2 async init, bindings, and navigation into a user-owned control.

    The caller supplies the framework WebView2 and a ``when_ready`` scheduler
    from ``host.wpf`` or ``host.winforms``. This type does not import either UI stack.

    Lifecycle: construct → CoreWebView2 ready → register bindings → navigate → dispose.
    """

    def __init__(
        self,
        webview,
        session,
        bindings,
        invoke_on_ui,
        when_ready,
        on_browser_ready=None,
        on_web_message=None,
    ):
        self._webview = webview
        self._session = session  # type: WebViewSession
        self._bindings = list(bindings)  # type: List[Bindable]
        self._invoke_on_ui = invoke_on_ui  # type: InvokeOnUi
        self._when_ready = when_ready  # type: WhenReady
        self._cancel_ready = None  # type: Optional[Callable[[], None]]
        self._on_browser_ready = on_browser_ready  # type: Optional[OnBrowserReady]
        self._message_callback = on_web_message  # type: Optional[Callable[[str], None]]
        self._disposed = False  # type: bool
        self._router = None  # type: Optional[MessageRouter]
        self._on_init_completed = None
        self._core_ready = False  # type: bool
        self._on_web_message_received = None  # type: Optional[WebMessageHandler]
        self._on_navigation_starting = None  # type: Optional[NavigationStartingHandler]
        self._on_navigation_completed = None  # type: Optional[NavigationCompletedHandler]
        debug_trace("WebViewControl.__init__", "begin")
        self._wire()
        debug_trace("WebViewControl.__init__", "wired")

    @property
    def webview(self):
        return self._webview

    @property
    def session(self):
        # type: () -> WebViewSession
        return self._session

    @property
    def router(self):
        # type: () -> Optional[MessageRouter]
        return self._router

    @property
    def is_disposed(self):
        # type: () -> bool
        return self._disposed

    @property
    def is_available(self):
        # type: () -> bool
        return (not self._disposed) and self._core_ready

    @property
    def is_browser_initialized(self):
        # type: () -> bool
        return self._core_ready

    def show_devtools(self):
        # type: () -> None
        if self.is_available:
            self._webview.CoreWebView2.OpenDevToolsWindow()

    def execute_script(self, script):
        # type: (str) -> None
        if self.is_available:
            self._webview.CoreWebView2.ExecuteScriptAsync(script)

    def post_json(self, message):
        # type: (dict) -> None
        """Post a JSON object with ``PostWebMessageAsJson`` on the UI thread."""
        raw = serialize(message)

        def send():
            # type: () -> None
            if not self.is_available:
                return
            try:
                self._webview.CoreWebView2.PostWebMessageAsJson(raw)
            except Exception as exc:
                print("[WebView] PostWebMessageAsJson failed: {0}".format(exc))
                self._session.logger.warning("PostWebMessageAsJson failed: %s", exc)

        self._invoke_on_ui(send)

    def dispose(self):
        # type: () -> None
        if self._disposed:
            return
        self._disposed = True
        self._core_ready = False
        self._session.logger.info("Disposing WebViewControl")
        self._router = None

        if self._cancel_ready is not None:
            self._cancel_ready()
            self._cancel_ready = None

        core = self._webview.CoreWebView2
        if core is not None:
            if self._on_web_message_received is not None:
                core.WebMessageReceived -= self._on_web_message_received  # pyright: ignore[reportOperatorIssue]
            if self._on_navigation_starting is not None:
                core.NavigationStarting -= self._on_navigation_starting  # pyright: ignore[reportOperatorIssue]
            if self._on_navigation_completed is not None:
                # CLR event -= is valid. The stub types the sender as Any, so it
                # does not match NavigationCompletedHandler.
                core.NavigationCompleted -= self._on_navigation_completed  # pyright: ignore[reportOperatorIssue]
        self._on_web_message_received = None
        self._on_navigation_starting = None
        self._on_navigation_completed = None

        if self._on_init_completed is not None:
            self._webview.CoreWebView2InitializationCompleted -= self._on_init_completed  # pyright: ignore[reportOperatorIssue]
            self._on_init_completed = None

        def dispose_browser():
            # type: () -> None
            try:
                self._webview.Dispose()
            except Exception as exc:
                self._session.logger.warning(
                    "Error disposing WebView2 browser: %s", exc
                )

        self._invoke_on_ui(dispose_browser)

    def __enter__(self):
        # type: () -> WebViewControl
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # type: (Optional[type], Optional[BaseException], Optional[TracebackType]) -> None
        self.dispose()

    def _wire(self):
        # type: () -> None
        _log_session(self._session)
        self._on_init_completed = self._on_core_init_completed
        self._webview.CoreWebView2InitializationCompleted += self._on_init_completed  # pyright: ignore[reportOperatorIssue]
        self._cancel_ready = self._when_ready(self._start_environment)

    def _start_environment(self):
        # type: () -> None
        if self._disposed:
            return

        debug_trace("WebViewControl._start_environment", "begin")
        user_data = ensure_user_data_folder(self._session.user_data_folder)
        options = _create_environment_options(self._session)
        self._session.logger.info("Creating WebView2 environment...")
        env_task = CoreWebView2Environment.CreateAsync(None, user_data, options)

        def check_task():
            # type: () -> None
            debug_trace(
                "CreateAsync.OnCompleted",
                "IsCompleted={0}".format(env_task.IsCompleted),
            )
            if not env_task.IsCompleted:
                return
            try:
                env = env_task.Result

                def ensure_core():
                    # type: () -> None
                    debug_trace("EnsureCoreWebView2Async", "on UI invoke")
                    self._webview.EnsureCoreWebView2Async(env)

                self._invoke_on_ui(ensure_core)
                self._session.logger.info(
                    "WebView2 environment ready, initializing core..."
                )
            except Exception as exc:
                debug_trace("CreateAsync.OnCompleted", "FAILED: {0}".format(exc))
                self._session.logger.exception("WebView2 env failed: %s", exc)
                print("WebView2 env failed: {0}".format(exc))

        env_task.GetAwaiter().OnCompleted(Action(check_task))
        debug_trace("WebViewControl._start_environment", "OnCompleted registered")

    def _on_core_init_completed(self, sender, args):
        debug_trace(
            "CoreWebView2InitializationCompleted",
            "IsSuccess={0}".format(getattr(args, "IsSuccess", "?")),
        )
        if self._disposed:
            return
        if not args.IsSuccess:
            _log_core_init_failure(self._session, args)
            return

        self._session.logger.info("CoreWebView2 ready, configuring settings...")
        try:
            _configure_initialized_core(self, self._webview.CoreWebView2)
            debug_trace("InitCompleted", "done")
        except Exception as exc:
            debug_trace("InitCompleted", "FAILED: {0!r}".format(exc))
            self._session.logger.exception("InitCompleted failed: %s", exc)
            print("InitCompleted failed: {0}".format(exc))
            raise


def _log_core_init_failure(session, args):
    # type: (WebViewSession, CoreWebView2InitializationCompletedEventArgs) -> None
    err = args.InitializationException
    if err is not None:
        msg = err.Message
        session.logger.error("CoreWebView2 init failed: %s", msg)
        print("CoreWebView2 init failed: {0}".format(msg))
        return
    session.logger.error("CoreWebView2 init failed: unknown error")
    print("CoreWebView2 init failed: unknown error")


def _bind_web_message(control, core):
    # type: (WebViewControl, CoreWebView2) -> None
    if control._message_callback is not None:
        callback = control._message_callback

        def on_message(_sender, event_args):
            # type: (CoreWebView2, CoreWebView2WebMessageReceivedEventArgs) -> None
            callback(event_args.WebMessageAsJson)

        control._on_web_message_received = on_message
        core.WebMessageReceived += on_message  # pyright: ignore[reportOperatorIssue]
        return

    router = MessageRouter(core, control._invoke_on_ui)
    control._router = router
    register_message_bindings(control._bindings, router)

    def on_router_message(_sender, event_args):
        # type: (CoreWebView2, CoreWebView2WebMessageReceivedEventArgs) -> None
        router.handle_raw(event_args.WebMessageAsJson)

    control._on_web_message_received = on_router_message
    core.WebMessageReceived += on_router_message  # pyright: ignore[reportOperatorIssue]


def _configure_initialized_core(control, core):
    # type: (WebViewControl, CoreWebView2) -> None
    debug_trace("InitCompleted", "configure_settings")
    configure_settings(core, control._session.settings)

    control._core_ready = True

    debug_trace("InitCompleted", "register_message_bindings")
    _bind_web_message(control, core)
    control._on_navigation_starting = lambda _s, ea: _on_navigation_starting(
        control._session, ea
    )
    control._on_navigation_completed = lambda _s, ea: _on_navigation_completed(
        control._session, ea
    )
    core.NavigationStarting += control._on_navigation_starting  # pyright: ignore[reportOperatorIssue]
    core.NavigationCompleted += control._on_navigation_completed  # pyright: ignore[reportOperatorIssue]

    start_url = _resolve_start_url(control._session, core)
    control._session.logger.info("Navigating to %s", start_url)
    debug_trace("InitCompleted", "Navigate {0}".format(start_url))
    core.Navigate(start_url)

    if control._on_browser_ready is not None:
        debug_trace("InitCompleted", "on_browser_ready")
        control._on_browser_ready(control)


def configure_settings(core, settings):
    # type: (CoreWebView2, WebViewSettings) -> None
    s = core.Settings
    s.IsScriptEnabled = settings.script_enabled
    s.IsWebMessageEnabled = settings.web_message_enabled
    s.AreDevToolsEnabled = settings.dev_tools_enabled
    s.AreDefaultContextMenusEnabled = settings.context_menus_enabled
    s.IsZoomControlEnabled = settings.zoom_control_enabled
    s.IsPinchZoomEnabled = settings.pinch_zoom_enabled
    s.IsBuiltInErrorPageEnabled = settings.built_in_error_page_enabled


def ensure_user_data_folder(folder_path):
    # type: (str) -> str
    from pyrevit_webview.log import get_logger

    folder = os.path.abspath(os.path.expanduser(folder_path))
    if _is_user_data_folder_writable(folder):
        return folder

    get_logger().warning("User data folder locked, clearing: %s", folder)
    shutil.rmtree(folder, ignore_errors=True)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    return folder


def _is_user_data_folder_writable(folder):
    # type: (str) -> bool
    try:
        if not os.path.isdir(folder):
            os.makedirs(folder)
        probe = os.path.join(folder, ".lock_test")
        with io.open(probe, "w", encoding="utf-8") as handle:
            handle.write(u"ok")
        os.remove(probe)
        return True
    except (OSError, IOError):
        return False


def _log_session(session):
    # type: (WebViewSession) -> None
    content = session.content
    session.logger.info("UserDataFolder=%s", session.user_data_folder)
    if isinstance(content, RemoteContent):
        session.logger.info("Content=Remote StartUrl=%s", content.start_url)
    elif isinstance(content, PackagedContent):
        session.logger.info(
            "Content=Packaged StartUri=%s Root=%s",
            content.start_uri,
            content.content_root,
        )
    if session.debug_cdp_port:
        session.logger.info("CDP http://127.0.0.1:%s", session.debug_cdp_port)


def _create_environment_options(session):
    # type: (WebViewSession) -> CoreWebView2EnvironmentOptions
    options = CoreWebView2EnvironmentOptions()
    args = [_UNIQUE_WINDOW_CLASS_ARGUMENT]
    if session.additional_browser_arguments:
        args.append(session.additional_browser_arguments.strip())
    if session.debug_cdp_port:
        args.append("--remote-debugging-port={0}".format(session.debug_cdp_port))
    options.AdditionalBrowserArguments = " ".join(args)
    return options


def _resolve_start_url(session, core):
    # type: (WebViewSession, CoreWebView2) -> str
    content = session.content
    if isinstance(content, RemoteContent):
        return content.start_url

    packaged = content  # type: PackagedContent
    folder = packaged.resolved_root()
    if not os.path.isdir(folder):
        session.logger.error("Packaged content root not found: %s", folder)

    session.logger.info(
        "Virtual host '%s' -> '%s'",
        packaged.host_name(),
        folder,
    )
    core.SetVirtualHostNameToFolderMapping(
        packaged.host_name(),
        str(folder),
        CoreWebView2HostResourceAccessKind.Allow,
    )
    return packaged.start_uri


def _on_navigation_starting(session, ea):
    # type: (WebViewSession, CoreWebView2NavigationStartingEventArgs) -> None
    session.logger.info("NavigationStarting: %s", ea.Uri)


def _on_navigation_completed(session, ea):
    # type: (WebViewSession, CoreWebView2NavigationCompletedEventArgs) -> None
    if ea.IsSuccess:
        session.logger.info("NavigationCompleted successfully")
        return
    session.logger.error("NavigationFailed: WebErrorStatus=%s", ea.WebErrorStatus)
