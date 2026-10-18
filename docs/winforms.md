# WinForms example

Complete dashboard: `Form` + WinForms `WebView2` + Python bindings.

## Prerequisites

- Built UI in `dist/` (see [dev server](dev-server.md) for Vite workflow)
- `start_uri` host matches your build (`https://app.local` is common with virtual host mapping)

## Paths

```python
UI_DIST = r"C:\myapp\ui\dist"
START_URI = "https://app.local/index.html"
```

## Full script

```python
# dashboard_winforms.py
import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Size
from System.Windows.Forms import DockStyle, Form

from pyrevit_webview import Bindable, bridge_callable
from pyrevit_webview.host import (
    PackagedContent,
    WebViewControl,
    WebViewSession,
    WebViewSettings,
)
from pyrevit_webview.host.winforms import WebView2, winforms_invoke, winforms_when_ready

UI_DIST = r"C:\myapp\ui\dist"
START_URI = "https://app.local/index.html"


class AppBinding(Bindable):
    """Handlers invoked via postMessage."""

    def __init__(self, form):
        self._form = form

    @bridge_callable("GetGreeting")
    def get_greeting(self):
        return {"message": "Hello from WinForms + Python"}

    @bridge_callable("SetTitle")
    def set_title(self, title):
        self._form.Text = str(title)
        return True


class DashboardForm(Form):
    def __init__(self):
        Form.__init__(self)
        self.Text = "My Dashboard"
        self.Size = Size(1024, 768)

        self._webview = WebView2()
        self._webview.Dock = DockStyle.Fill
        self.Controls.Add(self._webview)

        session = WebViewSession(
            app_name="myapp",
            content=PackagedContent(start_uri=START_URI, content_root=UI_DIST),
            settings=WebViewSettings(dev_tools_enabled=False),
        )

        self._control = WebViewControl(
            self._webview,
            session,
            bindings=[AppBinding(self)],
            invoke_on_ui=winforms_invoke(self),
            when_ready=winforms_when_ready(self._webview),
        )
        self.FormClosed += self._on_closed

    def _on_closed(self, sender, args):
        self._control.dispose()


form = DashboardForm()
form.Show()
```

## Key points

| Piece | Role |
|-------|------|
| `winforms_invoke(self)` | Marshals bridge callbacks and script execution to the form UI thread |
| `winforms_when_ready(webview)` | Starts the browser after the control handle exists |
| `PackagedContent` | Maps `https://app.local` → `UI_DIST` via WebView2 virtual host |
| `WebViewControl.dispose()` | Detach handlers and dispose WebView2 — call on `FormClosed` |

## pyRevit note

Use `form.Show()` (non-modal). The host process must keep its UI message loop running.

## See also

- [WPF](wpf.md) — same pattern with `wpf_invoke`
- [Revit](revit.md) — `revit_invoke_sync` for Revit API calls
- [Frontend](frontend.md) — JavaScript side
