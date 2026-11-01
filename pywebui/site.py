# -*- coding: utf-8 -*-
"""Where the page comes from: a dev server, a local build, or a deployed site."""

from __future__ import print_function, division

import os

from pywebui.compat import List, Optional, Union
from pywebui.webview.session import PackagedContent, RemoteContent


class Mode(object):
    """How the page is served."""

    DEV = "dev"
    LOCAL = "local"
    SERVER = "server"


class Site(object):
    """One page and the origins that may call the host for it.

    ``DEV`` loads ``dev_url``. ``SERVER`` loads ``server_url``. ``LOCAL`` loads the
    build in ``dist_dir``: WebView2 maps it to ``local_host``, and the HTTP
    transport serves it itself, so the page and the API share one origin.
    """

    def __init__(
        self, mode, dev_url=None, server_url=None, dist_dir=None, local_host="pywebui.local"
    ):
        # type: (str, Optional[str], Optional[str], Optional[str], str) -> None
        if mode not in (Mode.DEV, Mode.LOCAL, Mode.SERVER):
            raise ValueError("mode must be Mode.DEV, Mode.LOCAL or Mode.SERVER, got {0!r}".format(mode))
        self.mode = mode
        self.dev_url = dev_url  # type: Optional[str]
        self.server_url = server_url  # type: Optional[str]
        self.dist_dir = dist_dir  # type: Optional[str]
        self.local_host = local_host  # type: str
        if self.mode == Mode.DEV and not dev_url:
            raise ValueError("dev mode needs dev_url")
        if self.mode == Mode.SERVER and not server_url:
            raise ValueError("server mode needs server_url")
        if self.mode == Mode.LOCAL and not (
            dist_dir and os.path.isfile(os.path.join(dist_dir, "index.html"))
        ):
            raise IOError(
                "local mode needs a built page: {0} has no index.html".format(dist_dir)
            )

    @property
    def dev(self):
        # type: () -> bool
        return self.mode == Mode.DEV

    @property
    def static_dir(self):
        # type: () -> Optional[str]
        """Folder the HTTP transport serves at ``/``. ``None`` unless ``LOCAL``."""
        return self.dist_dir if self.mode == Mode.LOCAL else None

    @property
    def origins(self):
        # type: () -> List[str]
        """Origins other than the host's own that may call it."""
        if self.mode == Mode.DEV:
            return [_origin(self.dev_url)]
        if self.mode == Mode.SERVER:
            return [_origin(self.server_url)]
        return []

    def webview_content(self):
        # type: () -> Union[RemoteContent, PackagedContent]
        if self.mode == Mode.DEV:
            return RemoteContent(self.dev_url)
        if self.mode == Mode.SERVER:
            return RemoteContent(self.server_url)
        return PackagedContent(
            "https://{0}/index.html".format(self.local_host), self.dist_dir
        )

    def browser_url(self, port, token, host="127.0.0.1"):
        # type: (int, str, str) -> str
        """URL for the browser. The port and token tell the page which host to call."""
        if self.mode == Mode.LOCAL:
            base = "http://{}:{}/".format(host, port)
        else:
            base = (self.dev_url if self.mode == Mode.DEV else self.server_url).rstrip("/") + "/"
        return "{}?port={}#token={}".format(base, port, token)


def _origin(url):
    # type: (str) -> str
    return "/".join(url.split("/")[:3])
