"""Unit, security, and performance tests for the built-in WebReview client."""

import base64
import hashlib
import http.server
import os
import tempfile
import threading
import unittest
from unittest import mock

from grow.deployments.destinations import webreview_client, webreview_destination


class _MockGCSHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    store = {}
    fail_once_paths = set()
    connection_count = 0

    def setup(self):
        super().setup()
        type(self).connection_count += 1

    def log_message(self, format, *args):
        pass

    def _send(self, status, body=b''):
        self.send_response(status)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'keep-alive')
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_PUT(self):
        length = int(self.headers.get('Content-Length', '0'))
        data = self.rfile.read(length) if length else b''
        path = self.path.split('?', 1)[0]
        if path in self.fail_once_paths:
            self.fail_once_paths.remove(path)
            self._send(503, b'Transient error')
            return
        self.store[path] = data
        self._send(200, b'ok')

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path not in self.store:
            self._send(404, b'Not found')
            return
        self._send(200, self.store[path])

    def do_DELETE(self):
        path = self.path.split('?', 1)[0]
        if path not in self.store:
            self._send(404, b'Not found')
            return
        del self.store[path]
        self._send(204, b'')


class WebReviewClientTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _MockGCSHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        _MockGCSHandler.store.clear()
        _MockGCSHandler.fail_once_paths.clear()
        _MockGCSHandler.connection_count = 0

    def _signed_req(self, verb, path, content=b''):
        req = {
            'url': f'http://127.0.0.1:{self.port}{path}',
            'path': path,
            'verb': verb,
            'params': {
                'google_access_id': 'test@example.com',
                'signature': 'sig',
                'expires': '9999999999',
            },
        }
        if verb == webreview_client.Verb.PUT:
            unsigned = webreview_client.GoogleStorageSigner.create_unsigned_request(
                verb, path, content
            )
            req['headers'] = unsigned['headers']
        return req

    def test_project_validation_and_fileset(self):
        for bad in ('', 'noslash', '/missingowner', 'missingproject/'):
            with self.assertRaises(ValueError):
                webreview_client.WebReview(project=bad, host='example.com')

        client = webreview_client.WebReview(
            project='Owner/Proj',
            name='Staging',
            host='example.com',
            secure=True,
        )
        self.assertEqual(
            client.fileset,
            {
                'name': 'staging',
                'commit': None,
                'project': {
                    'nickname': 'proj',
                    'owner': {'nickname': 'owner'},
                },
            },
        )

    def test_create_unsigned_request_handles_str_utf8_bytes_and_binary(self):
        signer = webreview_client.GoogleStorageSigner
        # Text str
        req_str = signer.create_unsigned_request(webreview_client.Verb.PUT, '/index.html', 'héllo')
        expected_bytes = 'héllo'.encode()
        self.assertEqual(req_str['headers']['content_length'], str(len(expected_bytes)))
        self.assertEqual(
            req_str['headers']['content_md5'],
            base64.b64encode(hashlib.md5(expected_bytes).digest()).decode('utf-8'),
        )
        self.assertEqual(req_str['headers']['content_type'], 'text/html')

        # UTF-8 bytes (previously crashed hashlib.md5 in legacy webreview!)
        req_utf8_bytes = signer.create_unsigned_request(
            webreview_client.Verb.PUT, '/page/', b'hello world'
        )
        self.assertEqual(req_utf8_bytes['headers']['content_type'], 'text/html')
        self.assertEqual(req_utf8_bytes['headers']['content_length'], '11')

        # Non-UTF-8 binary bytes
        raw = b'\x89PNG\r\n\x1a\n\x00\xff'
        req_bin = signer.create_unsigned_request(webreview_client.Verb.PUT, '/img.png', raw)
        self.assertEqual(req_bin['headers']['content_length'], str(len(raw)))
        self.assertEqual(req_bin['headers']['content_type'], 'image/png')

    def test_execute_signed_request_put_get_delete_and_keepalive_reuse(self):
        signer = webreview_client.GoogleStorageSigner
        put_req = self._signed_req(webreview_client.Verb.PUT, '/hello.txt', b'hello')
        self.assertEqual(signer.execute_signed_request(put_req, b'hello'), b'ok')

        get_req = self._signed_req(webreview_client.Verb.GET, '/hello.txt')
        self.assertEqual(signer.execute_signed_request(get_req), b'hello')

        del_req = self._signed_req(webreview_client.Verb.DELETE, '/hello.txt')
        self.assertEqual(signer.execute_signed_request(del_req), b'')

        # All 3 requests on the same thread should reuse a single keep-alive socket.
        self.assertEqual(_MockGCSHandler.connection_count, 1)

        with self.assertRaises(webreview_client.GoogleStorageRpcError) as ctx:
            signer.execute_signed_request(get_req)
        self.assertEqual(ctx.exception.status, 404)

    def test_execute_signed_request_retries_on_503(self):
        signer = webreview_client.GoogleStorageSigner
        _MockGCSHandler.fail_once_paths.add('/retry.txt')
        put_req = self._signed_req(webreview_client.Verb.PUT, '/retry.txt', b'data')
        with mock.patch.object(webreview_client.time, 'sleep'):
            resp = signer.execute_signed_request(put_req, b'data')
        self.assertEqual(resp, b'ok')
        self.assertEqual(_MockGCSHandler.store['/retry.txt'], b'data')

    def test_execute_signed_request_rejects_non_http_scheme(self):
        signer = webreview_client.GoogleStorageSigner
        bad_req = self._signed_req(webreview_client.Verb.GET, '/x')
        bad_req['url'] = 'file:///etc/passwd'
        with self.assertRaises(ValueError):
            signer.execute_signed_request(bad_req)

    def test_http_with_api_key_scopes_header_to_allowed_host(self):
        http = webreview_client.HttpWithApiKey(api_key='secret-key', allowed_host='wr.example.com')
        seen_headers = []

        def fake_super_request(
            self_arg,
            conn,
            host,
            absolute_uri,
            request_uri,
            method,
            body,
            headers,
            redirections,
            cachekey,
        ):
            seen_headers.append((host, dict(headers)))
            return ({'status': '200'}, b'')

        with mock.patch.object(webreview_client.httplib2.Http, '_request', fake_super_request):
            http._request(
                None, 'wr.example.com', 'https://wr.example.com/', '/', 'GET', None, {}, 5, None
            )
            http._request(
                None,
                'evil.example.com',
                'https://evil.example.com/',
                '/',
                'GET',
                None,
                {'WebReview-Api-Key': 'secret-key'},
                5,
                None,
            )

        self.assertEqual(seen_headers[0][1].get('WebReview-Api-Key'), 'secret-key')
        self.assertNotIn('WebReview-Api-Key', seen_headers[1][1])

    def test_get_storage_blocks_path_traversal(self):
        with self.assertRaises(ValueError):
            webreview_client.get_storage('WebReview Client', '../etc/passwd')

    def test_get_credentials_respects_reauth_and_no_interactive_auth(self):
        fake_storage = mock.MagicMock()
        fake_storage.get.return_value = mock.MagicMock(invalid=False)
        with (
            mock.patch.object(webreview_client, 'get_storage', return_value=fake_storage),
            mock.patch.dict(os.environ, {'NO_INTERACTIVE_AUTH': '1'}, clear=False),
            mock.patch.object(os.path, 'exists', return_value=False),
        ):
            # Cached credentials returned when reauth=False
            creds = webreview_client.WebReview.get_credentials('default', reauth=False)
            self.assertIs(creds, fake_storage.get.return_value)

            # reauth=True skips cache and triggers non-interactive error instead of dead OOB flow
            with self.assertRaises(RuntimeError):
                webreview_client.WebReview.get_credentials('default', reauth=True)

    def test_upload_dir_reads_binary_and_text_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write('<h1>Hello</h1>')
            os.makedirs(os.path.join(tmpdir, 'img'))
            with open(os.path.join(tmpdir, 'img', 'pixel.bin'), 'wb') as f:
                f.write(b'\x89PNG\xff\x00')

            docs = webreview_client.WebReview._get_paths_to_rendered_doc_from_dir(tmpdir)
            self.assertEqual(docs['/index.html'].read(), b'<h1>Hello</h1>')
            self.assertEqual(docs['/img/pixel.bin'].read(), b'\x89PNG\xff\x00')

    def test_webreview_destination_uses_builtin_client(self):
        self.assertIs(webreview_destination._get_webreview(), webreview_client)
