from celery import Celery
import pika
import boto3
import json
import os
from uuid import uuid4
import datetime
from copy import deepcopy
from uuid import uuid4
import time
import traceback

from boto3.dynamodb.conditions import Key, Attr
from helpers.common_helpers import parse_message
from helpers.worker_helpers import get_enabled_wells
import decimal

client_sqs = boto3.client('sqs')
client_sns = boto3.client('sns')
client_ecs = boto3.client('ecs')
q_url = os.environ['SQS_Q_URL']
worker_cluster = os.environ['WORKER_CLUSTER']
worker_service = os.environ['WORKER_SERVICE']
metadatastore = os.environ["DYNAMODB_METADATA"]

prediction_table_string = os.environ['PREDICTIONS_LIST_TABLE']
failure_table_string = os.environ['FAILURE_LIST_TABLE']
workflow_output_table_string = os.environ['WORKFLOW_OUTPUT_TABLE']

concurrency = int(os.environ["WORKER_CONCURRENCY"])

app = Celery(
    main='tasks',
    backend='amqp',
    broker='amqp://guest:guest@localhost/'
)



class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def get_non_assigned_predictions(predictions_table):
    # Determine enabled well here
    fe = Key('Enabled').eq(True)
    predictions_list_response = predictions_table.scan(
        FilterExpression=Attr("Assignee").not_exists() & fe
    )
    return predictions_list_response["Items"]

def get_non_assigned_failures(predictions_table):
    # fe = Key('Enabled').eq(True);
    predictions_list_response = predictions_table.scan(
        FilterExpression=Attr("Assignee").not_exists()
    )
    return predictions_list_response["Items"]

def get_enabled_wells(table):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table)
    response = table.scan(FilterExpression=Attr("Enabled").eq(True))
    response = [i["NodeID"] for i in response["Items"]]

    return response




def get_list_users_and_user_id():

    secrets_client = boto3.client('secretsmanager')
    # user_pool = "dev/enerplus/cognito/pool"
    user_pool = os.environ['USER_POOL']
    secrets_response = secrets_client.get_secret_value(SecretId=user_pool)
    user_pool_config = json.loads(secrets_response['SecretString'])
    user_pool_id = user_pool_config['user_pool_id']
    user_pool_region = user_pool_config['user_pool_region']

    client = boto3.client('cognito-idp', region_name=user_pool_region)
    # metadata_store_table = "tasq-meta-datastore-dev-MetaDataTable-OXCE4Y3LQ2MZ"
    metadata_table_string = os.environ['DYNAMODB_METADATA']
    response = client.list_users(
        UserPoolId=user_pool_id,
        AttributesToGet=[
            'sub',
            'email'
        ],
    )


    username_and_id_dict = {}
    for user in response["Users"]:
        # "user" looks like: {'Username': 'john', 'Attributes': [{'Name': 'sub', 'Value': '4e67e0b9-4e2f-4e8b-97e4-4c107b44d93d'}], 'UserCreateDate': datetime.datetime(2020, 3, 15, 12, 10, 17, 41000, tzinfo=tzlocal()), 'UserLastModifiedDate': datetime.datetime(2020, 3, 15, 12, 10, 17, 41000, tzinfo=tzlocal()), 'Enabled': True, 'UserStatus': 'FORCE_CHANGE_PASSWORD'}
        print("[x] Checking user {}".format(user["Username"]))
        time.sleep(5)
        response = client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=user["Username"]
        )
        AcceptingTasqs = True
        for att in response["UserAttributes"]:
            if att["Name"] == "custom:accepting_tasqs":
                AcceptingTasqs = att["Value"]

        if AcceptingTasqs in ["False", "false", False]:
            AcceptingTasqs = False
        if not AcceptingTasqs:
            print("[x] {} is not accepting tasqs".format(user["Username"]))
            continue
        time.sleep(4)
        response = client.admin_list_groups_for_user(
            Username=user["Username"],
            UserPoolId=user_pool_id
        )
        Team = None
        for group in response["Groups"]:
            if "Team_" in group["GroupName"]:
                Team = group["GroupName"]

        UserSub = None
        for attr in user["Attributes"]:
            if attr["Name"] == "sub":
                UserSub = attr["Value"]

        UserEmail = None
        for attr in user["Attributes"]:
            if attr["Name"] == "email":
                UserEmail = attr["Value"]


        username_and_id_dict[UserEmail] = {}
        username_and_id_dict[UserEmail]["UserID"] = UserSub # Grab the sub
        username_and_id_dict[UserEmail]["Team"] = Team # Set the user's team if exists

    return username_and_id_dict

