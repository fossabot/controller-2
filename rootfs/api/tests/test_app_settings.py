import requests_mock

from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from api.models.app import App
from unittest import mock
from scheduler import KubeException
from api.tests import adapter, DryccTransactionTestCase

User = get_user_model()


@requests_mock.Mocker(real_http=True, adapter=adapter)
class TestAppSettings(DryccTransactionTestCase):
    """Tests setting and updating config values"""

    fixtures = ['tests.json']

    def setUp(self):
        self.user = User.objects.get(username='autotest')
        self.token = Token.objects.get(user=self.user).key
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

    def tearDown(self):
        # make sure every test has a clean slate for k8s mocking
        cache.clear()

    def test_settings_routable(self, mock_requests):
        """
        Create an application with the routable flag turned on or off
        """
        # create app, expecting routable to be true
        app_id = self.create_app()
        app = App.objects.get(id=app_id)
        self.assertTrue(app.appsettings_set.latest().routable)
        # Set routable to false
        response = self.client.post(
            '/v2/apps/{app.id}/settings'.format(**locals()),
            {'routable': False}
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertFalse(app.appsettings_set.latest().routable)

    def test_settings_allowlist(self, mock_requests):
        """
        Test that addresses can be added/deleted to allowlist
        """
        app_id = self.create_app()
        app = App.objects.get(id=app_id)
        # add addresses to empty allowlist
        addresses = ["0.0.0.0/0"]
        allowlist = {'addresses': addresses}
        response = self.client.post(
            '/v2/apps/{app_id}/allowlist'.format(**locals()),
            allowlist)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(set(response.data['addresses']),
                         set(app.appsettings_set.latest().allowlist), response.data)
        self.assertEqual(set(response.data['addresses']), set(addresses), response.data)

        # get the allowlist
        response = self.client.get('/v2/apps/{app_id}/allowlist'.format(**locals()))
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(set(response.data['addresses']),
                         set(app.appsettings_set.latest().allowlist), response.data)
        self.assertEqual(set(response.data['addresses']), set(addresses), response.data)

        # delete an address from allowlist
        allowlist = {'addresses': ["0.0.0.0/0"]}
        addresses.remove("0.0.0.0/0")
        response = self.client.delete(
            '/v2/apps/{app_id}/allowlist'.format(**locals()),
            allowlist)
        self.assertEqual(response.status_code, 204, response.data)
        self.assertEqual(set(addresses), set(app.appsettings_set.latest().allowlist))

        # add addresses to empty allowlist
        addresses = ["0.0.0.0/0"]
        allowlist = {'addresses': addresses}
        response = self.client.post(
            '/v2/apps/{app_id}/allowlist'.format(**locals()),
            allowlist)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(set(response.data['addresses']),
                         set(app.appsettings_set.latest().allowlist), response.data)
        self.assertEqual(set(response.data['addresses']), set(addresses), response.data)

        # add addresses to non-empty allowlist
        allowlist = {'addresses': ["2.3.4.5"]}
        addresses.extend(["2.3.4.5"])
        response = self.client.post(
            '/v2/apps/{app_id}/allowlist'.format(**locals()),
            allowlist)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(set(response.data['addresses']),
                         set(app.appsettings_set.latest().allowlist), response.data)
        self.assertEqual(set(response.data['addresses']), set(addresses), response.data)
        # add exisitng addresses to allowlist
        response = self.client.post(
            '/v2/apps/{app_id}/allowlist'.format(**locals()),
            allowlist)
        self.assertEqual(response.status_code, 409, response.data)
        # delete non-exisitng address from allowlist
        allowlist = {'addresses': ["2.3.4.6"]}
        response = self.client.delete(
            '/v2/apps/{app_id}/allowlist'.format(**locals()),
            allowlist)
        self.assertEqual(response.status_code, 422)

        # pass invalid address
        allowlist = {'addresses': ["2.3.4.6.7"]}
        response = self.client.post(
            '/v2/apps/{app_id}/allowlist'.format(**locals()),
            allowlist)
        self.assertEqual(response.status_code, 400, response.data)
        # update other appsettings and allowlist should be retained
        settings = {'routable': False}
        response = self.client.post(
            '/v2/apps/{app.id}/settings'.format(**locals()),
            settings)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(set(addresses), set(app.appsettings_set.latest().allowlist))

    def test_kubernetes_service_failure(self, mock_requests):
        """
        Cause an Exception in kubernetes services
        """
        app_id = self.create_app()

        # scheduler.svc.update exception
        with mock.patch('scheduler.resources.service.Service.update') as mock_kube:
            mock_kube.side_effect = KubeException('Boom!')
            addresses = ["2.3.4.5"]
            url = '/v2/apps/{}/allowlist'.format(app_id)
            response = self.client.post(url, {'addresses': addresses})
            self.assertEqual(response.status_code, 201, response.data)

    def test_autoscale(self, mock_requests):
        """
        Test that autoscale can be applied
        """
        app_id = self.create_app()

        # create an autoscaling rule
        scale = {'autoscale': {'cmd': {'min': 2, 'max': 5, 'cpu_percent': 45}}}
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            scale
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIn('cmd', response.data['autoscale'])
        self.assertEqual(response.data['autoscale'], scale['autoscale'])

        # update
        scale = {'autoscale': {'cmd': {'min': 2, 'max': 8, 'cpu_percent': 45}}}
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            scale
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIn('cmd', response.data['autoscale'])
        self.assertEqual(response.data['autoscale'], scale['autoscale'])

        # create
        scale = {'autoscale': {'worker': {'min': 2, 'max': 5, 'cpu_percent': 45}}}
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            scale
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIn('worker', response.data['autoscale'])
        self.assertEqual(response.data['autoscale']['worker'], scale['autoscale']['worker'])

        # check that the cmd proc type is still there
        self.assertIn('cmd', response.data['autoscale'])

        # check that config fails if trying to unset non-existing proc type
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            {'autoscale': {'invalid_proctype': None}})
        self.assertEqual(response.status_code, 422, response.data)

        # remove a proc type
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            {'autoscale': {'worker': None}})
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotIn('worker', response.data['autoscale'])
        self.assertIn('cmd', response.data['autoscale'])

        # remove another proc type
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            {'autoscale': {'cmd': None}})
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotIn('cmd', response.data['autoscale'])

    def test_autoscale_validations(self, mock_requests):
        """
        Test that autoscale validations work
        """
        app_id = self.create_app()

        # Set one of the values that require a numeric value to a string
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            {'autoscale': {'cmd': {'min': 4, 'max': 5, 'cpu_percent': "t"}}}
        )
        self.assertEqual(response.status_code, 400, response.data)

        # Don't set one of the mandatory value
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            {'autoscale': {'cmd': {'min': 4, 'cpu_percent': 45}}}
        )
        self.assertEqual(response.status_code, 400, response.data)

    def test_settings_labels(self, mock_requests):
        """
        Test that labels can be applied
        """
        app_id = self.create_app()

        # create
        base_labels = {
            'label':
                {
                    'git_repo': 'https://github.com/drycc/controller',
                    'team': 'frontend',
                    'empty': ''
                }
        }
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            base_labels
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['label'], base_labels['label'])

        # update
        labels = {'label': {'team': 'backend'}}
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            labels
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['label']['team'], labels['label']['team'])
        self.assertEqual(response.data['label']['git_repo'], base_labels['label']['git_repo'])
        self.assertEqual(response.data['label']['empty'], base_labels['label']['empty'])

        # remove
        labels = {'label': {'git_repo': None}}
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            labels
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['label']['team'], 'backend')
        self.assertFalse('git_repo' in response.data['label'])
        self.assertEqual(response.data['label']['empty'], base_labels['label']['empty'])

        # error on remove non-exist label
        labels = {'label': {'git_repo': None}}
        response = self.client.post(
            '/v2/apps/{app_id}/settings'.format(**locals()),
            labels
        )
        self.assertEqual(response.status_code, 422, response.data)
