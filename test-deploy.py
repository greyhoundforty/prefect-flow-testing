from prefect import flow

# Source for the code to deploy (here, a GitHub repo)
SOURCE_REPO="https://github.com/greyhoundforty/prefect-flow-testing.git"

if __name__ == "__main__":
    flow.from_source(
        source=SOURCE_REPO,
        entrypoint="list-vpcs-flow.py:get_all_vpcs", # Specific flow to run
    ).deploy(
        name="get-vpc-count-deployment",
        work_pool_name="rst-managed-pool", # Work pool target
        cron="* */4 * * *", # Cron schedule (every minute)
    )
