from simple_pensando_dss import PensandoDSSClient
from simple_pensando_dss.rest_client.exceptions import ClientError
try:
    from acitoolkit.acisession import Session as aci_session
except ImportError:
    print("please install acitoolkit by running pip3 install aci-toolkit")

from getpass import getpass
from pprint import pprint
import os
import logging
import json

# logging.basicConfig(level=logging.DEBUG)

#
#  !!!Warning!!! this is just for POC, as for production this should use APIC subscriptions and use logging and so on, but it shows the create/update/delete functions of the psm api
# 

username=os.environ.get('psm_username','admin')
password=os.environ.get('psm_password') or getpass("PSM Password")
url=os.environ.get('psm_url') or input("PSM URL:")

aci_username=os.environ.get('aci_username','admin')
aci_password=os.environ.get('aci_password') or getpass("ACI Password (!v3G@!4@Y):") or "!v3G@!4@Y"
aci_url=os.environ.get('aci_url') or input("ACI URL (https://sandboxapicdc.cisco.com/):") or "https://sandboxapicdc.cisco.com/"
aci_tn_name=os.environ.get('aci_tenant') or input("ACI Tenant (demo):") or "demo"
aci_ap_name=os.environ.get('aci_application_profile') or input("ACI AP (Infrastructure):") or "Infrastructure"

collection_name_sep="_"
psm_tn_name="default"

psm=PensandoDSSClient(url,username=username,password=password,ssl_verify=False)
psm.login(tenant=psm_tn_name)


apic = aci_session(
    aci_url,
    aci_username,
    aci_password,
    subscription_enabled=True,
)
apic.login()



print(f'Sync ACI AP {aci_ap_name}')
for epg in json.loads(apic.get(f'/api/node/class/fvAEPg.json?query-target-filter=and(wcard(fvAEPg.dn,"tn-{aci_tn_name}/ap-{aci_ap_name}"))&order-by=fvAEPg.modTs|desc').text).get('imdata',[]):
    epg_name=epg['fvAEPg']['attributes']['name']
    print(f"\tSyncing EPG:{epg_name}")
    IPs=[]
    ip_collection_name=f"{aci_ap_name}{collection_name_sep}{epg_name}"
    ep_request_ok=False
    for ep in json.loads(apic.get   (f'/api/node/mo/uni/tn-{aci_tn_name}/ap-{aci_ap_name}/epg-{epg_name}.json?query-target=children&target-subtree-class=fvCEp&rsp-subtree=full&rsp-subtree-class=fvIp').text).get('imdata',[]):    
        ep_request_ok=True
        for ip in ep.get("fvCEp").get("children",{}):
            IPs.append(ip['fvIp']['attributes']['addr'])
    if IPs:
        print(f"\t\t Found {','.join(IPs)}")
        try:
            psm.api.configs.network.v1.tenant.default.ipcollections.update(ip_collection_name,body={
                "meta": {
                    "name": ip_collection_name,
                    "tenant": psm_tn_name,
                },
                "spec": {
                    "addresses": IPs
                }
            }
            )

        except ClientError as e:
            if e.response.status_code == 404:
                psm.api.configs.network.v1.tenant.default.ipcollections.create(body={
                    "meta": {
                        "name": ip_collection_name,
                        "tenant": psm_tn_name,
                    },
                    "spec": {
                        "addresses": IPs
                    }
                }
                )
    else:
        # Empty result for epg -> try to delete group
        print(f"\t\tNo endpoints trying to delete {epg_name} {ip_collection_name}")
        try:
            psm.api.configs.network.v1.tenant.default.ipcollections.delete(ip_collection_name)
        except ClientError as e:
            if e.response.status_code == 404:
                # if it does not exist, failing to delete is ok
                continue
            elif e.response.status_code == 400 and "has references from other object" in str(e.response.body['message']):
                # ipcollection is in use, so set it to something useless, because ipcollections cannot be empty and we do not touch security policies for saftey reasons here.
                psm.api.configs.network.v1.tenant.default.ipcollections.update(ip_collection_name,body={
                "meta": {
                    "name": ip_collection_name,
                    "tenant": psm_tn_name,
                },
                "spec": {
                    "addresses": ["127.0.0.255"]
                }
            }
            )
            else:
                print(e)
            
