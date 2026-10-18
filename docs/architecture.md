# Architecture

## Layers

```
┌─────────────────────────────────────────┐
│  Your window (WinForms / WPF)           │
│  WebView2 control (.NET)                │
└─────────────────┬───────────────────────┘
                  │ WebViewControl (Python)
                  ▼
┌─────────────────────────────────────────┐
│  pyrevit_webview (Python)               │
│  • WebViewSession / settings            │
│  • Bindable + @bridge_callable          │
│  • MessageRouter (postMessage)          │
│  • invoke_on_ui (injected)              │
│  • host/wpf or host/winforms            │
│  • adapter/revit (optional host app)    │
└─────────────────┬───────────────────────┘
                  │ WebMessageReceived
                  ▼
┌─────────────────────────────────────────┐
│  Frontend (JavaScript / React)          │
│  chrome.webview.postMessage             │
│  window "bridge-response" CustomEvent   │
└─────────────────────────────────────────┘
```

## Request flow (JS → Python)

1. Page calls `chrome.webview.postMessage({ id, type: "invoke", method, params })`.
2. `WebMessageReceived` delivers JSON to `MessageRouter.handle_raw`.
3. Router dispatches to the `@bridge_callable` handler.
4. Handler may use `revit_invoke_sync` for Revit API work.
5. Router responds with `CustomEvent("bridge-response", { detail: { id, ok, data } })` via `ExecuteScriptAsync` on the UI thread.

## Threading rules

| Operation | Thread |
|-----------|--------|
| `CoreWebView2.ExecuteScriptAsync` | WebView UI thread (`invoke_on_ui`) |
| `@bridge_callable` body | `WebMessageReceived` callback — marshal to UI/Revit inside handler when needed |
| Revit API | `revit_invoke_sync` after `initialize_revit_task` |

## Shipped `bin/` (.NET fallbacks only)

| DLL | Role |
|-----|------|
| `Microsoft.Web.WebView2.*` | WebView2 managed API when host has not loaded it |
| `Revit.Async.dll` | `RevitTask` marshalling for `revit_invoke_sync` |
| `WebView2Loader.dll` | Native WebView2 loader |

No custom bridge assembly. Python + IronPython/pythonnet orchestrates the .NET WebView2 control directly.

## Dispose

`WebViewControl.dispose()`:

- Unhooks `CoreWebView2InitializationCompleted`
- Disposes `WebView2` on UI thread
- Clears router reference

Always call when the host window closes.
