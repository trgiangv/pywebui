# API reference

Prefer **subpackages** over dumping everything on the root.

| Package | Role |
|---------|------|
| `pyrevit_webview` | `Bindable`, `bridge_callable`, `MessageRouter`, command envelope |
| `pyrevit_webview.host` | `WebViewControl`, `WebViewSession`, content. No UI toolkit and no host app |
| `pyrevit_webview.host.wpf` | WPF `WebView2`, `wpf_invoke`, `wpf_when_ready` |
| `pyrevit_webview.host.winforms` | WinForms `WebView2`, `winforms_invoke`, `winforms_when_ready` |
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
)
from pyrevit_webview.host.wpf import WebView2, wpf_invoke, wpf_when_ready

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
    when_ready=wpf_when_ready(webview),
)
```

## Command envelope

Used when the host owns named commands. `@bridge_callable` keeps the `invoke` / `bridge-response` protocol.

| Symbol | Notes |
|--------|-------|
| `parse_request(raw_json)` | `{command, id, payload}`, or `None` when the message is not a request |
| `response_message(command, id, payload=None, error=None)` | `{type: "response", command, id, payload\|error}` |
| `event_message(command, payload)` | `{type: "event", command, payload}` |

```python
from pyrevit_webview import event_message, parse_request, response_message
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
| `wpf_invoke` / `winforms_invoke` | UI-thread marshal. Import from `host.wpf` or `host.winforms` |
| `wpf_when_ready` / `winforms_when_ready` | Runs browser startup after the control has a handle |

## Revit adapter

| Symbol | Notes |
|--------|-------|
| `initialize_revit_task(app)` | Once on Revit main thread |
| `revit_invoke_sync(action)` | Revit API from bridge handler; inline if already on main |

## Logging

```python
from pyrevit_webview.log import get_logger
```
