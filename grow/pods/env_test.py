from grow.pods import env
import os
import unittest

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata', 'pod')


class EnvTest(unittest.TestCase):

    def test_constructor_basic(self):
        config = env.EnvConfig(host='localhost')
        environment = env.Env(config)
        self.assertEqual('localhost', environment.host)
        self.assertEqual('http', environment.scheme)
        self.assertEqual(80, environment.port)

    def test_constructor_full(self):
        config = env.EnvConfig(host='remotehost', scheme='https', port=443)
        environment = env.Env(config)
        self.assertEqual('remotehost', environment.host)
        self.assertEqual('https', environment.scheme)
        self.assertEqual(443, environment.port)

    def test_url_host(self):
        config = env.EnvConfig(host='remotehost')
        environment = env.Env(config)
        self.assertEqual('http://remotehost/', environment.url)

    def test_url_port_80(self):
        config = env.EnvConfig(host='localhost', scheme='http', port=80)
        environment = env.Env(config)
        self.assertEqual('http://localhost/', environment.url)

    def test_url_port_80_mismatch(self):
        config = env.EnvConfig(host='localhost', scheme='https', port=80)
        environment = env.Env(config)
        self.assertEqual('https://localhost:80/', environment.url)

    def test_url_port_443(self):
        config = env.EnvConfig(host='localhost', scheme='https', port=443)
        environment = env.Env(config)
        self.assertEqual('https://localhost/', environment.url)

    def test_url_port_443_mismatch(self):
        config = env.EnvConfig(host='localhost', scheme='http', port=443)
        environment = env.Env(config)
        self.assertEqual('http://localhost:443/', environment.url)

    def test_url_port_custom(self):
        config = env.EnvConfig(host='localhost', scheme='http', port=8080)
        environment = env.Env(config)
        self.assertEqual('http://localhost:8080/', environment.url)

    def test_fingerprint(self):
        # May be used as {{env.fingerprint}} in templates.
        config = env.EnvConfig(host='localhost', scheme='http', port=8080)
        environment = env.Env(config)
        self.assertTrue(isinstance(environment.fingerprint, str))


if __name__ == '__main__':
    unittest.main()
