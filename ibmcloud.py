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

@task(name="Get VPC regions", log_prints=True)
def get_regions(authenticator):
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
    vpc_count = len(vpcs)
    return vpc_count

@flow(name="Get All VPCs", log_prints=True)
def get_all_vpcs():
    ibmcloud_api_key = get_dts_credentials()
    authenticator = set_iam_authenticator(ibmcloud_api_key)
    regions = get_regions(authenticator)
    region_vpc_counts = []
    for region in regions:
        vpc_count = get_regional_vpcs(region, authenticator)
        region_vpc_counts.append({
            "region": region,
            "vpc_count": vpc_count
        })
    return json.dumps(region_vpc_counts)

if __name__ == "__main__":
    get_all_vpcs()
