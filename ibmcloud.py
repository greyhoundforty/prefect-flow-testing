import os
import json
import ibm_vpc
from ibm_cloud_sdk_core import ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from prefect import task, flow

from prefect.blocks.system import Secret

@task(name="Get DTS Credentials from Prefect Secret", log_prints=True)
def get_dts_credentials():
    dts_credentials = Secret.load("ibmcloud-dts-auth").get()
    ibmcloud_api_key = dts_credentials["ibmcloud_api_key"]
    return ibmcloud_api_key

@task(name="Set IAM Authenticator", log_prints=True)
def set_iam_authenticator(ibmcloud_api_key):
    authenticator = IAMAuthenticator(
        apikey=ibmcloud_api_key
    )
    return authenticator


# dts_credentials = dts_credentials["ibmcloud_api_key"]
# if not dts_credentials:
#     raise ValueError("IBM Cloud API key environment variable not found")

@task(name="Get VPC regions", log_prints=True)
def get_regions(authenticator):
    # use us-south endpoint to look up all regions
    service = ibm_vpc.VpcV1(authenticator=authenticator)
    service.set_service_url(f'https://us-south.iaas.cloud.ibm.com/v1')
    response = service.list_regions().get_result()
    regions = response['regions']
    region_names = [region['name'] for region in regions]
    return region_names

@task(name="Get VPCs in a region", log_prints=True)
def get_regional_vpcs(region, authenticator):
    service = ibm_vpc.VpcV1(authenticator=authenticator)
    service.set_service_url(f'https://{region}.iaas.cloud.ibm.com/v1')
    response = service.list_vpcs().get_result()
    vpcs = response['vpcs']
    return vpcs

@flow(name="Get All VPCs", log_prints=True)
def get_all_vpcs():
    ibmcloud_api_key = get_dts_credentials()
    authenticator = set_iam_authenticator(ibmcloud_api_key)
    regions = get_regions(authenticator)
    all_vpcs = []
    for region in regions:
        vpcs = get_regional_vpcs(region, authenticator)
        all_vpcs.extend(vpcs)
    return all_vpcs

if __name__ == "__main__":
    get_all_vpcs()

