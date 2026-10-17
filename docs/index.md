# Documentation

WebView2 + Python **postMessage** bridge for pyRevit. You own the window (WinForms or WPF).

## Quick start

1. [Install](install.md) the lib extension and sync `bin/` DLLs.
2. Pick a host example:
   - [WinForms](winforms.md)
   - [WPF](wpf.md)
   - [Revit / pyRevit](revit.md)
3. Wire the [frontend](frontend.md) (`postMessage`).
4. Optional: [dev server](dev-server.md), [logging](logging.md).

## Guides

| Topic | Description |
|-------|-------------|
| [Install & build](install.md) | pyRevit extend, `sync-bin.ps1`, shipped DLLs |
| [WinForms example](winforms.md) | Complete `Form` + `WebView2` + bindings |
| [WPF example](wpf.md) | Complete `Window` + `WebView2` + bindings |
| [Revit adapter](revit.md) | `Revit.Async`, `revit_invoke_sync` |
| [Dev server](dev-server.md) | Vite + CDP debugging |
| [Frontend (JS)](frontend.md) | `postMessage` / `bridge-response` |
| [Logging](logging.md) | stdlib `logging` integration |
| [API reference](api.md) | Public Python types and helpers |
| [Architecture](architecture.md) | Layers & threading |

## Typical flow

```
npm run build → dist/
     ↓
Bindable + @bridge_callable
     ↓
WebViewSession + WebViewControl(webview, …)
     ↓
chrome.webview.postMessage({ type: "invoke", method, params })
     ↓
dispose() on window close
```
