from simple_pensando_dss import PensandoDSSClient
from getpass import getpass
import os

username=os.environ.get('psm_username','admin')
password=os.environ.get('psm_password',getpass())
url=os.environ.get('psm_url',input("PSM URL:"))


psm=PensandoDSSClient(url,username=username,password=password,ssl_verify=False)
psm.login()
for ipcollection in psm.api.configs.network.v1.tenant.default.ipcollections.list().body['items']:
    ipcollection['spec']['addresses'].append('1.1.1.1')
    print(f"Adding 1.1.1.1 to {ipcollection['meta']['name']}")
    pprint(psm.api.configs.network.v1.tenant.default.ipcollections.create(result['meta']['name'],body=ipcollection))

    