def get_list_users_and_user_id():

    secrets_client = boto3.client('secretsmanager')
    # user_pool = "dev/enerplus/cognito/pool"
    user_pool = os.environ['USER_POOL']
    secrets_response = secrets_client.get_secret_value(SecretId=user_pool)
    user_pool_config = json.loads(secrets_response['SecretString'])
    user_pool_id = user_pool_config['user_pool_id']
    user_pool_region = user_pool_config['user_pool_region']

    client = boto3.client('cognito-idp', region_name=user_pool_region)
    # metadata_store_table = "tasq-meta-datastore-dev-MetaDataTable-OXCE4Y3LQ2MZ"
    metadata_table_string = os.environ['DYNAMODB_METADATA']
    response = client.list_users(
        UserPoolId=user_pool_id,
        AttributesToGet=[
            'sub',
            'email'
        ],
    )


    username_and_id_dict = {}
    for user in response["Users"]:
        # "user" looks like: {'Username': 'john', 'Attributes': [{'Name': 'sub', 'Value': '4e67e0b9-4e2f-4e8b-97e4-4c107b44d93d'}], 'UserCreateDate': datetime.datetime(2020, 3, 15, 12, 10, 17, 41000, tzinfo=tzlocal()), 'UserLastModifiedDate': datetime.datetime(2020, 3, 15, 12, 10, 17, 41000, tzinfo=tzlocal()), 'Enabled': True, 'UserStatus': 'FORCE_CHANGE_PASSWORD'}
        print("[x] Checking user {}".format(user["Username"]))
        time.sleep(5)
        response = client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=user["Username"]
        )
        AcceptingTasqs = True
        for att in response["UserAttributes"]:
            if att["Name"] == "custom:accepting_tasqs":
                AcceptingTasqs = att["Value"]

        if AcceptingTasqs in ["False", "false", False]:
            AcceptingTasqs = False
        if not AcceptingTasqs:
            print("[x] {} is not accepting tasqs".format(user["Username"]))
            continue
        time.sleep(4)
        response = client.admin_list_groups_for_user(
            Username=user["Username"],
            UserPoolId=user_pool_id
        )
        Team = None
        for group in response["Groups"]:
            if "Team_" in group["GroupName"]:
                Team = group["GroupName"]

        UserSub = None
        for attr in user["Attributes"]:
            if attr["Name"] == "sub":
                UserSub = attr["Value"]

        UserEmail = None
        for attr in user["Attributes"]:
            if attr["Name"] == "email":
                UserEmail = attr["Value"]


        username_and_id_dict[UserEmail] = {}
        username_and_id_dict[UserEmail]["UserID"] = UserSub # Grab the sub
        username_and_id_dict[UserEmail]["Team"] = Team # Set the user's team if exists

    return username_and_id_dict





