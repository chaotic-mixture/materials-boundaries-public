"""Exercise the complete FastAPI app at the ASGI receive/send boundary.

HTTPX/TestClient buffer responses, so they cannot prove send backpressure or
chunk-by-chunk receive limits. These tests deliberately control both channels.
"""
import asyncio
import json
from threading import Event
import unittest

from materials_query.app import create_app
from materials_query.transport import MAX_BODY_BYTES


PIN = {'namespace': 'computed', 'baseline_version': 'a' * 64,
       'overlay_version': 'b' * 64, 'review_version': 'c' * 64}


class Registry:
    def snapshot(self):
        return {**PIN, 'records': [], 'attribution': 'transport test fixture'}


class Exchange:
    def __init__(self, path='/api/computed/export', *, body=None, headers=(),
                 chunks=None, method='POST', stall=None, fail_send=False):
        self.scope = {
            'type': 'http', 'asgi': {'version': '3.0', 'spec_version': '2.4'},
            'http_version': '1.1', 'method': method, 'scheme': 'http',
            'path': path, 'raw_path': path.encode(), 'root_path': '',
            'query_string': b'', 'headers': [(b'host', b'testserver'),
                                           (b'content-type', b'application/json'), *headers],
            'client': ('127.0.0.1', 32100), 'server': ('testserver', 80),
        }
        self.incoming = asyncio.Queue()
        if chunks is None:
            data = json.dumps(PIN if body is None else body).encode()
            chunks = [{'type': 'http.request', 'body': data, 'more_body': False}]
        for chunk in chunks:
            self.incoming.put_nowait(chunk)
        self.messages = []
        self.received_requests = 0
        self.stall = stall
        self.fail_send = fail_send
        self.sending = asyncio.Event()
        self.release = asyncio.Event()
        self.send_cancelled = asyncio.Event()

    async def receive(self):
        message = await self.incoming.get()
        if message['type'] == 'http.request':
            self.received_requests += 1
        return message

    async def send(self, message):
        if message['type'] == self.stall:
            self.sending.set()
            try:
                await self.release.wait()
            except asyncio.CancelledError:
                self.send_cancelled.set()
                raise
        if self.fail_send and message['type'] == 'http.response.body':
            raise OSError('transport closed')
        self.messages.append(message)

    async def run(self, app):
        await app(self.scope, self.receive, self.send)
        return self

    async def started(self):
        await asyncio.wait_for(self.sending.wait(), 2)

    def disconnect(self):
        self.incoming.put_nowait({'type': 'http.disconnect'})

    @property
    def statuses(self):
        return [m['status'] for m in self.messages if m['type'] == 'http.response.start']


