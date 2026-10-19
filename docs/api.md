# API reference

Prefer **subpackages** over dumping everything on the root.

| Package | Role |
|---------|------|
| `pyrevit_webview` | `Bindable`, `bridge_callable`, `MessageRouter`, command envelope |
| `pyrevit_webview.host` | `WebViewControl`, `WebViewSession`, content. No UI toolkit and no host app |
| `pyrevit_webview.host.wpf` | WPF `WebView2`, `WpfUi` |
| `pyrevit_webview.host.winforms` | WinForms `WebView2`, `WinFormsUi` |
| `pyrevit_webview.adapter.revit` | `RevitContext`, `REVIT_CONTEXT` |
| `pyrevit_webview.loader` | `load_bin`, `load_clr_types` (usually not needed — use `host.wpf`) |
| `pyrevit_webview.serialize` | Newtonsoft `serialize` / `deserialize` |

## Typical Revit script

```python
from pyrevit_webview import Bindable, bridge_callable
from pyrevit_webview.adapter.revit import REVIT_CONTEXT
from pyrevit_webview.host import (
    PackagedContent,
    WebViewControl,
    WebViewSession,
    WebViewSettings,
)
from pyrevit_webview.host.wpf import WebView2, WpfUi

REVIT_CONTEXT.initialize(__revit__)

session = WebViewSession(
    content=PackagedContent(start_uri=..., content_root=...),
    app_name="myapp",
    settings=WebViewSettings(dev_tools_enabled=True),
)

webview = WebView2()
control = WebViewControl(
    webview,
    session,
    bindings=[MyBinding()],
    ui=WpfUi(window, webview),
)
```

## Command envelope

Used when the host owns named commands. `@bridge_callable` keeps the invoke protocol.

Wire names live in `pyrevit_webview.bridge.contract`. Each value is the JSON text, so it is a dict key and a comparison.

| Symbol | Wire |
|--------|------|
| `EnvelopeKind.REQUEST` / `RESPONSE` / `EVENT` | `"request"` / `"response"` / `"event"` |
| `EnvelopeField.TYPE` `COMMAND` `ID` `PAYLOAD` `ERROR` `OK` | those key names |
| `parse_request(raw_json)` | `CommandRequest` (`.command`, `.id`, `.payload`), or `None` |
| `response_message(command, id, payload=None, error=None)` | response object. Omitted payload becomes `{ok: true}` |
| `event_message(command, payload)` | event object, no id |

```python
from pyrevit_webview import (
    CommandRequest,
    EnvelopeField,
    EnvelopeKind,
    event_message,
    parse_request,
    response_message,
)

parsed = parse_request(raw_json)
if parsed is not None:
    reply = response_message(parsed.command, parsed.id, payload=parsed.payload)
```

## Invoke (`@bridge_callable`)

| Symbol | Wire |
|--------|------|
| `InvokeKind.INVOKE` | `"invoke"` |
| `InvokeField.TYPE` `ID` `METHOD` `PARAMS` | request keys |
| `InvokeField.OK` `DATA` `ERROR` | `bridge-response` detail keys |
| `EventName.BRIDGE_RESPONSE` | `"bridge-response"` (`RESPONSE_EVENT` is the same value) |

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
| `WpfUi` / `WinFormsUi` | `post` queues on the UI thread. `call` waits. `after_hosted` starts the browser after `Loaded` or `HandleCreated` |

## Revit adapter

| Symbol | Notes |
|--------|-------|
| `REVIT_CONTEXT.initialize(app)` | Once on the Revit main thread. Records `ManagedThreadId` (.NET Framework 4.8 and .NET 8). |
| `REVIT_CONTEXT.post(action)` | New external event, then return. WebMessage callback and command chaining. |
| `REVIT_CONTEXT.invoke(action)` | Wait for the result from another thread. Inline only inside this gate's own event. Raises on the Revit UI thread outside that event. |

## JSON

| Symbol | Notes |
|--------|-------|
| `serialize(value)` | Python JSON value to a string. Dicts and lists are copied into CLR collections first. |
| `deserialize(text)` | String to a Python dict, list, or scalar via `JsonTextReader`. |
| `JsonValue` | Alias for those Python values. The envelope uses it. |

Requires `Newtonsoft.Json`. See [Architecture](architecture.md#json).

## Logging

```python
from pyrevit_webview.log import get_logger
```

`PYREVIT_WEBVIEW_LOG` sets the level. Default is `INFO`.
