import base64
import requests
from typing import List, Dict
from requests_toolbelt import user_agent
from django.conf import settings
from api import __version__ as drycc_version


class ManagerAPI(object):

    def __init__(self):
        token = base64.b85encode(b"%s:%s" % (
            settings.WORKFLOW_MANAGER_ACCESS_KEY.encode("utf8"),
            settings.WORKFLOW_MANAGER_SECRET_KEY.encode("utf8"),
        )).decode("utf8")
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'token %s' % token,
            'User-Agent': user_agent('Drycc Controller ', drycc_version)
        }

    def requests(self, method, url, **kwargs):
        headers = kwargs.get("headers", {})
        headers.update(self.headers)
        kwargs["headers"] = headers
        requests.request(method, url, **kwargs)

    def get(self, url, params=None, **kwargs):
        return self.request('get', url, params=params, **kwargs)

    def options(self, url, **kwargs):
        return self.request('options', url, **kwargs)

    def head(self, url, **kwargs):
        kwargs.setdefault('allow_redirects', False)
        return self.request('head', url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.request('post', url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.request('put', url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return self.request('patch', url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('delete', url, **kwargs)


class User(ManagerAPI):

    def get_status(self, id):
        """
        {
            "is_active": False,
            "message": "The user is in arrears"
        }
        """
        url = f"{settings.WORKFLOW_MANAGER_URL}/users/{id}/status/"
        return self.get(url=url).json()


class Measurement(ManagerAPI):

    def post(self, measurements: List[Dict[str, str]]):
        """
        [
            {
                "app_id":  "test",
                "owner_id": "test",
                "name": web,
                "type": "CPU",
                "unit": "G"
                "usage": "2",
                "timestamp": "1609231998.9103732"
            }
        ]
        """
        url = "%s/measurements/" % settings.WORKFLOW_MANAGER_URL
        return self.post(url=url, json=measurements)
