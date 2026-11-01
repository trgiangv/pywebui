# WPF example

Complete dashboard: `Window` + WPF `WebView2` + Python bindings.

## Paths

```python
UI_DIST = r"C:\myapp\ui\dist"
START_URI = "https://app.local/index.html"
```

## Full script

```python
# dashboard_wpf.py
import clr

clr.AddReference("PresentationFramework")
clr.AddReference("WindowsBase")

from System.Windows import Window, WindowStartupLocation

from pywebui import Bindable, bridge_callable
from pywebui.webview import (
    PackagedContent,
    WebViewControl,
    WebViewSession,
    WebViewSettings,
)
from pywebui.webview.wpf import WebView2, WpfUi

UI_DIST = r"C:\myapp\ui\dist"
START_URI = "https://app.local/index.html"


class AppBinding(Bindable):
    """Handlers invoked via postMessage."""

    def __init__(self, window):
        self._window = window

    @bridge_callable("GetGreeting")
    def get_greeting(self):
        return {"message": "Hello from WPF + Python"}

    @bridge_callable("SetTitle")
    def set_title(self, title):
        self._window.Title = str(title)
        return True


class DashboardWindow(Window):
    def __init__(self):
        Window.__init__(self)
        self.Title = "My Dashboard"
        self.Width = 1024
        self.Height = 768
        self.WindowStartupLocation = WindowStartupLocation.CenterScreen

        self._webview = WebView2()
        self.Content = self._webview

        session = WebViewSession(
            app_name="myapp",
            content=PackagedContent(start_uri=START_URI, content_root=UI_DIST),
            settings=WebViewSettings(dev_tools_enabled=False),
        )

        self._control = WebViewControl(
            self._webview,
            session,
            bindings=[AppBinding(self)],
            ui=WpfUi(self, self._webview),
        )
        self.Closed += self._on_closed

    def _on_closed(self, sender, args):
        self._control.dispose()


window = DashboardWindow()
window.Show()
```

## WinForms vs WPF

| | WinForms | WPF |
|---|----------|-----|
| WebView2 package | `Microsoft.Web.WebView2.WinForms` | `Microsoft.Web.WebView2.Wpf` |
| UI thread | `WinFormsUi` | `WpfUi` |
| Browser may start | `HandleCreated` | `Loaded` |
| Window close | `FormClosed` | `Closed` |

Both use the same `WebViewSession`, `Bindable`, and `WebViewControl` API.

## See also

- [WinForms](winforms.md)
- [Architecture](architecture.md) — why `post` stays on the window thread
