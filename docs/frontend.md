# Frontend (JavaScript)

`WebViewControl` wires `WebMessageReceived` to a Python `MessageRouter`. The page talks to Python through `chrome.webview.postMessage` — no COM host objects.

## Protocol

### JS → Python (invoke)

```javascript
chrome.webview.postMessage({
  id: crypto.randomUUID(),
  type: "invoke",
  method: "GetGreeting",
  params: [],
});
```

`@bridge_callable("GetGreeting")` methods are registered automatically from `bindings=[...]`.

### Python → JS (response)

Host emits a `CustomEvent`:

```javascript
window.addEventListener("bridge-response", (event) => {
  const { id, ok, data, error } = event.detail;
});
```

Shape: `{ id, ok: true, data }` or `{ id, ok: false, error }`.

### Host push events (optional)

From Python:

```python
control._router.emit("my-event", {"value": 1})
```

From JS:

```javascript
window.addEventListener("my-event", (event) => {
  console.log(event.detail);
});
```

## TypeScript client

See `webview_demo_ui/src/lib/bridge-client.ts` in the pyDCMvn extension for a minimal `BridgeClient` with `invoke(method, params)`.

## Dev vs production

- **Dev:** `RemoteContent("http://localhost:5174")` — Vite dev server, hot reload.
- **Prod:** `PackagedContent(start_uri, content_root=dist)` — virtual host mapping, no HTML injection.

## See also

- [WinForms](winforms.md) — full host setup
- [API](api.md) — `@bridge_callable` naming
