from .rest_client.api import API
from .rest_client.resource import Resource
from .rest_client.request import make_request
from .rest_client.models import Request
from types import MethodType

import logging
from pprint import pformat


class PensandoDSSResource(Resource):
    pass

class PensandoDSSClient(object):
    def __init__(self, url, **kwargs):
        self._log = logging.getLogger()
        self._base_url = url

        if self._base_url[:-1] != "/":
            self._base_url + "/"
            
        self._username = kwargs.get("username", None)
        self._password = kwargs.get("password", None)
        self._tenant = kwargs.get("tenant", 'default')

        self.api = API(
            api_root_url=url,  # base api url
            params={},  # default params
            headers={},  # default headers
            timeout=10,  # default timeout in seconds
            append_slash=False,  # append slash to final url
            json_encode_body=True,  # encode body as json
            ssl_verify=kwargs.get("ssl_verify", None),
            resource_class=PensandoDSSResource,
        )

    def __str__(self):
        return pformat(self.api.get_resource_list())

    def login(self, username=None, password=None, tenant=None):
        if username:
            self._username = username
        if password:
            self._password = password
        if tenant:
            self._tenant = tenant

        response = self.api.v1.login.create(
            body={"username": self._username, "password": self._password,'tenant': self._tenant}
        ).client_response
        for cookie_name,cookie_value in  response.cookies.items():
            if cookie_name == 'sid':
                self.api.headers["Cookie"] = f"sid={cookie_value}"
                
                logging.debug("Got authenticaiton cookie")

        
        return True