class FullAppTransportTests(unittest.IsolatedAsyncioTestCase):
    def app(self, timeout=2):
        return create_app(computed_registry=Registry(), transport_timeout_seconds=timeout)

    async def complete(self, app, **kwargs):
        return await asyncio.wait_for(Exchange(**kwargs).run(app), 2)

    async def test_incremental_limit_without_or_with_false_content_length(self):
        class NoProvider:
            def search(self, query):
                raise AssertionError('Oversized bodies must not reach the provider')
        app = create_app(NoProvider())
        for header in (None, b'0', b'10', b'garbage', b'-1'):
            with self.subTest(content_length=header):
                exchange = Exchange('/api/search', headers=() if header is None else [(b'content-length', header)],
                    chunks=[{'type': 'http.request', 'body': b'x' * 16384, 'more_body': True},
                            {'type': 'http.request', 'body': b'x' * 16384, 'more_body': True},
                            {'type': 'http.request', 'body': b'x', 'more_body': True},
                            {'type': 'http.request', 'body': b'never read', 'more_body': False}])
                await exchange.run(app)
                self.assertEqual(exchange.statuses, [413])
                self.assertEqual(exchange.received_requests, 3)
                self.assertEqual(exchange.incoming.qsize(), 1)

    async def test_exact_body_limit_and_oversize_on_non_body_route(self):
        body = json.dumps({'provider': 'materials_project', 'formula': 'Si'}).encode()
        exchange = Exchange('/api/search', chunks=[{'type': 'http.request',
            'body': body + b' ' * (MAX_BODY_BYTES - len(body)), 'more_body': False}])
        await exchange.run(self.app())
        self.assertEqual(exchange.statuses, [503])
        oversize = await self.complete(self.app(), path='/api/health', method='GET',
            chunks=[{'type': 'http.request', 'body': b'x' * (MAX_BODY_BYTES + 1)}])
        self.assertEqual(oversize.statuses, [413])

    async def test_declared_oversize_rejected_without_receiving(self):
        for value in (b'32769', b'9' * 5000):
            exchange = Exchange(headers=[(b'content-length', value)], chunks=[])
            await exchange.run(self.app())
            self.assertEqual(exchange.statuses, [413])
            self.assertEqual(exchange.received_requests, 0)

    async def test_one_shared_limit_retained_through_body_delivery(self):
        app = self.app()
        first = Exchange(stall='http.response.body')
        second = Exchange('/api/search', body={'provider': 'materials_project', 'formula': 'Si'},
                          stall='http.response.body')
        tasks = [asyncio.create_task(x.run(app)) for x in (first, second)]
        try:
            await first.started()
            await second.started()
            # The route handlers and response objects already exist. Their
            # uncompleted body delivery must continue to occupy both slots.
            for path, body in (
                ('/api/catalog/search', {'version': '0' * 64, 'query': 'wood'}),
                ('/api/computed/list', PIN),
                ('/api/demo', {}),
                ('/api/batch', {'queries': [{'formula': 'Si'}]}),
                ('/api/records/missing', {}),
            ):
                third = await self.complete(app, path=path, body=body)
                self.assertEqual(third.statuses, [429], path)
            for path in ('/api/health', '/api/catalog/status', '/api/computed/status'):
                response = await self.complete(app, path=path, method='GET', body={})
                self.assertEqual(response.statuses, [200], path)
            first.release.set()
            await tasks[0]
            self.assertEqual((await self.complete(app)).statuses, [200])
        finally:
            first.release.set()
            second.release.set()
            await asyncio.gather(*tasks)

    async def test_stalled_response_start_also_holds_slot(self):
        app = self.app()
        exchanges = [Exchange(stall='http.response.start') for _ in range(2)]
        tasks = [asyncio.create_task(x.run(app)) for x in exchanges]
        try:
            await asyncio.gather(*(x.started() for x in exchanges))
            self.assertEqual((await self.complete(app)).statuses, [429])
        finally:
            for exchange in exchanges:
                exchange.release.set()
            await asyncio.gather(*tasks)
        self.assertEqual((await self.complete(app)).statuses, [200])

    async def test_send_timeout_cancels_without_second_response_and_releases(self):
        app = self.app(timeout=.04)
        exchange = Exchange(stall='http.response.body')
        await asyncio.wait_for(exchange.run(app), 1)
        self.assertTrue(exchange.send_cancelled.is_set())
        self.assertEqual(exchange.statuses, [200])
        self.assertEqual((await self.complete(app)).statuses, [200])

    async def test_receive_timeout_returns_504_and_releases(self):
        app = self.app(timeout=.04)
        exchange = Exchange(chunks=[{'type': 'http.request', 'body': b'{', 'more_body': True}])
        await asyncio.wait_for(exchange.run(app), 1)
        self.assertEqual(exchange.statuses, [504])
        self.assertEqual((await self.complete(app)).statuses, [200])

    async def test_async_work_timeout_runs_cleanup_and_releases(self):
        app = self.app(timeout=.04)
        cleaned = asyncio.Event()
        @app.post('/api/computed/wait')
        async def wait():
            try:
                await asyncio.Event().wait()
            finally:
                cleaned.set()
        exchange = await self.complete(app, path='/api/computed/wait')
        self.assertEqual(exchange.statuses, [504])
        self.assertTrue(cleaned.is_set())
        self.assertEqual((await self.complete(app)).statuses, [200])

    async def test_caller_cancellation_joins_sends_and_releases(self):
        app = self.app()
        exchanges = [Exchange(stall='http.response.body') for _ in range(2)]
        tasks = [asyncio.create_task(x.run(app)) for x in exchanges]
        await asyncio.gather(*(x.started() for x in exchanges))
        for task in tasks:
            task.cancel()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self.assertTrue(all(isinstance(result, asyncio.CancelledError) for result in results))
        self.assertTrue(all(x.send_cancelled.is_set() for x in exchanges))
        self.assertEqual((await self.complete(app)).statuses, [200])

    async def test_disconnect_during_receive_and_send_releases(self):
        app = self.app()
        early = Exchange(chunks=[{'type': 'http.request', 'body': b'{', 'more_body': True},
                                 {'type': 'http.disconnect'}])
        await early.run(app)
        self.assertEqual(early.messages, [])
        exchanges = [Exchange(stall='http.response.body') for _ in range(2)]
        tasks = [asyncio.create_task(x.run(app)) for x in exchanges]
        await asyncio.gather(*(x.started() for x in exchanges))
        for exchange in exchanges:
            exchange.disconnect()
        await asyncio.wait_for(asyncio.gather(*tasks), 1)
        self.assertTrue(all(x.send_cancelled.is_set() for x in exchanges))
        self.assertEqual((await self.complete(app)).statuses, [200])

    async def test_closed_send_releases(self):
        app = self.app()
        for _ in range(3):
            exchange = await self.complete(app, fail_send=True)
            self.assertEqual(exchange.statuses, [200])
        self.assertEqual((await self.complete(app)).statuses, [200])

    async def test_sync_workers_keep_slots_until_cancellation_cleanup(self):
        app = self.app()
        entered = [Event(), Event()]
        release = Event()
        counter = iter(entered)
        @app.post('/api/computed/blocked')
        def blocked():
            next(counter).set()
            release.wait(2)
            return {'ok': True}
        exchanges = [Exchange('/api/computed/blocked') for _ in range(2)]
        tasks = [asyncio.create_task(x.run(app)) for x in exchanges]
        try:
            async with asyncio.timeout(1):
                while not all(event.is_set() for event in entered):
                    await asyncio.sleep(.001)
            tasks[0].cancel()
            await asyncio.sleep(.02)
            self.assertFalse(tasks[0].done(), 'Cancellation must join the active sync worker')
            self.assertEqual((await self.complete(app)).statuses, [429])
        finally:
            release.set()
            results = await asyncio.gather(*tasks, return_exceptions=True)
        self.assertIsInstance(results[0], asyncio.CancelledError)
        self.assertEqual(exchanges[0].statuses, [])
        self.assertEqual(exchanges[1].statuses, [200])
        self.assertEqual((await self.complete(app)).statuses, [200])

    async def test_sync_worker_timeout_retains_slots_until_workers_exit(self):
        app = self.app(timeout=.04)
        entered = [Event(), Event()]
        release = Event()
        counter = iter(entered)
        @app.post('/api/computed/blocked')
        def blocked():
            next(counter).set()
            release.wait(2)
            return {'ok': True}
        exchanges = [Exchange('/api/computed/blocked') for _ in range(2)]
        tasks = [asyncio.create_task(x.run(app)) for x in exchanges]
        try:
            async with asyncio.timeout(1):
                while not all(event.is_set() for event in entered):
                    await asyncio.sleep(.001)
            await asyncio.sleep(.08)
            self.assertTrue(all(not task.done() for task in tasks))
            self.assertEqual((await self.complete(app)).statuses, [429])
        finally:
            release.set()
            await asyncio.gather(*tasks)
        self.assertTrue(all(x.statuses == [504] for x in exchanges))
        self.assertEqual((await self.complete(app)).statuses, [200])

    async def test_timeout_error_delivery_itself_is_bounded(self):
        app = self.app(timeout=.02)
        exchange = Exchange(chunks=[], stall='http.response.start')
        await asyncio.wait_for(exchange.run(app), 1)
        self.assertTrue(exchange.send_cancelled.is_set())
        self.assertEqual((await self.complete(app)).statuses, [200])

    async def test_application_errors_preserve_semantics_and_release(self):
        app = self.app()
        @app.post('/api/computed/error')
        async def failure():
            raise ValueError('test error')
        for _ in range(3):
            exchange = Exchange('/api/computed/error')
            with self.assertRaisesRegex(ValueError, 'test error'):
                await exchange.run(app)
            self.assertEqual(exchange.statuses, [500])
            self.assertEqual(dict(exchange.messages[0]['headers'])[b'cache-control'], b'no-store')
        self.assertEqual((await self.complete(app)).statuses, [200])

    async def test_origin_host_and_security_headers_cover_boundary_errors(self):
        app = self.app()
        for headers, status in (
            ([(b'origin', b'https://evil.invalid')], 403),
            ([(b'content-length', b'32769')], 413),
        ):
            exchange = await self.complete(app, headers=headers)
            self.assertEqual(exchange.statuses, [status])
            response_headers = dict(exchange.messages[0]['headers'])
            self.assertEqual(response_headers[b'x-content-type-options'], b'nosniff')
            self.assertEqual(response_headers[b'cache-control'], b'no-store')
            self.assertIn(b"frame-ancestors 'none'", response_headers[b'content-security-policy'])
        exchange = Exchange()
        exchange.scope['headers'] = [(b'host', b'evil.invalid')]
        await exchange.run(app)
        self.assertEqual(exchange.statuses, [400])


if __name__ == '__main__':
    unittest.main()
