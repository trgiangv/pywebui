# Install & build

## pyRevit lib extension

```text
pyrevit extend lib pyWebUI https://github.com/trgiangv/pywebui.git
```

After cloning or forking, point `extend` at your repo URL.

## Shipped .NET fallbacks

Python hosts need WebView2, Revit.Async, and Newtonsoft.Json under `pywebui/bin/`:

```powershell
./scripts/sync-bin.ps1
```

This restores NuGet packages and copies managed DLLs into `pywebui/bin/`. **No custom bridge DLL** — the Python package talks to WebView2 directly.

## Runtime loading

If the assembly simple name is already in the AppDomain, `load_bin()` only registers it with the CLR importer and does not load the `bin/` copy. Otherwise it loads that file. Safe to call on every window open.

| File | When loaded |
|------|-------------|
| `Revit.Async.dll` | `RevitContext.initialize` |
| `Newtonsoft.Json.dll` | `serialize` / `deserialize`. An already loaded Revit copy is reused |
| `Microsoft.Web.WebView2.Core.dll` | WebView2 SDK fallback |
| `Microsoft.Web.WebView2.WinForms.dll` | WinForms control fallback |
| `Microsoft.Web.WebView2.Wpf.dll` | WPF control fallback |
| `runtimes/win-x64/native/WebView2Loader.dll` | Native loader (win-x64) |

Managed DLLs stay in `bin/`. Native `WebView2Loader.dll` follows the NuGet `runtimes/{rid}/native` layout.

### WebView2 control import

Host scripts import the control from the WPF or WinForms package after `load_bin()`:

```python
from pywebui.webview.wpf import WebView2
# or
from pywebui.webview.winforms import WebView2
```

`WebViewControl` calls `load_clr_types()` internally. That registers `bin/` and imports the WebView2 types. It does not start the CLR.

## Requirements

- **WebView2 Runtime** (Edge Chromium) installed on the machine
- pyRevit / IronPython 2.7 or compatible pythonnet host
- `System.Windows.Forms` / WPF — provided by the host (.NET Framework / Revit)

## Verify

```powershell
./scripts/sync-bin.ps1
# Expect: WebView2, Revit.Async, and Newtonsoft.Json listed under pywebui/bin/
```
