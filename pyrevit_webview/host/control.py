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

from pyrevit_webview.compat import Callable, Dict, List, Optional, Type
from pyrevit_webview.loader import load_clr_types
from pyrevit_webview.log import debug_trace
from pyrevit_webview.serialize import JsonValue, serialize

load_clr_types()

from Microsoft.Web.WebView2.Core import (
    CoreWebView2,
    CoreWebView2EnvironmentOptions,
    CoreWebView2InitializationCompletedEventArgs,
    CoreWebView2NavigationCompletedEventArgs,
    CoreWebView2NavigationStartingEventArgs,
    CoreWebView2WebMessageReceivedEventArgs,
)
from pyrevit_webview.loader import (
    Action,
    CoreWebView2Environment,
    CoreWebView2HostResourceAccessKind,
)
from pyrevit_webview.host.session import (
    PackagedContent,
    RemoteContent,
    WebViewSession,
)
from pyrevit_webview.host.invoke import UiThread

_UNIQUE_WINDOW_CLASS_ARGUMENT = "--edge-webview-unique-window-class"

OnBrowserReady = Callable[["WebViewControl"], None]
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

    The caller supplies the framework WebView2 and a ``WpfUi`` or ``WinFormsUi``.
    This type does not import either UI stack.

    Lifecycle: construct → CoreWebView2 ready → register bindings → navigate → dispose.
    """

    def __init__(
        self,
        webview,
        session,
        bindings,
        ui,
        on_browser_ready=None,
        on_web_message=None,
    ):
        self._webview = webview
        self._session = session  # type: WebViewSession
        self._bindings = list(bindings)  # type: List[Bindable]
        self._ui = ui  # type: UiThread
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
        self._begin_startup()
        debug_trace("WebViewControl.__init__", "startup scheduled")

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
        # type: (Dict[str, JsonValue]) -> None
        """Post a JSON object with ``PostWebMessageAsJson`` on the UI thread."""
        raw = serialize(message)

        def send():
            # type: () -> None
            if not self.is_available:
                return
            try:
                self._webview.CoreWebView2.PostWebMessageAsJson(raw)
            except Exception as exc:
                self._session.logger.warning("PostWebMessageAsJson failed: %s", exc)

        self._ui.post(send)

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

        self._ui.post(dispose_browser)

    def __enter__(self):
        # type: () -> WebViewControl
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
        self.dispose()

    def _begin_startup(self):
        # type: () -> None
        _log_session(self._session)
        self._on_init_completed = self._on_core_init_completed
        self._webview.CoreWebView2InitializationCompleted += self._on_init_completed  # pyright: ignore[reportOperatorIssue]
        self._cancel_ready = self._ui.after_hosted(self._start_environment)

    def _start_environment(self):
        # type: () -> None
        if self._disposed:
            return

        debug_trace("WebViewControl._start_environment", "begin")
        user_data = ensure_user_data_folder(self._session.user_data_folder)
        options = self._environment_options()
        self._session.logger.info("Creating WebView2 environment...")
        env_task = CoreWebView2Environment.CreateAsync(None, user_data, options)

        def on_environment_created():
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

                self._ui.post(ensure_core)
                self._session.logger.info(
                    "WebView2 environment ready, initializing core..."
                )
            except Exception as exc:
                debug_trace("CreateAsync.OnCompleted", "FAILED: {0}".format(exc))
                self._session.logger.exception("WebView2 env failed: %s", exc)

        env_task.GetAwaiter().OnCompleted(Action(on_environment_created))
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
            self._configure_core(self._webview.CoreWebView2)
            debug_trace("InitCompleted", "done")
        except Exception as exc:
            debug_trace("InitCompleted", "FAILED: {0!r}".format(exc))
            self._session.logger.exception("InitCompleted failed: %s", exc)
            raise

    def _environment_options(self):
        # type: () -> CoreWebView2EnvironmentOptions
        options = CoreWebView2EnvironmentOptions()
        extra = self._session.browser_arguments()
        parts = [_UNIQUE_WINDOW_CLASS_ARGUMENT]
        if extra:
            parts.append(extra)
        options.AdditionalBrowserArguments = " ".join(parts)
        return options

    def _configure_core(self, core):
        # type: (CoreWebView2) -> None
        debug_trace("InitCompleted", "configure_settings")
        self._session.settings.apply(core.Settings)
        self._core_ready = True

        debug_trace("InitCompleted", "register_message_bindings")
        self._bind_messages(core)
        self._on_navigation_starting = self._log_navigation_starting
        self._on_navigation_completed = self._log_navigation_completed
        core.NavigationStarting += self._on_navigation_starting  # pyright: ignore[reportOperatorIssue]
        core.NavigationCompleted += self._on_navigation_completed  # pyright: ignore[reportOperatorIssue]

        start_url = self._start_url(core)
        self._session.logger.info("Navigating to %s", start_url)
        debug_trace("InitCompleted", "Navigate {0}".format(start_url))
        core.Navigate(start_url)

        if self._on_browser_ready is not None:
            debug_trace("InitCompleted", "on_browser_ready")
            self._on_browser_ready(self)

    def _bind_messages(self, core):
        # type: (CoreWebView2) -> None
        if self._message_callback is not None:
            callback = self._message_callback

            def on_message(_sender, event_args):
                # type: (CoreWebView2, CoreWebView2WebMessageReceivedEventArgs) -> None
                callback(event_args.WebMessageAsJson)

            self._on_web_message_received = on_message
            core.WebMessageReceived += on_message  # pyright: ignore[reportOperatorIssue]
            return

        router = MessageRouter(core, self._ui.post)
        self._router = router
        register_message_bindings(self._bindings, router)

        def on_router_message(_sender, event_args):
            # type: (CoreWebView2, CoreWebView2WebMessageReceivedEventArgs) -> None
            router.handle_raw(event_args.WebMessageAsJson)

        self._on_web_message_received = on_router_message
        core.WebMessageReceived += on_router_message  # pyright: ignore[reportOperatorIssue]

    def _start_url(self, core):
        # type: (CoreWebView2) -> str
        content = self._session.content
        if isinstance(content, RemoteContent):
            return content.start_url

        packaged = content  # type: PackagedContent
        folder = packaged.resolved_root()
        if not os.path.isdir(folder):
            self._session.logger.error("Packaged content root not found: %s", folder)

        self._session.logger.info(
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

    def _log_navigation_starting(self, _sender, args):
        # type: (CoreWebView2, CoreWebView2NavigationStartingEventArgs) -> None
        self._session.logger.info("NavigationStarting: %s", args.Uri)

    def _log_navigation_completed(self, _sender, args):
        # type: (CoreWebView2, CoreWebView2NavigationCompletedEventArgs) -> None
        if args.IsSuccess:
            self._session.logger.info("NavigationCompleted successfully")
            return
        self._session.logger.error("NavigationFailed: WebErrorStatus=%s", args.WebErrorStatus)


def _log_core_init_failure(session, args):
    # type: (WebViewSession, CoreWebView2InitializationCompletedEventArgs) -> None
    err = args.InitializationException
    if err is not None:
        msg = err.Message
        session.logger.error("CoreWebView2 init failed: %s", msg)
        return
    session.logger.error("CoreWebView2 init failed: unknown error")


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


