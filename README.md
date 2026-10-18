# pyrevit-webview

WebView2 + Python **postMessage** bridge for pyRevit. You own the window — WinForms or WPF.

```python
from pyrevit_webview import Bindable, bridge_callable, MessageRouter
from pyrevit_webview.host import WebViewControl, WebViewSession, PackagedContent
from pyrevit_webview.host.wpf import WebView2, wpf_invoke, wpf_when_ready
from pyrevit_webview.adapter.revit import initialize_revit_task
```

No custom C# bridge — Python orchestrates WebView2 via IronPython / pythonnet.

## Quick start

```text
pyrevit extend lib pyrevit-webview https://github.com/trgiangv/pyrevit-webview.git
```

```powershell
./scripts/sync-bin.ps1
```

1. Build a frontend (`dist/`).
2. Define `Bindable` + `@bridge_callable`.
3. Create `WebViewSession` + `WebViewControl` on your `WebView2`.
4. `dispose()` when the window closes.

## Documentation

| Guide | Topic |
|-------|--------|
| [**docs/index.md**](docs/index.md) | Overview & navigation |
| [install.md](docs/install.md) | Install, `sync-bin.ps1`, shipped DLLs |
| [winforms.md](docs/winforms.md) | Complete WinForms example |
| [wpf.md](docs/wpf.md) | Complete WPF example |
| [revit.md](docs/revit.md) | `Revit.Async` adapter |
| [dev-server.md](docs/dev-server.md) | Vite + CDP debugging |
| [frontend.md](docs/frontend.md) | JavaScript `postMessage` API |
| [logging.md](docs/logging.md) | stdlib `logging` |
| [api.md](docs/api.md) | Public API reference |
| [architecture.md](docs/architecture.md) | Layers & threading |

## Shipped binaries (`pyrevit_webview/bin/`)

Populated by `./scripts/sync-bin.ps1` — loaded when not already in the AppDomain:

`Microsoft.Web.WebView2.*.dll` · `Revit.Async.dll` · `runtimes/win-x64/native/WebView2Loader.dll`

MIT
