import boto3
import datetime
import time
import os
from collections import deque

from helpers.broker_helpers import get_num_messages, \
    get_num_running_containers, \
    get_worker_stats, \
    get_num_messages_in_local_queue
from helpers.broker_helpers import get_message, delete_message, generate_work_to_SQS
from helpers.broker_helpers import populate_task_list_from_message
from worker import do_work

cloudwatch_client = boto3.client('cloudwatch')
ecs_client = boto3.client("ecs")
custom_metric_name = os.environ['WORKER_SCALE_CUSTOM_METRIC_NAME']
custom_metric_unit = os.environ['WORKER_SCALE_CUSTOM_METRIC_UNIT']
custom_metric_namespace = os.environ['WORKER_SCALE_CUSTOM_METRIC_NAMESPACE']
custom_metric_ideal_value = int(os.environ['WORKER_SCALE_CUSTOM_METRIC_IDEAL_VALUE'])
cluster_name = os.environ["WORKER_CLUSTER"]
worker_service = os.environ["WORKER_SERVICE"]

# Spin up workers and generate work queue to SQS
ecs_client.update_service(
    cluster=cluster_name,
    service=worker_service,
    desiredCount=2
)
generate_work_to_SQS()

print("[x] Listening to SQS Queue...")
current_tasks_list = deque()
num_messages = get_num_messages()
num_default_tasks_in_local_queue = get_num_messages_in_local_queue()

while num_messages > 0 or num_default_tasks_in_local_queue > 0:
    num_messages = get_num_messages()
    num_avail_workers, num_tasks_taken_up, num_running_tasks = get_worker_stats()
    num_running_worker_containers = get_num_running_containers()
    num_default_tasks_in_local_queue = get_num_messages_in_local_queue()

    print("[x] Tasks reserved by workers: {} | Running tasks: {} | Available workers: {} | Remaining Messages: {}".format(
        num_tasks_taken_up, num_running_tasks, num_avail_workers, num_messages))
    print("[x] Running default worker containers: {}".format(
        num_running_worker_containers))
    print("[x] {} tasks waiting in default queue".format(num_default_tasks_in_local_queue))


    if num_messages == 0:
        print("[x] Remaining Messages: {} | Available Workers: {}".format(
            num_messages, num_avail_workers))
        time.sleep(60)

    if num_avail_workers > 0 and num_messages > 0:
        num_messages_to_fetch = 10 #min(int(num_avail_workers/1), 10)
        num_messages_to_fetch = max(1, num_messages_to_fetch)
        package = get_message(num_messages_to_fetch)
        slots_filled = 0

        for i, p in enumerate(package):

            print("[{}] Processing Message: \"{}\" | Remaining: {}".format(
                datetime.datetime.utcnow(),
                p["message"],
                num_messages - (i+1)
            ))

            populate_task_list_from_message(p["message"], current_tasks_list)
            print("[x] Available workers: {} | Tasks generated for workers: {}".format(
                num_avail_workers - slots_filled, len(current_tasks_list)))

            slots_filled += len(current_tasks_list)
            for _ in range(len(current_tasks_list)):
                do_work.apply_async(args=[current_tasks_list.popleft(), "State Change Detection"])


            delete_message(p["receipt_handle"])

services = ecs_client.list_services(cluster=cluster_name)["serviceArns"]

time.sleep(30)

[ecs_client.update_service(cluster=cluster_name, service=s, desiredCount=0) for s in services]
