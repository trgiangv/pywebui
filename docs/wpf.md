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

from pyrevit_webview import (
    Bindable,
    PackagedContent,
    WebViewControl,
    WebViewSession,
    WebViewSettings,
    bridge_callable,
    default_user_data_folder,
    ensure_webview2_wpf,
    wpf_invoke,
)

ensure_webview2_wpf()
from Microsoft.Web.WebView2.Wpf import WebView2

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
            user_data_folder=default_user_data_folder("myapp"),
            content=PackagedContent(start_uri=START_URI, content_root=UI_DIST),
            settings=WebViewSettings(dev_tools_enabled=False),
        )

        self._control = WebViewControl(
            self._webview,
            session,
            bindings=[AppBinding(self)],
            invoke_on_ui=wpf_invoke(self),
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
| UI dispatch | `winforms_invoke(form)` | `wpf_invoke(window)` |
| Window close | `FormClosed` | `Closed` |

Both use the same `WebViewSession`, `Bindable`, and `WebViewControl` API.

## See also

- [WinForms](winforms.md)
- [Architecture](architecture.md) — why `invoke_on_ui` matters for script execution
