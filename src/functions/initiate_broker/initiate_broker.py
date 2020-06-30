import os
import boto3

ecs_client = boto3.client("ecs")

cluster_name = os.environ["BROKER_CLUSTER"]
service_name = os.environ["BROKER_SERVICE"]

def handler(event, context):
    response = ecs_client.update_service(
        cluster=cluster_name,
        service=service_name,
        desiredCount=1
    )

    print(response)
