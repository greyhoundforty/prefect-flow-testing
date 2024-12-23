import os
import json
import ibm_vpc
from ibm_cloud_sdk_core import ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from prefect import task, flow
from prefect.blocks.system import Secret
from prefect.cache_policies import TASK_SOURCE

# 1. Import IceCream
from icecream import ic

# 2. (Optional) Configure IceCream output.
#    For example, disable prefix or redirect to a custom function:
ic.configureOutput(prefix='IC debug | ', outputFunction=print)

@task(name="Get DTS Credentials from Prefect Secret", log_prints=True, cache_policy=TASK_SOURCE)
def get_dts_credentials():
    # 3. Use IceCream for debugging
    ic("Fetching DTS credentials from Prefect Secret...")
    dts_credentials = Secret.load("ibmcloud-dts-auth").get()
    ic(dts_credentials)  # Will display the dictionary so you can check its structure
    
    ibmcloud_api_key = dts_credentials["ibmcloud_api_key"]
    return ibmcloud_api_key

@task(name="Set IAM Authenticator", log_prints=True, cache_policy=TASK_SOURCE)
def set_iam_authenticator(ibmcloud_api_key):
    ic("Setting up IAM Authenticator...")
    authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
    ic(authenticator)  # Show the authenticator object
    return authenticator

@task(name="Get VPC regions", log_prints=True, cache_policy=TASK_SOURCE)
def get_regions(authenticator):
    ic("Listing VPC regions...")
    service = ibm_vpc.VpcV1(authenticator=authenticator)
    service.set_service_url('https://us-south.iaas.cloud.ibm.com/v1')
    
    # Using try/except helps catch and debug errors
    try:
        response = service.list_regions().get_result()
    except ApiException as e:
        ic("ApiException occurred while listing regions")
        ic(e)
        raise  # Reraise or handle
    
    regions = response['regions']
    region_names = [region['name'] for region in regions]
    ic(region_names)  # Show the region names
    return region_names

@task(name="Get VPCs in a region", log_prints=True, cache_policy=TASK_SOURCE)
def get_regional_vpcs(region, authenticator):
    ic(f"Listing VPCs in region: {region}")
    service = ibm_vpc.VpcV1(authenticator=authenticator)
    service.set_service_url(f'https://{region}.iaas.cloud.ibm.com/v1')
    
    try:
        response = service.list_vpcs().get_result()
    except ApiException as e:
        ic("ApiException occurred while listing VPCs")
        ic(e)
        raise
    
    vpcs = response['vpcs']
    vpc_count = len(vpcs)
    ic(f"Found {vpc_count} VPCs in region {region}")
    return vpc_count

@flow(name="Get All VPCs", log_prints=True)
def get_all_vpcs():
    ic("Starting flow to get all VPCs...")
    ibmcloud_api_key = get_dts_credentials()
    authenticator = set_iam_authenticator(ibmcloud_api_key)
    
    regions = get_regions(authenticator)
    region_vpc_counts = []
    
    for region in regions:
        vpc_count = get_regional_vpcs(region, authenticator)
        region_vpc_counts.append({"region": region, "vpc_count": vpc_count})
    
    ic("Final region and VPC counts:", region_vpc_counts)
    return json.dumps(region_vpc_counts)

if __name__ == "__main__":
    get_all_vpcs()

