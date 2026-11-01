# Revit / pyRevit

Inside Revit, WebView bridge callbacks may run on a thread that cannot call the Revit API. Use `RevitContext`. Callers do not reference `RevitTask`.

## Two thread layers

| Layer | Helper | Purpose |
|-------|--------|---------|
| Window UI | `host.wpf` or `host.winforms` | WebView2 control, form title, `ExecuteScriptAsync` |
| Revit API | `adapter.revit.RevitContext` | Document, elements, transactions |

`post` raises one synchronous external event and returns. Use it from `WebMessageReceived`, and from a running action when the next command must be its own event.

`invoke` returns the result. It waits only from a thread other than the Revit UI thread. It runs inline only while `RevitContext` is already inside its own external event. The modeless window dispatcher has the same `ManagedThreadId` and is still outside an API context, so `invoke` there raises instead of calling the API or blocking the thread that must pump the event. Both methods pass a synchronous delegate. An `async` delegate can resume outside that event after `await`.

`ManagedThreadId` exists on .NET Framework 4.8 and on .NET 8. It identifies the thread. It does not mean Revit is in an API context.

## 1. Extension startup (once)

```python
from pywebui.adapter.revit import REVIT_CONTEXT

REVIT_CONTEXT.initialize(uiapp)  # UIApplication
```

After `initialize`, `REVIT_CONTEXT` also exposes the application it was given, so later code does not need it passed again: `uiapp`, `app`, `uidoc`, `doc`, `version` (e.g. `"2025"`) and `main_window` (the Revit WPF main window, for `window.Owner`). `uidoc` and `doc` are read from the live `UIApplication` on every access; do not cache them.
## 2. Session

```python
from pywebui.webview import PackagedContent, WebViewSession

session = WebViewSession(
    content=PackagedContent(
        start_uri="https://app.local/index.html",
        content_root=r"C:\myapp\ui\dist",
    ),
    app_name="myapp",
)
```

## 3. Binding that reads the model

IronPython: bridge handlers may lose **module globals**. Capture deps on ``self``.

```python
from pywebui import Bindable, bridge_callable
from pywebui.adapter.revit import REVIT_CONTEXT


class RevitAppBinding(Bindable):
    name = "app"

    def __init__(self):
        self._uiapp = __revit__  # noqa: F821

    @bridge_callable("GetDocumentTitle")
    def get_document_title(self):
        uiapp = self._uiapp

        def read_title():
            return uiapp.ActiveUIDocument.Document.Title

        return REVIT_CONTEXT.invoke(read_title)
```

That `invoke` is valid when the handler is not running on the Revit UI thread. A modeless WebView callback on that thread uses `post`, then sends the title with `emit` after the event runs.

## 4. Window wiring

```python
from pywebui.webview import WebViewControl
from pywebui.webview.wpf import WebView2, WpfUi

webview = WebView2()
control = WebViewControl(
    webview,
    session,
    bindings=[RevitAppBinding()],
    ui=WpfUi(window, webview),
)
```

## Shipped DLLs

`./scripts/sync-bin.ps1` copies `Revit.Async.dll` and `Newtonsoft.Json.dll` into `pywebui/bin/`. Revit reuses an assembly of the same simple name that is already loaded. The full set is in [install.md](install.md).

## See also

- [API](api.md) — package layout
- [Architecture](architecture.md) — request flow and JSON
