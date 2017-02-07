from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

# Create your tests here.
from dynamic_logging.handlers import MockHandler
from dynamic_logging.models import Config, Trigger
from dynamic_logging.scheduler import main_scheduler
from dynamic_logging.tests import now_plus


class TestPages(TestCase):
    def setUp(self):
        pass

    def test_200(self):
        res = self.client.get('/testapp/ok/')
        self.assertEqual(res.status_code, 200)

    def test_401(self):
        res = self.client.get('/testapp/error401/')
        self.assertEqual(res.status_code, 401)

    def test_raise(self):
        self.assertRaises(Exception, self.client.get, '/testapp/error500/')

    def test_log_no_cfg(self):
        with MockHandler.capture() as messages:
            res = self.client.get('/testapp/log/DEBUG/testproject.testapp/')
            self.assertEqual(res.status_code, 200)
            self.assertEqual(messages['debug'], [])

    def test_log_with_cfg(self):
        cfg = Config(name='mocklog')
        cfg.config = {"loggers": {
            "testproject.testapp": {
                "handlers": ["mock"],
                "level": "WARN",
            }
        }}
        cfg.apply()
        with MockHandler.capture() as messages:
            res = self.client.get('/testapp/log/DEBUG/testproject.testapp/')
            self.assertEqual(res.status_code, 200)
            self.assertEqual(messages['debug'], [])

    def test_log_bad_level(self):
        self.assertRaises(Exception, self.client.get, '/testapp/log/OOPS/testproject.testapp/')


class TestAdminContent(TestCase):

    def setUp(self):
        super(TestAdminContent, self).setUp()
        u = get_user_model().objects.create(username='admin', is_staff=True, is_superuser=True)
        """:type: django.contrib.auth.models.User"""
        u.set_password('password')
        u.save()
        self.client.login(username='admin', password='password')
        main_scheduler.reload()
        self.c = c = Config.objects.create(name='my_config', config_json='{}')
        self.t = Trigger.objects.create(name='in1hour', config=c, start_date=now_plus(2), end_date=now_plus(4))

    def tearDown(self):
        main_scheduler.reset()

    def test_logging_in_admin(self):
        response = self.client.get('/admin/')
        self.assertContains(response, 'Trigger')

    def test_config_list(self):
        response = self.client.get(reverse('admin:dynamic_logging_config_changelist'))
        self.assertContains(response, 'default settings')

    def test_trigger_list(self):
        response = self.client.get(reverse('admin:dynamic_logging_trigger_changelist'))
        self.assertContains(response, 'in1hour')

    def test_config_change(self):
        response = self.client.get(reverse('admin:dynamic_logging_config_change', args=(self.t.pk,)))
        self.assertContains(response, 'my_config')

    def test_trigger_change(self):
        response = self.client.get(reverse('admin:dynamic_logging_trigger_change', args=(self.t.pk,)))
        self.assertContains(response, 'in1hour')
