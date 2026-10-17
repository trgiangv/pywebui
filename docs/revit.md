# Revit / pyRevit

Inside Revit, WebView bridge callbacks may run on **worker threads**. Revit API calls require **Revit's main thread** (`RevitTask`), not only WinForms/WPF `BeginInvoke`.

## Two thread layers

| Layer | Helper | Purpose |
|-------|--------|---------|
| Window UI | `host.wpf_invoke` / `host.winforms_invoke` | WebView2 control, form title, `ExecuteScriptAsync` |
| Revit API | `revit_invoke_sync` | Document, elements, transactions |

## 1. Extension startup (once)

```python
from pyrevit_webview.adapter.revit import initialize_revit_task

initialize_revit_task(__revit__)  # UIControlledApplication / UIApplication
```

## 2. Session

```python
from pyrevit_webview.host import PackagedContent, WebViewSession

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
from pyrevit_webview import Bindable, bridge_callable
from pyrevit_webview.adapter.revit import revit_invoke_sync


class RevitAppBinding(Bindable):
    name = "app"

    def __init__(self):
        self._invoke = revit_invoke_sync
        self._uiapp = __revit__  # noqa: F821

    @bridge_callable("GetDocumentTitle")
    def get_document_title(self):
        uiapp = self._uiapp

        def read_title():
            return uiapp.ActiveUIDocument.Document.Title

        return self._invoke(read_title)
```

`revit_invoke_sync` runs **inline** when already on Revit main (avoids deadlock with UI invoke); otherwise marshals via `RevitTask`.

## 4. Window wiring

```python
from pyrevit_webview.host import WebViewControl, wpf_invoke
from pyrevit_webview.host.wpf import WebView2

webview = WebView2()
control = WebViewControl(
    webview,
    session,
    bindings=[RevitAppBinding()],
    invoke_on_ui=wpf_invoke(window),
)
```

## Shipped DLL

`Revit.Async.dll` is copied to `pyrevit_webview/bin/` at build time.

## See also

- [API](api.md) — package layout
- [Architecture](architecture.md) — JS → C# → Python thread flow
