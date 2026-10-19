# Dev server (Vite / webpack)

Use a live dev server while building the UI; switch to `PackagedContent` for production.

## Session for development

```python
from pyrevit_webview.host import (
    RemoteContent,
    WebViewControl,
    WebViewSession,
    WebViewSettings,
)
from pyrevit_webview.host.winforms import WinFormsUi

session = WebViewSession(
    app_name="myapp-dev",
    content=RemoteContent("http://localhost:5173"),
    debug_cdp_port=9225,
    settings=WebViewSettings(dev_tools_enabled=True),
)

control = WebViewControl(
    webview,
    session,
    bindings=[AppBinding(host)],
    ui=WinFormsUi(form, webview),
    on_browser_ready=lambda c: c.show_devtools(),
)
```

| Option | Effect |
|--------|--------|
| `RemoteContent(url)` | Navigate to Vite/webpack dev server |
| `debug_cdp_port` | Chrome can attach to embedded browser (`chrome://inspect`) |
| `additional_browser_arguments` | Extra Chromium command-line arguments appended to the host defaults |
| `dev_tools_enabled=True` | Allow `show_devtools()` / F12-style debugging |
| `on_browser_ready` | Callback after CoreWebView2 init — good place to open DevTools |

## Vite virtual host for production

When you ship `dist/`, use `PackagedContent` with a stable host name:

```python
PackagedContent(
    start_uri="https://app.local/index.html",
    content_root=r"C:\myapp\ui\dist",
)
```

In `vite.config.ts`:

```ts
export default defineConfig({
  base: "/",
  server: {
    host: "localhost",
    port: 5173,
  },
  // For production build, assets work under https://app.local when mapped
});
```

The `start_uri` host (`app.local`) must match what you configure for virtual host mapping — WebView2 does not use real DNS for `PackagedContent`.

## Typical workflow

1. Terminal: `npm run dev` (Vite on `:5173`)
2. Revit/pyRevit: open dashboard with `RemoteContent`
3. Edit frontend → hot reload in embedded WebView
4. `npm run build` → switch session to `PackagedContent` for release

## See also

- [WinForms](winforms.md) / [WPF](wpf.md) — production `PackagedContent` wiring
