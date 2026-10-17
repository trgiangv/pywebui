# pythonnet out-of-process bridge harness (no Revit)

Isolates `postMessage` ↔ `MessageRouter` ↔ `bridge-response` latency on a dedicated
STA WPF thread.

## Run

```powershell
cd c:\Users\truon\source\repos\pyrevit-webview

$env:PYTHONNET_RUNTIME = "netfx"
uv run --python 3.13 --with pythonnet --no-project python tests\pythonnet_oob\run_wpf_bridge_test.py
```

No `WebViewBridge.dll` build required — Python bridge is pure postMessage.

## Pass criteria

- Final line: `[oob] finished status=ok`
- Exit code `0`
