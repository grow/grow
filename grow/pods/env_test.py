import os
import unittest

from grow.common import structures
from grow.pods import env

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata', 'pod')


class EnvTest(unittest.TestCase):

    def test_constructor_basic(self):
        config = structures.AttributeDict(host='localhost')
        environment = env.Env(config)
        self.assertEqual('localhost', environment.host)
        self.assertEqual(None, environment.scheme)
        self.assertEqual(None, environment.port)

    def test_constructor_full(self):
        config = structures.AttributeDict(host='remotehost', scheme='https', port=443)
        environment = env.Env(config)
        self.assertEqual('remotehost', environment.host)
        self.assertEqual('https', environment.scheme)
        self.assertEqual(443, environment.port)

    def test_url_host(self):
        config = structures.AttributeDict(host='remotehost')
        environment = env.Env(config)
        self.assertEqual('http://remotehost/', str(environment.url))

    def test_url_port_80(self):
        config = structures.AttributeDict(host='localhost', scheme='http', port=80)
        environment = env.Env(config)
        self.assertEqual('http://localhost/', str(environment.url))

    def test_url_port_80_mismatch(self):
        config = structures.AttributeDict(host='localhost', scheme='https', port=80)
        environment = env.Env(config)
        self.assertEqual('https://localhost:80/', str(environment.url))

    def test_url_port_443(self):
        config = structures.AttributeDict(host='localhost', scheme='https', port=443)
        environment = env.Env(config)
        self.assertEqual('https://localhost/', str(environment.url))

    def test_url_port_443_mismatch(self):
        config = structures.AttributeDict(host='localhost', scheme='http', port=443)
        environment = env.Env(config)
        self.assertEqual('http://localhost:443/', str(environment.url))

    def test_url_port_custom(self):
        config = structures.AttributeDict(host='localhost', scheme='http', port=8080)
        environment = env.Env(config)
        self.assertEqual('http://localhost:8080/', str(environment.url))

    def test_fingerprint(self):
        # May be used as {{env.fingerprint}} in templates.
        config = structures.AttributeDict(host='localhost', scheme='http', port=8080)
        environment = env.Env(config)
        self.assertTrue(isinstance(environment.fingerprint, str))


if __name__ == '__main__':
    unittest.main()
