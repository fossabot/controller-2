from scheduler.resources import Resource
from scheduler.exceptions import KubeHTTPException


class ServiceCatalog(Resource):
    api_version = 'servicecatalog.k8s.io/v1beta1'
    api_prefix = 'apis'
    short_name = 'svcat'

    @staticmethod
    def service_instance_manifest(namespace, name, version=None, **kwargs):
        labels = {
            'heritage': 'drycc',
        }
        data = {
            "apiVersion": 'servicecatalog.k8s.io/v1beta1',
            "kind": "ServiceInstance",
            "metadata": {
                "name": name,
                "namespace": namespace,
                'labels': labels
            },
            "spec": {
                "clusterServiceClassExternalName": kwargs.get('instance_class'),
                "clusterServicePlanExternalName": kwargs.get('instance_plan'),
            }
        }
        if version:
            data["metadata"]["resourceVersion"] = version
        if kwargs.get('parameters'):
            data["spec"]["parameters"] = kwargs.get('parameters')
        if kwargs.get('external_id'):
            data["spec"]["externalID"] = kwargs.get('external_id')
        return data

    def get_serviceclasses(self, namespace=None):
        if namespace is None:
            url = self.api('/clusterserviceclasses')
            message = 'get clusterserviceclasses'
        else:
            url = self.api('/namespaces/{}/serviceclasses', namespace)
            message = 'get serviceclasses ' + namespace
        response = self.http_get(url)
        if self.unhealthy(response.status_code):
            raise KubeHTTPException(response, message)
        return response

    def get_serviceplans(self, namespace=None):
        if namespace is None:
            url = self.api('/clusterserviceplans')
            message = 'get clusterserviceplans'
        else:
            url = self.api('/namespaces/{}/serviceplans', namespace)
            message = 'get serviceplans ' + namespace
        response = self.http_get(url)
        if self.unhealthy(response.status_code):
            raise KubeHTTPException(response, message)
        return response

    def get_instance(self, namespace, name=None):
        """
        Fetch a single serviceinstance or a list of serviceinstances
        """
        if name is not None:
            url = self.api('/namespaces/{}/serviceinstances/{}',
                           namespace, name)
            message = 'get serviceinstances ' + name
        else:
            url = self.api('/namespaces/{}/serviceinstances', namespace)
            message = 'get serviceinstances'
        response = self.http_get(url)
        if self.unhealthy(response.status_code):
            raise KubeHTTPException(response, message)
        return response

    def create_instance(self, namespace, name, **kwargs):
        """
        Create serviceinstances
        """
        url = self.api('/namespaces/{}/serviceinstances', namespace)
        data = self.service_instance_manifest(namespace, name, **kwargs)
        response = self.http_post(url, json=data)
        if not response.status_code == 201:
            raise KubeHTTPException(
                response,
                "create serviceinstances {}".format(namespace))
        return response

    def put_instance(self, namespace, name, version, **kwargs):
        """
        update serviceinstances
        """
        url = self.api('/namespaces/{}/serviceinstances/{}', namespace, name)
        data = self.service_instance_manifest(namespace, name, version, **kwargs)
        response = self.http_put(url, json=data)
        if not response.status_code == 200:
            raise KubeHTTPException(
                response,
                "update serviceinstances {}".format(namespace))
        return response

    def delete_instance(self, namespace, name):
        """
        Delete serviceinstances
        """
        url = self.api('/namespaces/{}/serviceinstances/{}', namespace,
                       name)
        response = self.http_delete(url)
        if self.unhealthy(response.status_code):
            raise KubeHTTPException(response, 'delete serviceinstance ' + name)
        return response

    @staticmethod
    def service_binding_manifest(namespace, name, version=None, **kwargs):
        labels = {
            'heritage': 'drycc',
        }
        data = {
            "apiVersion": 'servicecatalog.k8s.io/v1beta1',
            "kind": "ServiceBinding",
            "metadata": {
                "name": name,
                "namespace": namespace,
                'labels': labels
            },
            "spec": {
                "instanceRef": {
                    "name": name
                }
            }
        }
        if version:
            data["metadata"]["resourceVersion"] = version
        return data

    def get_binding(self, namespace, name=None):
        """
        Fetch a single servicebinding or a list of servicebindings
        """
        if name is not None:
            url = self.api('/namespaces/{}/servicebindings/{}',
                           namespace, name)
            message = 'get servicebindings ' + name
        else:
            url = self.api('/namespaces/{}/servicebindings', namespace)
            message = 'get servicebindings'
        response = self.http_get(url)
        if self.unhealthy(response.status_code):
            raise KubeHTTPException(response, message)
        return response

    def create_binding(self, namespace, name, **kwargs):
        """
        Create servicebindings
        """
        url = self.api('/namespaces/{}/servicebindings', namespace)
        data = self.service_binding_manifest(namespace, name, **kwargs)
        response = self.http_post(url, json=data)
        if not response.status_code == 201:
            raise KubeHTTPException(
                response,
                "create servicebindings {}".format(namespace))
        return response

    def delete_binding(self, namespace, name):
        """
        Delete servicebindings
        """
        url = self.api('/namespaces/{}/servicebindings/{}', namespace, name)
        response = self.http_delete(url)
        if self.unhealthy(response.status_code):
            raise KubeHTTPException(response,
                                    'delete servicebindings ' + name)
        return response