def generate_work_to_SQS():
    well_list = get_enabled_wells(metadatastore)


    dynamodb = boto3.resource('dynamodb')
    predictions_table = dynamodb.Table(prediction_table_string)
    failure_table = dynamodb.Table(failure_table_string)

    unassigned_predictions = get_non_assigned_predictions(predictions_table)
    unassigned_failures = get_non_assigned_failures(failure_table)

    datetime_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    username_and_id_dict = get_list_users_and_user_id()

    predictions_msg_list = ["<>".join([str(uuid4()), json.dumps({
        "unassigned_prediction": json.dumps(n, cls=DecimalEncoder),
        "work_type": "process_state_changes",
        "table_name": prediction_table_string,
        "username_and_id_dict": username_and_id_dict,
        "from_time": datetime_now,
        "to_time": datetime_now
    })]) for n in unassigned_predictions]


    failure_msg_list = ["<>".join([str(uuid4()), json.dumps({
        "unassigned_prediction": json.dumps(n, cls=DecimalEncoder),
        "work_type": "process_failures",
        "table_name": failure_table_string,
        "username_and_id_dict": username_and_id_dict,
        "from_time": datetime_now,
        "to_time": datetime_now
    })]) for n in unassigned_failures]

    no_comms_msg_list = ["<>".join([str(uuid4()), json.dumps({
        "unassigned_prediction": json.dumps(n, cls=DecimalEncoder),
        "work_type": "check_no_comms",
        "username_and_id_dict": username_and_id_dict,
        "from_time": datetime_now,
        "to_time": datetime_now,
        "node_id": n
    })]) for n in well_list]


    workflow_decision_msg_list = ["<>".join([str(uuid4()), json.dumps({
        "work_type": "workflow_decision",
        "username_and_id_dict": username_and_id_dict,
        "from_time": datetime_now,
        "to_time": datetime_now,
    })])]

    # msg_list = workflow_decision_msg_list
    msg_list = failure_msg_list + predictions_msg_list + no_comms_msg_list + workflow_decision_msg_list
    [client_sqs.send_message(QueueUrl=q_url, MessageBody=m) for m in msg_list]


def get_num_messages():
    resp = client_sqs.get_queue_attributes(**{
        "QueueUrl": q_url,
        "AttributeNames": ["ApproximateNumberOfMessages"]
    })

    num_messages = resp["Attributes"]["ApproximateNumberOfMessages"]

    return int(num_messages)


def get_worker_stats():
    inspect = app.control.inspect()
    workers = inspect.active()
    if workers is not None:
        num_running_tasks = sum(
            [len(v) for k, v in workers.items() if 'off_time_calc_worker' not in k])
        avail_workers = [{k: v} for k, v in workers.items() if (
            len(v) < concurrency and 'off_time_calc_worker' not in k)]
    else:
        num_running_tasks = 0
        avail_workers = []
    num_avail_workers = len(avail_workers)

    workers = inspect.reserved()
    if workers is not None:
        num_tasks_taken_up = sum(
            len(v)
            for k, v in workers.items()
            if 'off_time_calc_worker' not in k
        )

    else:
        num_tasks_taken_up = 0

    return num_avail_workers, num_tasks_taken_up, num_running_tasks


def get_num_messages_in_local_queue():
    queue_connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=pika.credentials.PlainCredentials('guest', 'guest'),
        )
    )
    queue_channel = queue_connection.channel()
    queue = queue_channel.queue_declare(
        queue="celery",
        durable=True,
        exclusive=False,
        auto_delete=False
    )
    num_messages_in_default_queue = queue.method.message_count

    queue_channel.close()
    queue_connection.close()

    return num_messages_in_default_queue


def get_num_running_containers():
    worker_ecs_tasks_info = client_ecs.list_tasks(
        cluster=worker_cluster,
        serviceName=worker_service,
        launchType='FARGATE'
    )   # Type: dict
    return len(worker_ecs_tasks_info['taskArns'])


def get_message(num_message):
    try:
        response = client_sqs.receive_message(
            QueueUrl=q_url,
            MaxNumberOfMessages=num_message,
            AttributeNames=["SentTimestamp"],
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=1,
            WaitTimeSeconds=1
        )

        result = [{
            "message": r["Body"],
            "receipt_handle": r["ReceiptHandle"]
        } for r in response['Messages']]
    except:
        result = []

    return result


def populate_task_list_from_message(message, task_list):
    print('[x] Parsing message: {}'.format(message))
    msg_dict, msg_uuid, status_message = parse_message(message)
    print('[x] {}'.format(status_message))
    if msg_dict is None:
        print(['[x] Invalid message encountered, moving on....'])
    else:
        try:
            temp_dict_string = json.dumps(msg_dict)
            temp_msg = str(uuid4()) + '<>' + temp_dict_string
            task_list.append(temp_msg)
            print('[{}] Generated new task for workers: {}'.format(
                msg_uuid, temp_msg))
        except KeyError as e:
            print(
                '[{}] Fatal! Task dict is malformed, proper keys not found.'.format(msg_uuid))


def delete_message(receipt_handle):
    client_sqs.delete_message(
        QueueUrl=q_url,
        ReceiptHandle=receipt_handle
    )
