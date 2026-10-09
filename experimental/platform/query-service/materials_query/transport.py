"""Bounded local HTTP transport, outside routing and response serialization.

A slot covers receive, application work, and the actual ASGI send. Cancellation
joins application work before returning its slot; synchronous worker threads
cannot be forcibly interrupted, so their existing I/O bounds still apply.
"""
from math import isfinite
from threading import BoundedSemaphore

import anyio
from fastapi import FastAPI
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse

MAX_BODY_BYTES = 32768
REQUEST_TIMEOUT_SECONDS = 60.0
SECURITY_HEADERS = (
    (b'x-content-type-options', b'nosniff'),
    (b'cache-control', b'no-store'),
    (b'content-security-policy',
     b"default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'"),
)


def is_heavy_request(path):
    """One shared budget for provider queries and local/computed reads."""
    return (
        path in {'/api/search', '/api/batch', '/api/demo'}
        or path.startswith('/api/records/')
        or any(path.startswith(prefix) and path != prefix + 'status'
               for prefix in ('/api/catalog/', '/api/computed/'))
    )


class LocalTransportBoundary:
    """Pure ASGI boundary; never relies on Content-Length for enforcement."""

    def __init__(self, app, *, timeout_seconds=REQUEST_TIMEOUT_SECONDS):
        if not isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError('Transport timeout must be positive')
        self.app = app
        self.timeout_seconds = timeout_seconds
        # A threading semaphore also covers concurrent TestClient event loops.
        self._slots = BoundedSemaphore(2)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        response_started = False
        response_finished = False
        acquired = False
        disconnected = anyio.Event()

        async def secured_send(message):
            nonlocal response_started, response_finished
            # Do not deliver a late result after cancellation of a sync worker.
            await anyio.lowlevel.checkpoint()
            if disconnected.is_set():
                return
            if message['type'] == 'http.response.start':
                message = dict(message)
                names = {name for name, _ in SECURITY_HEADERS}
                message['headers'] = [(name, value) for name, value in message.get('headers', ())
                                      if name.lower() not in names] + list(SECURITY_HEADERS)
                # A cancelled send may already have written bytes to the socket.
                response_started = True
            try:
                await send(message)
                if (message['type'] == 'http.response.body' and not message.get('more_body', False)
                        or message['type'] == 'http.response.pathsend'):
                    response_finished = True
            except OSError:
                disconnected.set()
                raise

        async def error(status, detail):
            await JSONResponse({'detail': detail}, status_code=status)(scope, receive, secured_send)

        async def serve():
            nonlocal acquired
            headers = Headers(scope=scope)
            origin = headers.get('origin')
            if origin and origin != str(Request(scope).base_url).rstrip('/'):
                await error(403, 'Cross-origin requests are disabled')
                return
            # Reject an honest oversized declaration early, but always count the
            # bytes below for missing, malformed, or understated declarations.
            for raw in headers.getlist('content-length'):
                value = raw.lstrip('0') or '0'
                if value.isascii() and value.isdecimal() and (
                    len(value) > len(str(MAX_BODY_BYTES)) or int(value) > MAX_BODY_BYTES
                ):
                    await error(413, 'Request body exceeds 32 KiB')
                    return
            if is_heavy_request(scope.get('path', '')):
                acquired = self._slots.acquire(blocking=False)
                if not acquired:
                    await error(429, 'Two query operations are active; retry later')
                    return

            # Buffer only the bounded body before routing. This also protects
            # endpoints which do not consume a body, and keeps body-limit errors
            # outside FastAPI's request-validation exception translation.
            body = bytearray()
            while True:
                try:
                    message = await receive()
                except OSError:
                    disconnected.set()
                    return
                if message['type'] == 'http.disconnect':
                    disconnected.set()
                    return
                if message['type'] != 'http.request':
                    continue
                chunk = message.get('body', b'')
                if len(chunk) > MAX_BODY_BYTES - len(body):
                    await error(413, 'Request body exceeds 32 KiB')
                    return
                body.extend(chunk)
                if not message.get('more_body', False):
                    break

            replayed = False
            finished = anyio.Event()
            failure = None

            async def bounded_receive():
                nonlocal replayed
                if not replayed:
                    replayed = True
                    return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
                await disconnected.wait()
                return {'type': 'http.disconnect'}

            async def run_application():
                nonlocal failure
                try:
                    await self.app(scope, bounded_receive, secured_send)
                except OSError as exc:
                    # Only a transport error is a disconnect. Preserve errors
                    # raised by application code for FastAPI's normal handling.
                    if not disconnected.is_set():
                        failure = exc
                except Exception as exc:
                    failure = exc
                finally:
                    finished.set()

            async def watch_disconnect(tasks):
                while True:
                    await anyio.lowlevel.checkpoint()
                    try:
                        message = await receive()
                    except OSError:
                        message = {'type': 'http.disconnect'}
                    if message['type'] == 'http.disconnect':
                        # Some servers report disconnect as soon as the final
                        # body is sent. Let normal response cleanup finish.
                        if response_finished:
                            return
                        disconnected.set()
                        tasks.cancel_scope.cancel()
                        return

            # Run application work in a child task. Cancelling the caller then
            # joins the child, including shielded synchronous threadpool work,
            # rather than abandoning it while admitting another operation.
            async with anyio.create_task_group() as tasks:
                tasks.start_soon(run_application)
                tasks.start_soon(watch_disconnect, tasks)
                await finished.wait()
                tasks.cancel_scope.cancel()
            if failure is not None:
                raise failure

        try:
            with anyio.fail_after(self.timeout_seconds) as deadline:
                await serve()
        except TimeoutError:
            if not deadline.cancel_called:
                raise
            # A started response cannot be replaced with a second status. End
            # its ASGI invocation; the server closes the incomplete response.
            if not response_started and not disconnected.is_set():
                with anyio.move_on_after(min(1.0, self.timeout_seconds)):
                    try:
                        await error(504, 'Request exceeded the transport timeout')
                    except OSError:
                        pass
        except OSError:
            # Closed response transport; cleanup still releases a slot.
            if not disconnected.is_set():
                raise
        finally:
            if acquired:
                self._slots.release()


class TransportBoundedFastAPI(FastAPI):
    """Keep FastAPI's route/state API while bounding its entire middleware stack."""

    def __init__(self, *args, transport_timeout_seconds=REQUEST_TIMEOUT_SECONDS, **kwargs):
        super().__init__(*args, **kwargs)
        self.transport_boundary = LocalTransportBoundary(
            super().__call__, timeout_seconds=transport_timeout_seconds)

    async def __call__(self, scope, receive, send):
        await self.transport_boundary(scope, receive, send)
