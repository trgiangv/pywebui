# -*- coding: utf-8 -*-
from __future__ import division, print_function

import asyncio
import binascii
import hmac
import os
import socket
import threading
import time

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pywebui.bridge.contract import CommandRequest, EnvelopeField, EnvelopeKind
from pywebui.bridge.sink import EnvelopeSink
from pywebui.log import get_logger
from pywebui.serialize import serialize

_KEEPALIVE = 15.0


class InvokeBody(BaseModel):
    id: str
    command: str
    payload: dict = Field(default_factory=dict)


class _Client(object):
    """One SSE connection. ``put`` is safe from any thread."""

    def __init__(self):
        self.loop = asyncio.get_running_loop()
        self.queue = asyncio.Queue()

    def put(self, text):
        self.loop.call_soon_threadsafe(self.queue.put_nowait, text)


class HttpSink(EnvelopeSink):
    """Resolves the request waiting for a response and fans events out over SSE."""

    def __init__(self):
        self._lock = threading.Lock()
        self._waiting = {}
        self._clients = []

    def request(self, request_id, submit, timeout):
        """Run ``submit`` and wait for the response with this id. ``None`` on timeout."""
        slot = (threading.Event(), [None])
        with self._lock:
            self._waiting[request_id] = slot
        submit()
        if slot[0].wait(timeout):
            return slot[1][0]
        with self._lock:
            self._waiting.pop(request_id, None)
        return None

    def client_count(self):
        with self._lock:
            return len(self._clients)

    def add_client(self):
        """Call from the server's event loop."""
        client = _Client()
        with self._lock:
            self._clients.append(client)
        return client

    def remove_client(self, client):
        with self._lock:
            self._clients.remove(client)

    def close_clients(self):
        """End every event stream so the server can shut down without cancelling them."""
        with self._lock:
            clients = list(self._clients)
        for client in clients:
            client.put(None)

    def send(self, message):
        if message.get(EnvelopeField.TYPE) == EnvelopeKind.RESPONSE:
            with self._lock:
                slot = self._waiting.pop(message.get(EnvelopeField.ID), None)
            if slot is not None:
                slot[1][0] = message
                slot[0].set()
            return
        with self._lock:
            clients = list(self._clients)
        if clients:
            text = serialize(message)
            for client in clients:
                client.put(text)


class HttpTransport(object):
    """Loopback HTTP server for one page.

    ``submit(request)`` receives each ``CommandRequest`` on a server thread. It
    must queue the work and later call ``sink.send`` with the response.
    ``info`` is served by ``/api/health``. Read host API values before
    ``start``: request threads must not touch them.

    Only the origins of ``site`` may call the API, and only with the session
    token, which is sent in ``token_header`` or in ``?token=`` for SSE. In local
    mode the transport also serves the build and accepts its own origin.
    """

    def __init__(
        self,
        sink,
        submit,
        site,
        ports,
        info=None,
        host="127.0.0.1",
        token_header="X-Pywebui-Token",
        request_timeout=300.0,
        title="pywebui",
    ):
        self.sink = sink
        self.port = None
        self.token = binascii.hexlify(os.urandom(16)).decode("ascii")
        self._submit = submit
        self._site = site
        self._origins = set(site.origins)
        self._ports = ports
        self._host = host
        self._token_header = token_header
        self._timeout = request_timeout
        self._info = dict(info or {}, ok=True, transport="http", pid=os.getpid())
        self._server = None
        self._app = self._create_app(title)

    def start(self):
        """Bind the first free port and serve on a worker thread."""
        sock = self._bind()
        server = uvicorn.Server(
            uvicorn.Config(
                self._app,
                log_config=None,
                lifespan="off",
                ws="none",
                http="h11",
                timeout_graceful_shutdown=2,
            )
        )
        threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True).start()
        self._server = server
        get_logger().info("HTTP transport listening on port {0}".format(self.port))

    def stop(self):
        server, self._server = self._server, None
        if server is not None:
            self.sink.close_clients()
            server.should_exit = True

    def _bind(self):
        for port in self._ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind((self._host, port))
            except OSError:
                sock.close()
                continue  # in use by another host process
            sock.listen()  # a browser opened before uvicorn accepts waits in the backlog
            self.port = port
            if self._site.static_dir:
                self._origins.update(
                    "http://{0}:{1}".format(name, port) for name in (self._host, "localhost")
                )
            return sock
        raise RuntimeError(
            "no free port in {0}-{1}".format(self._ports[0], self._ports[-1])
        )

    def _create_app(self, title):
        app = FastAPI(title=title, docs_url=None, redoc_url=None, openapi_url=None)
        app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=[self._host, "localhost"]
        )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=sorted(self._origins),
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", self._token_header],
            allow_private_network=True,  # Chrome asks before a public page may call loopback
            max_age=600,
        )

        def origin_allowed(request: Request) -> None:
            origin = request.headers.get("origin")
            if origin is not None and origin not in self._origins:
                raise HTTPException(403, "forbidden")

        def token_valid(
            header: str = Header(None, alias=self._token_header),
            token: str = Query(None),
        ) -> None:
            if not hmac.compare_digest(header or token or "", self.token):
                raise HTTPException(401, "missing or wrong token")

        guarded = [Depends(origin_allowed), Depends(token_valid)]

        @app.get("/api/health", dependencies=[Depends(origin_allowed)])
        def health(request: Request):
            get_logger().info("health from {0}".format(request.headers.get("origin")))
            return self._info

        @app.post(
            "/api/invoke",
            dependencies=guarded,
            responses={504: {"description": "The host did not answer within the request timeout"}},
        )
        def invoke(body: InvokeBody):
            parsed = CommandRequest(body.command, body.id, body.payload)
            get_logger().info("invoke {0} {1}".format(parsed.command, parsed.id))
            reply = self.sink.request(parsed.id, lambda: self._submit(parsed), self._timeout)
            if reply is None:
                get_logger().warning(
                    "invoke {0} {1}: no answer in {2}s".format(parsed.command, parsed.id, self._timeout)
                )
                raise HTTPException(504, "no answer in time")
            started = time.perf_counter()
            text = serialize(reply)
            get_logger().info(
                "invoke {0} {1}: serialized {2} chars in {3:.0f} ms".format(
                    parsed.command, parsed.id, len(text), (time.perf_counter() - started) * 1000
                )
            )
            return Response(text, media_type="application/json")

        @app.get("/api/events", dependencies=guarded)
        async def events():
            client = self.sink.add_client()
            get_logger().info("events connected")

            async def stream():
                try:
                    yield ": connected\n\n"
                    while True:
                        try:
                            text = await asyncio.wait_for(client.queue.get(), _KEEPALIVE)
                            if text is None:
                                return
                            yield "data: {0}\n\n".format(text)
                        except asyncio.TimeoutError:
                            yield ": ping\n\n"
                finally:
                    self.sink.remove_client(client)

            return StreamingResponse(
                stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
            )

        if self._site.static_dir:
            app.mount("/", StaticFiles(directory=self._site.static_dir, html=True))

        return app
