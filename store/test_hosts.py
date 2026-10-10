from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.test import SimpleTestCase, RequestFactory, override_settings

class DeploymentHostTests(SimpleTestCase):
    def test_public_alias_is_allowed(self):
        self.assertIn('kedarkhand.vercel.app', settings.ALLOWED_HOSTS)
        request = RequestFactory().get('/', HTTP_HOST='kedarkhand.vercel.app')
        with override_settings(ALLOWED_HOSTS=settings.ALLOWED_HOSTS, DEBUG=False):
            self.assertEqual(request.get_host(), 'kedarkhand.vercel.app')

    def test_other_domains_remain_disallowed(self):
        request = RequestFactory().get('/', HTTP_HOST='untrusted.example')
        with override_settings(ALLOWED_HOSTS=settings.ALLOWED_HOSTS, DEBUG=False):
            with self.assertRaises(DisallowedHost):
                request.get_host()

    def test_public_alias_is_trusted_for_csrf(self):
        self.assertIn('https://kedarkhand.vercel.app', settings.CSRF_TRUSTED_ORIGINS)
