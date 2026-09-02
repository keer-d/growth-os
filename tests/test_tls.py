import ssl
import unittest

from pipeline.tls import trusted_ssl_context


class TLSConfigurationTests(unittest.TestCase):
    def test_live_provider_context_keeps_verification_enabled(self):
        context = trusted_ssl_context()
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)


if __name__ == "__main__":
    unittest.main()
