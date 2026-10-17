(function () {
  "use strict";

  var out = document.getElementById("out");
  var pending = {};
  var lines = [];
  var RESPONSE_EVENT = "bridge-response";

  function log(msg) {
    lines.push(msg);
    out.textContent = lines.join("\n");
    if (window.console && console.log) console.log(msg);
  }

  function newRequestId() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "req-" + Date.now() + "-" + Math.random().toString(16).slice(2);
  }

  function postInvoke(method, params) {
    return new Promise(function (resolve, reject) {
      var post = window.chrome && chrome.webview && chrome.webview.postMessage;
      if (!post) {
        reject(new Error("chrome.webview.postMessage missing"));
        return;
      }
      var id = newRequestId();
      pending[id] = { resolve: resolve, reject: reject };
      post({
        id: id,
        type: "invoke",
        method: method,
        params: params || []
      });
    });
  }

  window.addEventListener(RESPONSE_EVENT, function (event) {
    var detail = event.detail || {};
    var entry = pending[detail.id];
    if (!entry) return;
    delete pending[detail.id];
    if (detail.ok) {
      entry.resolve(detail.data);
    } else {
      entry.reject(new Error(detail.error || "Unknown error"));
    }
  });

  function timed(label, factory) {
    var t0 = performance.now();
    return factory().then(function (data) {
      var ms = performance.now() - t0;
      log(label + " OK  " + ms.toFixed(1) + " ms  " + JSON.stringify(data));
      return { label: label, ms: ms, data: data };
    }).catch(function (err) {
      var ms = performance.now() - t0;
      log(label + " FAIL " + ms.toFixed(1) + " ms  " + String(err));
      throw err;
    });
  }

  function pingOnce(i) {
    return timed("Ping#" + i, function () { return postInvoke("Ping", [i]); });
  }

  function runSequential(n) {
    var chain = Promise.resolve();
    var results = [];
    for (var i = 1; i <= n; i++) {
      (function (idx) {
        chain = chain.then(function () {
          return pingOnce(idx).then(function (r) { results.push(r); return r; });
        });
      })(i);
    }
    return chain.then(function () {
      var total = results.reduce(function (s, r) { return s + r.ms; }, 0);
      log("--- sequential n=" + n + " total=" + total.toFixed(1) + " ms avg=" + (total / n).toFixed(1) + " ms");
      return results;
    });
  }

  function runBurst(n) {
    var jobs = [];
    for (var i = 1; i <= n; i++) jobs.push(pingOnce(i));
    var t0 = performance.now();
    return Promise.all(jobs).then(function (results) {
      var wall = performance.now() - t0;
      var total = results.reduce(function (s, r) { return s + r.ms; }, 0);
      log("--- burst n=" + n + " wall=" + wall.toFixed(1) + " ms sum=" + total.toFixed(1) + " ms");
      return results;
    });
  }

  function autoRun() {
    lines = [];
    log("Auto-run start");
    return timed("Ping#warm", function () { return postInvoke("Ping", [0]); })
      .then(function () { return runSequential(10); })
      .then(function () { return runBurst(10); })
      .then(function () { return timed("Echo", function () { return postInvoke("Echo", ["hello", 42]); }); })
      .then(function () {
        log("AUTO_DONE");
        return postInvoke("NotifyDone", ["ok"]);
      })
      .catch(function (err) {
        log("AUTO_FAIL " + String(err));
        try { return postInvoke("NotifyDone", ["fail:" + String(err)]); } catch (e) { return null; }
      });
  }

  document.getElementById("btnPing").onclick = function () { pingOnce(1); };
  document.getElementById("btnSeq").onclick = function () { runSequential(10); };
  document.getElementById("btnBurst").onclick = function () { runBurst(10); };
  document.getElementById("btnAuto").onclick = function () { autoRun(); };

  function waitBridge(attempts) {
    if (window.chrome && chrome.webview && chrome.webview.postMessage) {
      log("Bridge ready");
      autoRun();
      return;
    }
    if (attempts <= 0) {
      log("Bridge NOT ready");
      return;
    }
    setTimeout(function () { waitBridge(attempts - 1); }, 200);
  }

  window.addEventListener("DOMContentLoaded", function () { waitBridge(50); });
})();
