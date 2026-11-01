# Logging

Uses Python stdlib `logging` (IronPython 2.7 / CPython 3).

## Default logger

```python
from pywebui.log import get_logger

logger = get_logger()  # logging.getLogger("pywebui")
logger.info("ready")
```

Lines look like `[pywebui] ready`. The level comes from `PYWEBUI_LOG` and defaults to `INFO`. `debug_trace` writes `DEBUG` and includes the managed thread id. Set `PYWEBUI_LOG=DEBUG` to see those lines.

## Per-app logger

```python
import logging

from pywebui.webview import WebViewSession
from pywebui.log import get_logger

logging.basicConfig(level=logging.INFO)

session = WebViewSession(
    content=...,
    app_name="myapp",
    logger=get_logger("myapp"),
)
```

## What gets logged

| Source | Examples |
|--------|----------|
| `WebViewControl` | Env init, navigation, dispose |
| `MessageRouter` | Unknown message types, handler errors |
| Your code | `session.logger.info(...)` |

## See also

- [API](api.md) — `get_logger`
