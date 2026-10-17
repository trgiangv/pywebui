# -*- coding: utf-8 -*-
"""WebView session, content sources, and settings."""

from __future__ import print_function, division

import logging
import os
import tempfile

from pyrevit_webview.compat import Optional, Union
from pyrevit_webview.log import get_logger


class WebViewSettings(object):
    """CoreWebView2.Settings mirror (production-safe defaults)."""

    def __init__(
        self,
        script_enabled=True,
        web_message_enabled=True,
        dev_tools_enabled=False,
        context_menus_enabled=False,
        zoom_control_enabled=False,
        pinch_zoom_enabled=False,
        built_in_error_page_enabled=False,
    ):
        # type: (bool, bool, bool, bool, bool, bool, bool) -> None
        self.script_enabled = script_enabled  # type: bool
        self.web_message_enabled = web_message_enabled  # type: bool
        self.dev_tools_enabled = dev_tools_enabled  # type: bool
        self.context_menus_enabled = context_menus_enabled  # type: bool
        self.zoom_control_enabled = zoom_control_enabled  # type: bool
        self.pinch_zoom_enabled = pinch_zoom_enabled  # type: bool
        self.built_in_error_page_enabled = built_in_error_page_enabled  # type: bool


class RemoteContent(object):
    """Dev server URL (Vite, etc.)."""

    def __init__(self, start_url):
        # type: (str) -> None
        self.start_url = start_url  # type: str


class PackagedContent(object):
    """Local assets via virtual host mapping (direct folder map, no copy)."""

    def __init__(self, start_uri, content_root):
        # type: (str, str) -> None
        self.start_uri = start_uri  # type: str
        self.content_root = content_root  # type: str

    def host_name(self):
        # type: () -> str
        return _uri_host(self.start_uri)

    def resolved_root(self):
        # type: () -> str
        return os.path.abspath(os.path.expanduser(self.content_root))


class WebViewSession(object):
    """Browser profile + content for :class:`WebViewControl`.

    ``user_data_folder`` defaults to ``%TEMP%/<app_name>`` — pass ``app_name``
    or override ``user_data_folder`` explicitly.
    """

    def __init__(
        self,
        content,
        user_data_folder=None,
        app_name="pyrevit_webview",
        debug_cdp_port=None,
        settings=None,
        logger=None,
        additional_browser_arguments=None,
    ):
        # type: (Union[RemoteContent, PackagedContent], Optional[str], str, Optional[int], Optional[WebViewSettings], Optional[logging.Logger], Optional[str]) -> None
        self.content = content  # type: Union[RemoteContent, PackagedContent]
        self.user_data_folder = user_data_folder or _default_user_data_folder(app_name)  # type: str
        self.debug_cdp_port = debug_cdp_port  # type: Optional[int]
        self.additional_browser_arguments = additional_browser_arguments or ""  # type: str
        self.settings = settings or WebViewSettings()  # type: WebViewSettings
        self.logger = logger or get_logger()  # type: logging.Logger


def _default_user_data_folder(name="pyrevit_webview"):
    # type: (str) -> str
    return os.path.join(tempfile.gettempdir(), name)


def _uri_host(uri):
    # type: (str) -> str
    if "://" in uri:
        rest = uri.split("://", 1)[1]
        return rest.split("/")[0]
    return uri.split("/")[0]
