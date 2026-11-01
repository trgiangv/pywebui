# pyWebUI

One page, two ways to host it: a **WebView2** window inside Revit, or the user's **browser** over a loopback HTTP server. Both carry the same command envelope, so the application code is written once.

```python
from pywebui import Bridge, parse_request, response_message, event_message
from pywebui.adapter.revit import REVIT_CONTEXT

bridge = Bridge()

@bridge.command("Zoom")
def zoom(payload):
    return {"ok": True}
```

| Module | Runs on | Use |
|--------|---------|-----|
| `pywebui.webview` | IronPython, CPython | `WebViewControl`, `WebViewSession`, `RemoteContent`, `wpf.WebView2` / `winforms.WebView2` |
| `pywebui.http` | CPython only | `HttpSink`, `HttpTransport` (FastAPI + uvicorn + pydantic) |
| `pywebui.Site` / `Mode` | IronPython, CPython | `Mode.DEV` (dev server), `Mode.LOCAL` (a build folder), `Mode.SERVER` (a deployed URL). One `Site` gives WebView2 its content and the HTTP transport its origins and static folder |
| `pywebui.runtime` | IronPython, CPython | `find_python`, `ensure_packages`: check, delete and `pip install --target` the HTTP packages for a CPython interpreter into `%LOCALAPPDATA%\pyWebUI\packages\<tag>`, through child processes. A missing, old or unimportable package heals by reinstalling the folder |
| `pywebui.embed` | IronPython, CPython | `start`, `run`: start pyRevit's pythonnet and a CPython engine inside the host process with the GIL released, then run CPython source with CLR objects as globals. Must be the first CPython runtime started in the Revit session; otherwise `RuntimeAlreadyStartedError` asks for a Revit restart |

Importing `pywebui.http` under IronPython raises `UnsupportedRuntimeError`; with the packages missing it raises `MissingDependencyError` and names the `pip` command. Both subclass `ImportError`.

```python
from pywebui import embed

embed.start(runtime_dll, python_dll, python_home, sys_path=[packages_dir])
embed.run("print(app.Application.VersionName)", app=uiapp)
```

## Quick start

```text
pyrevit extend lib pyWebUI https://github.com/trgiangv/pyrevit-webview.git
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

## Shipped binaries (`pywebui/bin/`)

Populated by `./scripts/sync-bin.ps1` — loaded when not already in the AppDomain:

`Microsoft.Web.WebView2.*.dll` · `Revit.Async.dll` · `Newtonsoft.Json.dll` · `runtimes/win-x64/native/WebView2Loader.dll`

MIT
