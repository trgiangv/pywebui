# API reference

Prefer **subpackages** over dumping everything on the root.

| Package | Role |
|---------|------|
| `pyrevit_webview` | `Bindable`, `bridge_callable`, `MessageRouter` |
| `pyrevit_webview.host` | `WebViewControl`, `WebViewSession`, content, `wpf_invoke` / `winforms_invoke` |
| `pyrevit_webview.host.wpf` | `WebView2` (loads `bin/` then CLR type) |
| `pyrevit_webview.host.winforms` | WinForms `WebView2` |
| `pyrevit_webview.adapter.revit` | `initialize_revit_task`, `revit_invoke_sync` |
| `pyrevit_webview.dotnet` | `load_bin` (usually not needed — use `host.wpf`) |

## Typical Revit script

```python
from pyrevit_webview import Bindable, bridge_callable
from pyrevit_webview.adapter.revit import initialize_revit_task, revit_invoke_sync
from pyrevit_webview.host import (
    PackagedContent,
    WebViewControl,
    WebViewSession,
    WebViewSettings,
    wpf_invoke,
)
from pyrevit_webview.host.wpf import WebView2

initialize_revit_task(__revit__)

session = WebViewSession(
    content=PackagedContent(start_uri=..., content_root=...),
    app_name="myapp",
    settings=WebViewSettings(dev_tools_enabled=True),
)

control = WebViewControl(
    WebView2(),
    session,
    bindings=[MyBinding()],
    invoke_on_ui=wpf_invoke(window),
)
```

## Binding

| Symbol | Package |
|--------|---------|
| `Bindable` | `pyrevit_webview` / `bridge.binding` |
| `@bridge_callable("Name")` | same |

## Host

| Symbol | Notes |
|--------|-------|
| `WebViewSession(content, app_name=..., user_data_folder=None, ...)` | Profile path defaults from `app_name` |
| `WebViewSettings(...)` | CoreWebView2 settings |
| `PackagedContent` / `RemoteContent` | Content source |
| `WebViewControl` | Init, postMessage router, navigate, dispose |
| `wpf_invoke` / `winforms_invoke` | UI-thread marshal for host callbacks |

## Revit adapter

| Symbol | Notes |
|--------|-------|
| `initialize_revit_task(app)` | Once on Revit main thread |
| `revit_invoke_sync(action)` | Revit API from bridge handler; inline if already on main |

## Logging

```python
from pyrevit_webview.log import get_logger
```
