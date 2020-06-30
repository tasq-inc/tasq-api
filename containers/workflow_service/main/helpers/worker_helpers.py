import pandas as pd
import numpy as np
import boto3
from datetime import date, datetime
from datetime import timedelta
from boto3.dynamodb.conditions import Attr, Key
from s3fs import S3FileSystem
from uuid import uuid4
from copy import deepcopy
import json
from decimal import Decimal
import decimal
import pyarrow.parquet as pq
import pyarrow as pa
import os
import time
from helpers.Classes import StateObject, NodeRouteObject, LastStateChangeObject, WellObject
from requests_aws4auth import AWS4Auth
import requests
import random

session = requests.Session()
credentials = boto3.session.Session().get_credentials()
session.auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    boto3.session.Session().region_name,
    'appsync',
    session_token=credentials.token
)


dynamodb = boto3.resource("dynamodb")


def get_ingest_done_message(msg_dict):
    ingest_done_msg_dict = deepcopy(msg_dict)
    ingest_done_message = json.dumps(ingest_done_msg_dict)
    ingest_done_message = str(uuid4()) + '<>' + ingest_done_message

    return ingest_done_message


def _stringify_list_of_dicts(slice_df):
    slice_df = slice_df[['EventID', 'Note', 'UserID']]
    return str(slice_df.to_dict('records'))



def get_enabled_wells(table):
    table = dynamodb.Table(table)
    response = table.scan(FilterExpression=Attr("Enabled").eq(True))
    response_array = []
    for index, i in enumerate(response["Items"]):
        response_array.append(i["NodeID"])
        # if index > 2:
        #     break
        # response = [i["NodeID"] for i in response["Items"] if index > 2: break]
    print("ENABLED WELLS: ")
    print(response_array)
    return response_array



def grab_events_data(api_url, current_date, from_time_obj, to_time_obj, node_id):

    duration_days = current_date - from_time_obj
    delta = current_date - from_time_obj
    delta_days = delta.days

    from_time_str = from_time_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_time_str = to_time_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

    query = """
        query data {{
            list_node_events(
                nodeid:"{node}",
                from_time:"{f_time}",
                to_time:"{t_time}"
            ) {{
    dataset
            }}
        }}
    """ .format(
            node=node_id,
            f_time=from_time_str,
            t_time=to_time_str
    )

    response = session.request(
        url=api_url, method="POST", json={'query': query})
    data = response.json()

    return({
        "nodeid": node_id,
        "dataset": data["data"]["list_node_events"]["dataset"]
    })




def retrieve_single_user_from_team_dict(team):
    secrets_client = boto3.client('secretsmanager')
    user_pool = "dev/enerplus/cognito/pool"
    # user_pool = os.environ['USER_POOL']
    should_assign_test_user = os.environ['SHOULD_ASSIGN_TEST_USER']

    secrets_response = secrets_client.get_secret_value(SecretId=user_pool)
    user_pool_config = json.loads(secrets_response['SecretString'])
    user_pool_id = user_pool_config['user_pool_id']
    user_pool_region = user_pool_config['user_pool_region']

    client = boto3.client('cognito-idp', region_name=user_pool_region)
    time.sleep(4)
    response = client.list_users_in_group(
        UserPoolId=user_pool_id,
        GroupName=team
    )
    available_users = []

    check_string_val = "false"
    if should_assign_test_user and should_assign_test_user != "false" and should_assign_test_user != "False":
        check_string_val = "true"
    for User in response["Users"]:
        contains_test_user_attr = False
        should_add_user = False
        AcceptingTasqs = True
        for Attribute in User["Attributes"]:
            if Attribute["Name"] == "custom:accepting_tasqs":
                AcceptingTasqsVal = Attribute["Value"]
                if AcceptingTasqsVal == "False" or AcceptingTasqsVal == "false" or AcceptingTasqsVal == False:
                    should_add_user = False
            if (Attribute["Name"] == "custom:is_test_user"):
                contains_test_user_attr = True
                if (Attribute["Value"] == check_string_val):
                    should_add_user = True
        if (not contains_test_user_attr) and (not should_assign_test_user):
            should_add_user = True

        if should_add_user and AcceptingTasqs:
            available_users.append(User)

    user = random.choice(available_users)

    sub = None
    user_email = None
    for att in user["Attributes"]:
        if att["Name"] == "sub":
            sub = att["Value"]
        if att["Name"] == "email":
            user_email = att["Value"]


    response = client.admin_list_groups_for_user(
        Username=user_email,
        UserPoolId=user_pool_id
    )

    Role = None
    groups = response["Groups"]
    for group in groups:
        if "Automation" in group["GroupName"]:
            Role = "Automation"
        if "Engineers" in group["GroupName"]:
            Role = "Engineers"
        if "FieldOperator" in group["GroupName"]:
            Role = "FieldOperator"
        if "Intervention" in group["GroupName"]:
            Role = "Intervention"
        if "Maintenance" in group["GroupName"]:
            Role = "Maintenance"
        if "Operators" in group["GroupName"]:
            Role = "Operators"
        if "Optimizer" in group["GroupName"]:
            Role = "Optimizer"
        if "SafetyCritical" in group["GroupName"]:
            Role = "SafetyCritical"


    assignee_dict = {
        "UserEmail":user_email,
        "UserID": sub,
        "Role": Role
    }
    return assignee_dict






def retrieve_single_user_from_role_dict(role):
    secrets_client = boto3.client('secretsmanager')
    user_pool = "dev/enerplus/cognito/pool"
    # user_pool = os.environ['USER_POOL']
    should_assign_test_user = os.environ['SHOULD_ASSIGN_TEST_USER']

    secrets_response = secrets_client.get_secret_value(SecretId=user_pool)
    user_pool_config = json.loads(secrets_response['SecretString'])
    user_pool_id = user_pool_config['user_pool_id']
    user_pool_region = user_pool_config['user_pool_region']

    client = boto3.client('cognito-idp', region_name=user_pool_region)
    time.sleep(4)
    response = client.list_users_in_group(
        UserPoolId=user_pool_id,
        GroupName=role
    )
    available_users = []

    check_string_val = "false"
    if should_assign_test_user and should_assign_test_user != "false" and should_assign_test_user != "False":
        check_string_val = "true"
    for User in response["Users"]:
        contains_test_user_attr = False
        should_add_user = False
        AcceptingTasqs = True
        for Attribute in User["Attributes"]:
            if Attribute["Name"] == "custom:accepting_tasqs":
                AcceptingTasqsVal = Attribute["Value"]
                if AcceptingTasqsVal == "False" or AcceptingTasqsVal == "false" or AcceptingTasqsVal == False:
                    should_add_user = False
            if (Attribute["Name"] == "custom:is_test_user"):
                contains_test_user_attr = True
                if (Attribute["Value"] == check_string_val):
                    should_add_user = True
        if (not contains_test_user_attr) and (not should_assign_test_user):
            should_add_user = True

        if should_add_user and AcceptingTasqs:
            available_users.append(User)

    user = random.choice(available_users)

    sub = None
    user_email = None
    print("_____________ response ___________ ")
    print(user)
    for att in user["Attributes"]:
        if att["Name"] == "sub":
            sub = att["Value"]
        if att["Name"] == "email":
            user_email = att["Value"]


    # response = client.admin_list_groups_for_user(
    #     Username=user_email,
    #     UserPoolId=user_pool_id
    # )

    # Role = None
    # groups = response["Groups"]
    # for group in groups:
    #     if "Automation" in group["GroupName"]:
    #         Role = "Automation"
    #     if "Engineers" in group["GroupName"]:
    #         Role = "Engineers"
    #     if "FieldOperator" in group["GroupName"]:
    #         Role = "FieldOperator"
    #     if "Intervention" in group["GroupName"]:
    #         Role = "Intervention"
    #     if "Maintenance" in group["GroupName"]:
    #         Role = "Maintenance"
    #     if "Operators" in group["GroupName"]:
    #         Role = "Operators"
    #     if "Optimizer" in group["GroupName"]:
    #         Role = "Optimizer"
    #     if "SafetyCritical" in group["GroupName"]:
    #         Role = "SafetyCritical"


    assignee_dict = {
        "UserEmail":user_email,
        "UserID": sub,
        "Role": role
    }
    return assignee_dict










def grab_card_data(api_url, current_date, from_time_obj, to_time_obj, node_id):

    duration_days = current_date - from_time_obj
    delta = current_date - from_time_obj
    delta_days = delta.days

    from_time_str = from_time_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_time_str = to_time_obj.strftime("%Y-%m-%dT%H:%M:%SZ")


    query = """
        query data {{
            get_clean_ts_data_time_range(
                nodeid:"{node}",
                description:"{description}",
                from_time:"{f_time}",
                to_time:"{t_time}"
            ) {{
    dataset
            }}
        }}
    """ .format(
            node=node_id,
            description="SPM",
            operator="Enerplus",
            f_time=from_time_str,
            t_time=to_time_str
    )
    spm_response = session.request(
        url=api_url, method="POST", json={'query': query})
    spm_data = spm_response.json()



    query = """
        query data {{
            get_clean_ts_data_time_range(
                nodeid:"{node}",
                description:"{description}",
                from_time:"{f_time}",
                to_time:"{t_time}"
            ) {{
    dataset
            }}
        }}
    """ .format(
            node=node_id,
            description="StrokeLength",
            operator="Enerplus",
            f_time=from_time_str,
            t_time=to_time_str
    )
    stroke_length_response = session.request(
        url=api_url, method="POST", json={'query': query})
    stroke_length_data = stroke_length_response.json()


    spm_time_array = []
    spm_array = []
    stroke_length_time_array = []
    stroke_length_array = []

    if "time" in json.loads(spm_data["data"]["get_clean_ts_data_time_range"]["dataset"]):
        
        spm_time_array = json.loads(spm_data["data"]["get_clean_ts_data_time_range"]["dataset"])["time"]
        spm_array = json.loads(spm_data["data"]["get_clean_ts_data_time_range"]["dataset"])["Value"]

    if "time" in json.loads(stroke_length_data["data"]["get_clean_ts_data_time_range"]["dataset"]):
        stroke_length_time_array = json.loads(stroke_length_data["data"]["get_clean_ts_data_time_range"]["dataset"])["time"]
        stroke_length_array = json.loads(stroke_length_data["data"]["get_clean_ts_data_time_range"]["dataset"])["Value"]

    
    spm_formatted_list = pd.DataFrame(
    {
        'time': spm_time_array,
        'SPM': spm_array
    })
    stroke_length_formatted_list = pd.DataFrame(
    {
        'time': stroke_length_time_array,
        'StrokeLength': stroke_length_array
    })


    combined_merged_df = pd.merge(spm_formatted_list, stroke_length_formatted_list, on='time', how='inner')

    combined_merged_df.sort_values(by=['time'], inplace=True, ascending=False)
    return combined_merged_df




def grab_well_test_data(api_url, current_date, from_time_obj, to_time_obj, node_id):
    duration_days = current_date - from_time_obj
    delta = current_date - from_time_obj
    delta_days = delta.days

    from_time = from_time_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_time = to_time_obj.strftime("%Y-%m-%dT%H:%M:%SZ")



    to_time_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    from_time_str = from_time_obj.strftime("%Y-%m-%dT%H:%M:%S")


    query = """
        query data {{
            get_well_test_data_time_range(
                nodeid:"{node}",
                from_date:"{f_time}",
                to_date:"{t_time}"
            ) {{
    nodeid
    oil_rate
    gas_rate
    water_rate
    date
            }}
        }}
    """ .format(
            node=node_id,
            f_time=from_time_str,
            t_time=to_time_str
    )
    response = session.request(
        url=api_url, method="POST", json={'query': query})

    print(query)
    print("RESPONSE.JSON: ")
    print(response.json())
    print("____________________")
    print(response.json()["data"])
    return response.json()["data"]["get_well_test_data_time_range"]






def grab_node_signals_data(api_url, node_id, description, from_time):
    to_time_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    from_time_str = from_time.strftime("%Y-%m-%dT%H:%M:%S")

    query = """
        query data {{
            get_clean_ts_data_time_range(
                nodeid:"{node}",
                description:"{desc}",
                from_time:"{f_time}",
                to_time:"{t_time}"
            ) {{
    nodeid
    description
    dataset
    exc_time
            }}
        }}
    """ .format(
            node=node_id,
            desc=description,
            f_time=from_time_str,
            t_time=to_time_str
    )
    response = session.request(
        url=api_url, method="POST", json={'query': query})
    response = response.json()
    response["data"]["get_clean_ts_data_time_range"]["dataset"] = json.loads(response["data"]["get_clean_ts_data_time_range"]["dataset"])
    return response["data"]["get_clean_ts_data_time_range"]




def populate_node_details_dict(node_details_dict):
    api_url = "https://lnc6uax525cxtjg5gxfilsluhu.appsync-api.us-east-2.amazonaws.com/graphql"

    current_date = datetime.now()
    from_time_obj = current_date - timedelta(days=4)
    to_time_obj = current_date + timedelta(days=1)
    from_time = from_time_obj.strftime("%Y-%m-%dT%H:%M:%S")
    to_time = to_time_obj.strftime("%Y-%m-%dT%H:%M:%S")

    from_time_well_test_obj = current_date - timedelta(days=5)
    to_time_well_test_obj = current_date + timedelta(days=1)
    from_well_test_time = from_time_obj.strftime("%Y-%m-%dT%H:%M:%S")
    to_well_test_time = to_time_obj.strftime("%Y-%m-%dT%H:%M:%S")


    for node_id, value in node_details_dict.items():
        print("[x] Storing well test data for {}".format(node_id))
        # ***********************************************
        # ************ GET WELL TEST DATA ***************
        # ***********************************************
        node_details_dict[node_id]["WellTestData"] = grab_well_test_data(api_url, current_date, from_time_well_test_obj, to_time_well_test_obj, node_id)
        print("[x] Storing card data for {}".format(node_id))
        # ***********************************************
        # ************ GET CARD DATA ***************
        # ***********************************************
        node_details_dict[node_id]["CardData"] = grab_card_data(api_url, current_date, from_time_well_test_obj, to_time_well_test_obj, node_id)
        print("[x] Storing event data for {}".format(node_id))
        # ***********************************************
        # ************ GET EVENT DATA ***************
        # ***********************************************
        node_details_dict[node_id]["EventData"] = grab_events_data(api_url, current_date, from_time_well_test_obj, to_time_well_test_obj, node_id)
        print("[x] Storing signal data for {}".format(node_id))
        # ***********************************************
        # ************** GET SIGNAL DATA ****************
        # ***********************************************
        description_array = ["Polished Rod HP", "Current Percent Run", "Pump Fillage", "Last Stroke Min Load", "Fluid Load", "Last Stroke Peak Load", "Calculated Run Status", "Consecutive Pumpoff Strokes Allowed"]
        node_details_dict[node_id]["SignalsData"] = {}
        for description in description_array:
            node_details_dict[node_id]["SignalsData"][description] = grab_node_signals_data(api_url, node_id, description, from_time_obj)

            if len(node_details_dict[node_id]["SignalsData"][description]["dataset"]) > 0:
                formatted_list = pd.DataFrame(
                {
                'time': node_details_dict[node_id]["SignalsData"][description]["dataset"]["time"],
                'Value': node_details_dict[node_id]["SignalsData"][description]["dataset"]["Value"]
                })
                formatted_list.sort_values(by=['time'], inplace=True, ascending=False)
                node_details_dict[node_id]["SignalsData"][description]["dataset"] = formatted_list
            else:
                node_details_dict[node_id]["SignalsData"][description]["dataset"] = pd.DataFrame()
    return node_details_dict





def retrieve_default_user_assignment_dict():
    # metadata_table_string = "tasq-meta-datastore-dev-MetaDataTable-OXCE4Y3LQ2MZ"
    metadata_table_string = os.environ['DYNAMODB_METADATA']
    dynamodb = boto3.resource('dynamodb')
    metadata_table = dynamodb.Table(metadata_table_string)

    metadata_response = metadata_table.query(
        IndexName='EnabledString-index',
        KeyConditionExpression=Key('EnabledString').eq("True")
    )

    default_user_assignment_dict = {}
    for metadata_response in metadata_response["Items"]:
        default_user_assignment_dict[metadata_response["NodeID"]] = metadata_response["Username"]
    return default_user_assignment_dict



def get_default_user_for_node(node_id, default_user_assignment_dict):

    if node_id in default_user_assignment_dict:
        # print("[x] Adding {} as default assignee for {}".format(default_username, prediction_id))
        return default_user_assignment_dict[node_id]
    print("[x] No default user found for {}".format(node_id))
    return "jgeorge@enerplus.com"



def get_team_for_user(username):
    secrets_client = boto3.client('secretsmanager')
    user_pool = os.environ['USER_POOL']
    # user_pool = "dev/enerplus/cognito/pool"
    secrets_response = secrets_client.get_secret_value(SecretId=user_pool)
    user_pool_config = json.loads(secrets_response['SecretString'])
    user_pool_id = user_pool_config['user_pool_id']
    user_pool_region = user_pool_config['user_pool_region']

    client = boto3.client('cognito-idp', region_name=user_pool_region)

    response = client.admin_list_groups_for_user(
        Username=username,
        UserPoolId=user_pool_id
    )

    Team = None
    groups = response["Groups"]
    for group in groups:
        if "Team_" in group["GroupName"]:
            Team = group["GroupName"]


    return Team




def determine_if_is_tasq_prediction_type(condition_results_dict):
    for key, condition_result in condition_results_dict.items():
        if (
            "condition" in condition_result
            and "condition_definition" in condition_result["condition"]
            and condition_result["data_feed"] == "TASQ_PREDICTION"
        ):
            return condition_result["result"] # The result contains the item from the PredictionsTable








""" Returns True or False depending on if the well is currently in a no_comms state
No comms is a period in which a well is not recieving new data.

Params:
    - node_id (The id of the well)

Returns:
    - True or False
"""
def get_well_state_details(node_id):
    s3Bucket_well_state = os.environ["WELL_STATE_S3"]
    # s3Bucket_well_state = "well-state-dev"
    node_id = node_id.replace(" ", "_")
    node_id = node_id.lower()
    s3 = boto3.client('s3', region_name="us-east-2")
    obj = s3.get_object(Bucket=s3Bucket_well_state, Key=node_id + "/well_state.txt")
    formated_json_string = obj['Body'].read().decode("utf-8")

    print("formated_json_string: ")
    print(formated_json_string)

    formated_json = None
    try:
        formated_json = json.loads(formated_json_string)
    except:
        formated_json_string = formated_json_string.replace("'","\"")
        formated_json_string = formated_json_string.replace(": False,",": \"False\",")
        formated_json_string = formated_json_string.replace(": False}",": \"False\"}")
        formated_json_string = formated_json_string.replace(")}","}")
        formated_json_string = formated_json_string.replace("),",",")
        formated_json_string = formated_json_string.replace(": Decimal(",": ")

        print(formated_json_string)
        formated_json = json.loads(formated_json_string)

    production_average = None
    if "ProductionAverage" in formated_json:
        with decimal.localcontext(boto3.dynamodb.types.DYNAMODB_CONTEXT) as ctx:
            ctx.traps[decimal.Inexact] = False
            ctx.traps[decimal.Rounded] = False
            production_average = ctx.create_decimal_from_float(formated_json["ProductionAverage"])
    return formated_json["NoComms"], production_average

    # Using the descriptions "Fluid Load", "Last Stroke Peak Load", "Last Stroke Min Load", and "Polished Rod HP",
    # we can extract the two most recent values from each of these responses.
    # If the last two values for each description are equivalent,
    # we can assume with a high level of confidence the well is in a no-comms state.
    return check_no_comms_status_values(fluid_load_dataset, peak_load_dataset, min_load_dataset, polished_rod_hp_dataset)


def get_last_state_change_object(node_id):
    predictions_list_table = os.environ['PREDICTIONS_LIST_TABLE']
    # predictions_list_table = "tasq-detect-state-change-dev-PredictionTable-OWFZZ8X5FOG8"
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(predictions_list_table)

    response = table.query(
        IndexName='NodeID-index',
        KeyConditionExpression=Key('NodeID').eq(node_id)
    )
    items = response["Items"]
    items = list(reversed(sorted(items, key=lambda x: datetime.strptime(x['StateChangeDate'], '%Y-%m-%dT%H:%M:%S'))))
    if items:
        return items[0]
    return None



def get_route_for_node(node_id):
    metadata_store_table = os.environ['DYNAMODB_METADATA']
    # metadata_store_table = "tasq-meta-datastore-dev-MetaDataTable-OXCE4Y3LQ2MZ"
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(metadata_store_table)
    response = table.query(
        KeyConditionExpression=Key('NodeID').eq(node_id)
    )
    if len(response["Items"]) > 0:
        route_string = response["Items"][0]["Route"]
        route_id = response["Items"][0]["RouteID"]
        contact_list_id = response["Items"][0]["ContactListID"]
        return NodeRouteObject(route_string, route_id, contact_list_id)

    else:
        return None




# Constructs the well object for use in the assignment decision tree
def get_well_object(node_id, prediction_id, default_user_assignment_dict, prediction_type, username_and_id_dict):
    print("[x] Fetching the default user for {}".format(node_id))
    default_username = get_default_user_for_node(node_id, default_user_assignment_dict)
    print("[x] Fetching user_id and team for {}".format(default_username))
    default_assignee_user_id = username_and_id_dict[default_username]["UserID"]
    default_user_team = username_and_id_dict[default_username]["Team"]
    print("[x] Fetching the \"no comms\" status for {}".format(node_id))
    no_comms, production_average = get_well_state_details(node_id)
    print("[x] Fetching the last state change object for {}".format(node_id))
    last_state_change_object = None
    if "state change" == prediction_type:
        last_state_change_object = get_last_state_change_object(node_id)
    print("[x] Fetching the route details for {}".format(node_id))
    route_object = get_route_for_node(node_id)
    print("[x] Generating the well object for {}".format(node_id))
    return WellObject(
        default_username,
        default_assignee_user_id,
        no_comms,
        last_state_change_object,
        route_object,
        production_average,
        default_user_team,
    )






# Return the user with the least number of tasks
def get_user_to_assign(role, available_users, well_object):
    # workflow_output_table = "tasq-assign-user-tasks-dev-WorkflowOutputTable-TPNPON59UL2Z"
    workflow_output_table = os.environ['WORKFLOW_OUTPUT_TABLE']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(workflow_output_table)

    start_of_day = datetime.now()
    start_of_day_string = start_of_day.strftime("%Y-%m-%dT00:00:00")

    fe       = Key('time').gte(start_of_day_string) # & Key('time').lte(to_time);
    response = table.query(
        IndexName='Role-index',
        KeyConditionExpression=Key('Role').eq(role),
        FilterExpression=fe
    )
    response_items = response["Items"]

    user_dict = {}
    for user in available_users:
        for attr in user["Attributes"]:
            if attr["Name"] == "sub":
                user_dict[attr["Value"]] = {"Details":user, "TotalPreviousAssignments":1}


    for item in response_items:
        if item["UserID"] in user_dict:
            user_dict[item["UserID"]]["TotalPreviousAssignments"] = user_dict[item["UserID"]]["TotalPreviousAssignments"] + 1


    if not user_dict:
        # Simply return default assignee for now
        return({
            "UserEmail":well_object.default_assignee,
            "UserID":well_object.default_assignee_user_id
        })
        # return_dict = {}
        # for attr in available_users[0]["User"]["Attributes"]:
        #     if attr["Name"] == "sub":
        #         return_dict["UserID"] = attr["Value"]
        #     if attr["Name"] == "email":
        #         return_dict["UserEmail"] = attr["Value"]
        # return return_dict


    min_user_assignment = None
    for key, value in user_dict.items():
        if not min_user_assignment:
            min_user_assignment = value
        else:
            if value["TotalPreviousAssignments"] < min_user_assignment["TotalPreviousAssignments"]:
                min_user_assignment = value

    return_dict = {}
    for attr in min_user_assignment["Details"]["Attributes"]:
        if attr["Name"] == "sub":
            return_dict["UserID"] = attr["Value"]
        if attr["Name"] == "email":
            return_dict["UserEmail"] = attr["Value"]
    return return_dict







# Return the user with the least number of tasks
def get_user_to_assign_no_comms(role, available_users):
    # workflow_output_table = "tasq-assign-user-tasks-dev-WorkflowOutputTable-TPNPON59UL2Z"
    workflow_output_table = os.environ['WORKFLOW_OUTPUT_TABLE']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(workflow_output_table)

    start_of_day = datetime.now()
    start_of_day_string = start_of_day.strftime("%Y-%m-%dT00:00:00")

    fe       = Key('time').gte(start_of_day_string) # & Key('time').lte(to_time);
    response = table.query(
        IndexName='Role-index',
        KeyConditionExpression=Key('Role').eq(role),
        FilterExpression=fe
    )
    response_items = response["Items"]

    user_dict = {}
    for user in available_users:
        for attr in user["Attributes"]:
            if attr["Name"] == "sub":
                user_dict[attr["Value"]] = {"Details":user, "TotalPreviousAssignments":1}


    for item in response_items:
        if item["UserID"] in user_dict:
            user_dict[item["UserID"]]["TotalPreviousAssignments"] = user_dict[item["UserID"]]["TotalPreviousAssignments"] + 1

    min_user_assignment = None
    for key, value in user_dict.items():
        if not min_user_assignment:
            min_user_assignment = value
        else:
            if value["TotalPreviousAssignments"] < min_user_assignment["TotalPreviousAssignments"]:
                min_user_assignment = value

    return_dict = {}
    for attr in min_user_assignment["Details"]["Attributes"]:
        if attr["Name"] == "sub":
            return_dict["UserID"] = attr["Value"]
        if attr["Name"] == "email":
            return_dict["UserEmail"] = attr["Value"]
    return return_dict




def get_available_users_in_group(role):
    secrets_client = boto3.client('secretsmanager')
    # user_pool = "dev/enerplus/cognito/pool"
    user_pool = os.environ['USER_POOL']
    should_assign_test_user = os.environ['SHOULD_ASSIGN_TEST_USER']

    secrets_response = secrets_client.get_secret_value(SecretId=user_pool)
    user_pool_config = json.loads(secrets_response['SecretString'])
    user_pool_id = user_pool_config['user_pool_id']
    user_pool_region = user_pool_config['user_pool_region']

    client = boto3.client('cognito-idp', region_name=user_pool_region)
    time.sleep(4)
    response = client.list_users_in_group(
        UserPoolId=user_pool_id,
        GroupName=role
    )
    available_users = []

    check_string_val = "false"
    if should_assign_test_user and should_assign_test_user != "false" and should_assign_test_user != "False":
        check_string_val = "true"
    AcceptingTasqs = True
    for User in response["Users"]:
        contains_test_user_attr = False
        should_add_user = False
        for Attribute in User["Attributes"]:
            if Attribute["Name"] == "custom:accepting_tasqs":
                AcceptingTasqsVal = Attribute["Value"]
                if AcceptingTasqsVal in ["False", "false", False]:
                    should_add_user = False
            if (Attribute["Name"] == "custom:is_test_user"):
                contains_test_user_attr = True
                if (Attribute["Value"] == check_string_val):
                    should_add_user = True
        if not (contains_test_user_attr or should_assign_test_user):
            should_add_user = True

        if should_add_user and AcceptingTasqs:
            available_users.append(User)
    return available_users






def assignment_decision_tree(well_object):

    available_engineering_users = get_available_users_in_group('Engineers')
    available_automation_users = get_available_users_in_group('Automation')
    if well_object.no_comms and len(available_automation_users) > 0:
        user_to_assign_task_dict = get_user_to_assign("Automation", available_automation_users, well_object)
        return({
            "Role": "Automation",
            "UserID": user_to_assign_task_dict["UserID"],
            "UserEmail": user_to_assign_task_dict["UserEmail"]
        })
    else:
        user_to_assign_task_dict = get_user_to_assign("Engineers", available_engineering_users, well_object)
        return({
            "Role": "Engineers",
            "UserID": user_to_assign_task_dict["UserID"],
            "UserEmail": user_to_assign_task_dict["UserEmail"]
        })





def get_single_user_details(username):
    secrets_client = boto3.client('secretsmanager')
    user_pool = os.environ['USER_POOL']
    # user_pool = "dev/enerplus/cognito/pool"
    secrets_response = secrets_client.get_secret_value(SecretId=user_pool)
    user_pool_config = json.loads(secrets_response['SecretString'])
    user_pool_id = user_pool_config['user_pool_id']
    user_pool_region = user_pool_config['user_pool_region']

    client = boto3.client('cognito-idp', region_name=user_pool_region)
    response = client.admin_get_user(
        UserPoolId=user_pool_id,
        Username=username
    )
    sub = None


    for att in response["UserAttributes"]:
        if att["Name"] == "sub":
            sub = att["Value"]


    response = client.admin_list_groups_for_user(
        Username=username,
        UserPoolId=user_pool_id
    )

    Role = None
    groups = response["Groups"]
    for group in groups:
        if "Automation" in group["GroupName"]:
            Role = "Automation"
        if "Engineers" in group["GroupName"]:
            Role = "Engineers"
        if "FieldOperator" in group["GroupName"]:
            Role = "FieldOperator"
        if "Intervention" in group["GroupName"]:
            Role = "Intervention"
        if "Maintenance" in group["GroupName"]:
            Role = "Maintenance"
        if "Operators" in group["GroupName"]:
            Role = "Operators"
        if "Optimizer" in group["GroupName"]:
            Role = "Optimizer"
        if "SafetyCritical" in group["GroupName"]:
            Role = "SafetyCritical"


    return({
        "UserEmail":username,
        "UserID": sub,
        "Role": Role
    })







def retrieve_default_user_assignment_dict():
    # metadata_table_string = "tasq-meta-datastore-dev-MetaDataTable-OXCE4Y3LQ2MZ"
    metadata_table_string = os.environ['DYNAMODB_METADATA']
    dynamodb = boto3.resource('dynamodb')
    metadata_table = dynamodb.Table(metadata_table_string)

    metadata_response = metadata_table.query(
        IndexName='EnabledString-index',
        KeyConditionExpression=Key('EnabledString').eq("True")
    )

    default_user_assignment_dict = {}
    for metadata_response in metadata_response["Items"]:
        default_user_assignment_dict[metadata_response["NodeID"]] = metadata_response["Username"]
    return default_user_assignment_dict










# ******************************************************************************
# ******************************************************************************
# *************************** TASQ_PREDICTION **********************************
# ******************************************************************************
# ******************************************************************************

def check_state_change_condition_met(well, description, from_time, to_time):
    # Grab all state changes in last hour
    predictions_list_table = os.environ['PREDICTIONS_LIST_TABLE']
    # predictions_list_table = "tasq-detect-state-change-dev-PredictionTable-OWFZZ8X5FOG8"
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(predictions_list_table)


    # start_of_day = datetime.now()
    # hour_ago = start_of_day - timedelta(hours=1)
    # hour_ago_string = hour_ago.strftime("%Y-%m-%dT%H:00:00")
    fe       = Key('time').gte(from_time) & Key('time').lte(to_time) & Key('PredictionType').eq("state change") & Key("Assignee").not_exists()
    response = table.scan(
        IndexName='TimeIndex',
        FilterExpression= fe
    )
    items = response["Items"]
    items = list(reversed(sorted(items, key=lambda x: datetime.strptime(x['StateChangeDate'], '%Y-%m-%dT%H:%M:%S'))))

    if not items:
        return None

    for item in items:
        if "States" in item:
            for state in item["States"]:
                if description == state["Description"]:
                    return item

    return None



def check_failure_condition_met(well, from_time, to_time):
    # Grab all state changes in last hour
    predictions_list_table = os.environ['PREDICTIONS_LIST_TABLE']
    # predictions_list_table = "tasq-detect-state-change-dev-PredictionTable-OWFZZ8X5FOG8"
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(predictions_list_table)


    # start_of_day = datetime.now()
    # hour_ago = start_of_day - timedelta(hours=1)
    # hour_ago_string = hour_ago.strftime("%Y-%m-%dT%H:00:00")
    fe       = Key('time').gte(from_time) & Key('time').lte(to_time) & Key('PredictionType').eq("failure prediction") & Key("Assignee").not_exists()
    response = table.scan(
        IndexName='TimeIndex',
        FilterExpression= fe
    )
    items = response["Items"]
    items = list(reversed(sorted(items, key=lambda x: datetime.strptime(x['AssignmentTime'], '%Y-%m-%dT%H:%M:%S'))))

    if not items:
        return None


    return items[0]


def check_prediction_condition_met(well, from_time, to_time):
    # Grab all state changes in last hour
    predictions_list_table = os.environ['PREDICTIONS_LIST_TABLE']
    # predictions_list_table = "tasq-detect-state-change-dev-PredictionTable-OWFZZ8X5FOG8"
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(predictions_list_table)

    # Check for if any datapoints exceed the value within the window

    # start_of_day = datetime.now()
    # hour_ago = start_of_day - timedelta(hours=1)
    # hour_ago_string = hour_ago.strftime("%Y-%m-%dT%H:00:00")
    fe       = Key('time').gte(from_time) & Key('time').lte(to_time) & Key('PredictionType').eq("failure prediction") & Key("Assignee").not_exists()
    response = table.scan(
        IndexName='TimeIndex',
        FilterExpression= fe
    )
    items = response["Items"]
    items = list(reversed(sorted(items, key=lambda x: datetime.strptime(x['AssignmentTime'], '%Y-%m-%dT%H:%M:%S'))))

    if len(items) == 0:
        return None


    return items[0]



def fit_data_to_window(window):
    local_node_details_dict = deepcopy(__node_details_dict)
    description_array = ["Polished Rod HP", "Current Percent Run", "Pump Fillage", "Last Stroke Min Load", "Fluid Load", "Last Stroke Peak Load"]
    for key, value in __node_details_dict.items():
        window = "2 days"
        duration = float(window.split(" ")[0])
        rate = window.split(" ")[1]

        if "hour" in rate.lower():
            if len(__node_details_dict[key]["WellTestData"]) > 0:
                end_datetime = datetime.strptime(__node_details_dict[key]["WellTestData"].iloc[0]["date"], '%Y-%m-%d')
                start_datetime = end_datetime - timedelta(hours=duration)
                local_node_details_dict[key]["WellTestData"] = __node_details_dict[key]["WellTestData"][(__node_details_dict[key]["WellTestData"]["date"] >= start_datetime.strftime("%Y-%m-%d"))]
            for description in description_array:
                if len(__node_details_dict[key]["SignalsData"][description]["dataset"]) > 0:
                    end_datetime = datetime.strptime(__node_details_dict[key]["SignalsData"][description]["dataset"].iloc[0]["time"], '%Y-%m-%dT%H:%M:%SZ')
                    start_datetime = end_datetime - timedelta(hours=duration)
                    local_node_details_dict[key]["SignalsData"][description]["dataset"] = __node_details_dict[key]["SignalsData"][description]["dataset"][(__node_details_dict[key]["SignalsData"][description]["dataset"]["time"] >= start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"))]

        elif "day" in rate.lower():
            if len(__node_details_dict[key]["WellTestData"]) > 0:
                end_datetime = datetime.strptime(__node_details_dict[key]["WellTestData"].iloc[0]["date"], '%Y-%m-%d')
                start_datetime = end_datetime - timedelta(days=duration)
                local_node_details_dict[key]["WellTestData"] = __node_details_dict[key]["WellTestData"][(__node_details_dict[key]["WellTestData"]["date"] >= start_datetime.strftime("%Y-%m-%d"))]

            for description in description_array:
                if len(__node_details_dict[key]["SignalsData"][description]["dataset"]) > 0:
                    end_datetime = datetime.strptime(__node_details_dict[key]["SignalsData"][description]["dataset"].iloc[0]["time"], '%Y-%m-%dT%H:%M:%SZ')
                    start_datetime = end_datetime - timedelta(days=duration)
                    local_node_details_dict[key]["SignalsData"][description]["dataset"] = __node_details_dict[key]["SignalsData"][description]["dataset"][(__node_details_dict[key]["SignalsData"][description]["dataset"]["time"] >= start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"))]

        elif "week" in rate.lower():
            duration *= 7
            if len(__node_details_dict[key]["WellTestData"]) > 0:
                end_datetime = datetime.strptime(__node_details_dict[key]["WellTestData"].iloc[0]["date"], '%Y-%m-%d')
                start_datetime = end_datetime - timedelta(days=duration)
                local_node_details_dict[key]["WellTestData"] = __node_details_dict[key]["WellTestData"][(__node_details_dict[key]["WellTestData"]["date"] >= start_datetime.strftime("%Y-%m-%d"))]

            for description in description_array:
                if len(__node_details_dict[key]["SignalsData"][description]["dataset"]) > 0:
                    end_datetime = datetime.strptime(__node_details_dict[key]["SignalsData"][description]["dataset"].iloc[0]["time"], '%Y-%m-%dT%H:%M:%SZ')
                    start_datetime = end_datetime - timedelta(days=duration)
                    local_node_details_dict[key]["SignalsData"][description]["dataset"] = __node_details_dict[key]["SignalsData"][description]["dataset"][(__node_details_dict[key]["SignalsData"][description]["dataset"]["time"] >= start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"))]

        elif "month" in rate.lower():
            duration *= 30
            if len(__node_details_dict[key]["WellTestData"]) > 0:
                end_datetime = datetime.strptime(__node_details_dict[key]["WellTestData"].iloc[0]["date"], '%Y-%m-%d')
                start_datetime = end_datetime - timedelta(days=duration)
                local_node_details_dict[key]["WellTestData"] = __node_details_dict[key]["WellTestData"][(__node_details_dict[key]["WellTestData"]["date"] >= start_datetime.strftime("%Y-%m-%d"))]

            for description in description_array:
                if len(__node_details_dict[key]["SignalsData"][description]["dataset"]) > 0:
                    end_datetime = datetime.strptime(__node_details_dict[key]["SignalsData"][description]["dataset"].iloc[0]["time"], '%Y-%m-%dT%H:%M:%SZ')
                    start_datetime = end_datetime - timedelta(days=duration)
                    local_node_details_dict[key]["SignalsData"][description]["dataset"] = __node_details_dict[key]["SignalsData"][description]["dataset"][(__node_details_dict[key]["SignalsData"][description]["dataset"]["time"] >= start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"))]

    return local_node_details_dict



def check_value_against_operator(well, window, description, value, operator):
    # Check the ts_signals_clean_data key in the json file you are importing
    # Loop through values going back to "window"
    # Check if all data for description are greater than, or all data for description are less than the "value"


    # Create a local_node_details_dict with the data ranging withing the "window" (a subset of global __node_details_dict)
    local_node_details_dict = fit_data_to_window(window)
    
    well_test_df = local_node_details_dict[well]["WellTestData"]

    value = float(value)
    # Use SignalsData
    if description == "Last Stroke Peak Load" \
    or description == "Fluid Load" \
    or description == "Last Stroke Min Load" \
    or description == "Pump Fillage" \
    or description == "Percent Run" \
    or description == "Polish Rod HP":
        signals_df = local_node_details_dict[well]["SignalsData"][description]["dataset"]
        if operator == "GREATER_THAN":
            for index, row in signals_df.iterrows():
                if row['Value'] > value:
                    return True
            return False
        elif operator == "GREATER_THAN_EQUAL_TO":
            for index, row in signals_df.iterrows():
                if row['Value'] >= value:
                    return True
            return False
        elif operator == "LESS_THAN":
            for index, row in signals_df.iterrows():
                if row['Value'] < value:
                    return True
            return False
        elif operator == "LESS_THAN_EQUAL_TO":
            for index, row in signals_df.iterrows():
                if row['Value'] <= value:
                    return True
            return False

    # Use WellTestData
    else:
        column_description = None
        if "water" in description.lower():
            column_description = "water_rate"
        if "oil" in description.lower():
            column_description = "oil_rate"
        if "gas" in description.lower():
            column_description = "gas_rate"
        print("PRINT WELL TEST DATA IF FAILS: ")
        print(well_test_df)
        if operator == "GREATER_THAN":
            for index, row in well_test_df.iterrows():
                if row[column_description] > value:
                    return True
            return False
        elif operator == "GREATER_THAN_EQUAL_TO":
            for index, row in well_test_df.iterrows():
                if row[column_description] >= value:
                    return True
            return False
        elif operator == "LESS_THAN":
            for index, row in well_test_df.iterrows():
                if row[column_description] < value:
                    return True
            return False
        elif operator == "LESS_THAN_EQUAL_TO":
            for index, row in well_test_df.iterrows():
                if row[column_description] <= value:
                    return True
            return False
    return False



def check_value_against_operator_mean(well, window, description, value, operator):
    # Check the ts_signals_clean_data key in the json file you are importing
    # Loop through values going back to "window"
    # Check if all data for description are greater than, or all data for description are less than the "value"


    # Create a local_node_details_dict with the data ranging withing the "window" (a subset of global __node_details_dict)
    local_node_details_dict = fit_data_to_window(window)

    
    well_test_df = local_node_details_dict[well]["WellTestData"]


    # Use SignalsData
    if description == "Last Stroke Peak Load" \
    or description == "Fluid Load" \
    or description == "Last Stroke Min Load" \
    or description == "Pump Fillage" \
    or description == "Percent Run" \
    or description == "Polish Rod HP":
        signals_df = local_node_details_dict[well]["SignalsData"][description]["dataset"]
        mean = df["Value"].mean()
        if operator == "GREATER_THAN":
            if mean > value:
                return True
            return False
        elif operator == "GREATER_THAN_EQUAL_TO":
            if mean >= value:
                return True
            return False
        elif operator == "LESS_THAN":
            if mean < value:
                return True
            return False
        elif operator == "LESS_THAN_EQUAL_TO":
            if mean <= value:
                return True
            return False

    # Use WellTestData
    else:
        column_description = None
        if "water" in description.lower():
            column_description = "water_rate"
        if "oil" in description.lower():
            column_description = "oil_rate"
        if "gas" in description.lower():
            column_description = "gas_rate"

        mean = well_test_df[column_description].mean()
        if operator == "GREATER_THAN":
            if mean > value:
                return True
            return False
        elif operator == "GREATER_THAN_EQUAL_TO":
            if mean >= value:
                return True
            return False
        elif operator == "LESS_THAN":
            if mean < value:
                return True
            return False
        elif operator == "LESS_THAN_EQUAL_TO":
            if mean <= value:
                return True
            return False
    return False






def check_value_against_operator_std_dev(well, window, description, value, operator):
    # Check the ts_signals_clean_data key in the json file you are importing
    # Loop through values going back to "window"
    # Check if all data for description are greater than, or all data for description are less than the "value"


    # Create a local_node_details_dict with the data ranging withing the "window" (a subset of global __node_details_dict)
    local_node_details_dict = fit_data_to_window(window)

    
    well_test_df = local_node_details_dict[well]["WellTestData"]


    # Use SignalsData
    if description == "Last Stroke Peak Load" \
    or description == "Fluid Load" \
    or description == "Last Stroke Min Load" \
    or description == "Pump Fillage" \
    or description == "Percent Run" \
    or description == "Polish Rod HP":
        signals_df = local_node_details_dict[well]["SignalsData"][description]["dataset"]
        std_dev = df["Value"].std()
        if operator == "GREATER_THAN":
            if std_dev > value:
                return True
            return False
        elif operator == "GREATER_THAN_EQUAL_TO":
            if std_dev >= value:
                return True
            return False
        elif operator == "LESS_THAN":
            if std_dev < value:
                return True
            return False
        elif operator == "LESS_THAN_EQUAL_TO":
            if std_dev <= value:
                return True
            return False

    # Use WellTestData
    else:
        column_description = None
        if "water" in description.lower():
            column_description = "water_rate"
        if "oil" in description.lower():
            column_description = "oil_rate"
        if "gas" in description.lower():
            column_description = "gas_rate"

        std_dev = well_test_df[column_description].std()
        if operator == "GREATER_THAN":
            if std_dev >= value:
                return True
            return False
        elif operator == "GREATER_THAN_EQUAL_TO":
            if std_dev >= value:
                return True
            return False
        elif operator == "LESS_THAN":
            if row[column_description] < value:
                return True
            return False
        elif operator == "LESS_THAN_EQUAL_TO":
            if std_dev <= value:
                return True
            return False
    return False






def check_value_against_operator_avg_percent_change(well, window, description, value, operator):
    # Check the ts_signals_clean_data key in the json file you are importing
    # Loop through values going back to "window"
    # Check if all data for description are greater than, or all data for description are less than the "value"


    # Create a local_node_details_dict with the data ranging withing the "window" (a subset of global __node_details_dict)
    local_node_details_dict = fit_data_to_window(window)

    
    well_test_df = local_node_details_dict[well]["WellTestData"]


    # Use SignalsData
    if description == "Last Stroke Peak Load" \
    or description == "Fluid Load" \
    or description == "Last Stroke Min Load" \
    or description == "Pump Fillage" \
    or description == "Percent Run" \
    or description == "Polish Rod HP":
        signals_df = local_node_details_dict[well]["SignalsData"][description]["dataset"]
        signals_df['PercentChange'] = signals_df["Value"].pct_change()
        avg_percent_change = signals_df["PercentChange"].mean()
        if operator == "GREATER_THAN":
            if avg_percent_change > value:
                return True
            return False
        elif operator == "GREATER_THAN_EQUAL_TO":
            if avg_percent_change >= value:
                return True
            return False
        elif operator == "LESS_THAN":
            if avg_percent_change < value:
                return True
            return False
        elif operator == "LESS_THAN_EQUAL_TO":
            if avg_percent_change <= value:
                return True
            return False

    # Use WellTestData
    else:
        column_description = None
        if "water" in description.lower():
            column_description = "water_rate"
        if "oil" in description.lower():
            column_description = "oil_rate"
        if "gas" in description.lower():
            column_description = "gas_rate"

        well_test_df['PercentChange'] = well_test_df[column_description].pct_change()
        avg_percent_change = well_test_df["PercentChange"].mean()
        if operator == "GREATER_THAN":
            if avg_percent_change > value:
                return True
            return False
        elif operator == "GREATER_THAN_EQUAL_TO":
            if avg_percent_change >= value:
                return True
            return False
        elif operator == "LESS_THAN":
            if avg_percent_change < value:
                return True
            return False
        elif operator == "LESS_THAN_EQUAL_TO":
            if avg_percent_change <= value:
                return True
            return False
    return False



# ################ EVENT DATA EXAMPLE ##################
# {'Bobbin 149-93-04D-03H TF': {'EventData':                     time                                              Value
# 20  2020-06-17T17:45:00Z  {'Value': [{'EventID': 'a44f9bc7-6cff-4e7e-ac1...
# 19  2020-06-17T09:45:00Z  {'Value': [{'EventID': '8718f04f-f7ee-4e71-88a...
# 18  2020-06-16T09:45:00Z  {'Value': [{'EventID': '4366db95-a270-4f58-acd...
# 17  2020-06-16T01:45:00Z  {'Value': [{'EventID': 'ffbf1705-662c-445f-ad5...
# 16  2020-06-15T17:45:00Z  {'Value': [{'EventID': '06ab3274-ff92-4854-b77...
# 15  2020-06-15T09:45:00Z  {'Value': [{'EventID': 'b3dbd7fc-c048-469c-b79...
# 14  2020-06-15T01:45:00Z  {'Value': [{'EventID': 'bff684a5-954b-4c1f-a3b...
# 13  2020-06-14T17:45:00Z  {'Value': [{'EventID': '2655425c-1312-4213-97e...
# 12  2020-06-10T09:45:00Z  {'Value': [{'EventID': '7fcd6cab-dc3c-40fe-b44...
# 11  2020-06-10T01:45:00Z  {'Value': [{'EventID': '2f669c63-6b77-4e34-812...
# 10  2020-06-09T17:45:00Z  {'Value': [{'EventID': 'f87a246c-a7d1-44bb-b27...
# 9   2020-05-25T18:30:00Z  [{'EventID': '1406512', 'Note': 'Belt Slippage...
# 8   2020-05-19T09:40:00Z  {'Value': [{'EventID': '2c27c1be-8e2d-49b2-96d...
# 7   2020-05-18T17:35:00Z  {'Value': [{'EventID': '175eda10-ae0e-45e6-8ea...
# 6   2020-05-18T12:10:00Z  [{'EventID': '1403268', 'Note': 'PeakLoad=3584...
# 5   2020-05-16T09:35:00Z  {'Value': [{'EventID': '69456766-b368-4fcf-9c2...
# 4   2020-05-15T17:35:00Z  {'Value': [{'EventID': '5d7a962c-c00e-4054-8e2...
# 3   2020-05-14T09:35:00Z  {'Value': [{'EventID': 'afaef078-a246-41d1-84a...
# 2   2020-05-13T09:35:00Z  {'Value': [{'EventID': '76983790-74fc-4c5a-b62...
# 1   2020-05-09T17:35:00Z  {'Value': [{'EventID': 'acb08cfd-6911-4d83-bdb...
# 0   2020-05-09T01:35:00Z  {'Value': [{'EventID': '830b61ba-c6fa-4f60-8d9...}}


def check_events_change_data_change(well, window, description, value, operator):
    # Check the ts_signals_clean_data key in the json file you are importing
    # Loop through values going back to "window"
    # Check if all data for description are greater than, or all data for description are less than the "value"


    # Create a local_node_details_dict with the data ranging withing the "window" (a subset of global __node_details_dict)
    local_node_details_dict = fit_data_to_window(window)

    event_df = local_node_details_dict[well]["EventData"][description]["dataset"]

    # value = float(value)

    description = description.replace("_"," ")
    if "high" in description.lower():
        for index, row in signals_df.iterrows():
            if "Shutdown, Hi Ld" in row['Value']:
                return row
    else:
        for index, row in signals_df.iterrows():
            if "Shutdown, Lo Ld" in row['Value']:
                return row
    return False





def check_setpoint_change_card_data(well, window, description, value, operator):
    # Check the ts_signals_clean_data key in the json file you are importing
    # Loop through values going back to "window"
    # Check if all data for description are greater than, or all data for description are less than the "value"


    # Create a local_node_details_dict with the data ranging withing the "window" (a subset of global __node_details_dict)
    local_node_details_dict = fit_data_to_window(window)

    card_df = local_node_details_dict[well]["CardData"][description]["dataset"]

    card_df['PercentChange'] = signals_df[description].pct_change()
    max_percent_change_abs = abs(max_percent_change = card_df['PercentChange'].max())
    min_percent_change_abs = abs(min_percent_change = card_df['PercentChange'].min())
    max_change = max(max_percent_change_abs, min_percent_change_abs)
    max_row = None
    if max_percent_change_abs >= min_percent_change_abs:
        max_row = card_df[card_df['PercentChange']==card_df['PercentChange'].max()]
    else:
        max_row = card_df[card_df['PercentChange']==card_df['PercentChange'].min()]
    if operator == "GREATER_THAN":
        if max_change > value:
            return max_row
        return False
    elif operator == "GREATER_THAN_EQUAL_TO":
        if max_change >= value:
            return max_row
        return False
    elif operator == "LESS_THAN":
        if max_change < value:
            return max_row
        return False
    elif operator == "LESS_THAN_EQUAL_TO":
        if max_change <= value:
            return max_row
        return False




def check_setpoint_change_signals(well, window, description, value, operator):
    # Check the ts_signals_clean_data key in the json file you are importing
    # Loop through values going back to "window"
    # Check if all data for description are greater than, or all data for description are less than the "value"


    # Create a local_node_details_dict with the data ranging withing the "window" (a subset of global __node_details_dict)
    local_node_details_dict = fit_data_to_window(window)

    signals_df = local_node_details_dict[well]["SignalsData"][description]["dataset"]
    well_test_df = local_node_details_dict[well]["WellTestData"]

    signals_df['PercentChange'] = signals_df["Value"].pct_change()
    max_percent_change_abs = abs(max_percent_change = df['PercentChange'].max())
    min_percent_change_abs = abs(min_percent_change = df['PercentChange'].min())
    max_change = max(max_percent_change_abs, min_percent_change_abs)
    max_row = None
    if max_percent_change_abs >= min_percent_change_abs:
        max_row = signals_df[signals_df['PercentChange']==signals_df['PercentChange'].max()]
    else:
        max_row = signals_df[signals_df['PercentChange']==signals_df['PercentChange'].min()]
    if operator == "GREATER_THAN":
        if max_change > value:
            return max_row
        return False
    elif operator == "GREATER_THAN_EQUAL_TO":
        if max_change >= value:
            return max_row
        return False
    elif operator == "LESS_THAN":
        if max_change < value:
            return max_row
        return False
    elif operator == "LESS_THAN_EQUAL_TO":
        if max_change <= value:
            return max_row
        return False





def check_condition_groups_req_met(node_details_dict, well_array_input, conditions):
    global __node_details_dict
    __node_details_dict = node_details_dict
    well_result_dict = {}

    # Calculate hours ago for predictions, if a prediction occurred in the last 2 hours
    current_date_time = datetime.now()
    hour_ago = current_date_time - timedelta(hours=2)

    for well in well_array_input:
        well_result_dict[well] = {}
    for index, condition in enumerate(conditions):
        if condition["type"] == "condition":
            condition_definition = condition["condition_group_definition"]
            data_feed = condition_definition["data_feed"]
            source = condition_definition["source"]
            conditional_operator = condition_definition["conditional_operator"]
            value = condition_definition["value"]
            window = condition_definition["window"]
            operational_modifier = condition_definition["operational_modifier"] if "operational_modifier" in condition_definition else None
            if operational_modifier == "" or operational_modifier.lower() == "value":
                operational_modifier = None
            reoccurring_condition = condition_definition["reoccurring_condition"] if "reoccurring_condition" in condition_definition else None

            if source == "PEAK_LOAD":
                source = "Last Stroke Peak Load"
            if source == "FLUID_LOAD":
                source = "Fluid Load"
            if source == "MIN_LOAD":
                source = "Last Stroke Min Load"
            if source == "PUMP_FILLAGE":
                source = "Pump Fillage"
            if source == "PERCENT_RUN":
                source = "Percent Run"
            if source == "POLISH_ROD_HP":
                source = "Polish Rod HP"


            if data_feed in ["CONFIGURATION", "EOT"]:
                print()

            elif data_feed == "EVENT":
                for well, dict_value in well_result_dict.items():
                    well_result_dict[well][index] = {}
                    result = check_events_change_data_change(well, window, description, value, operator)
                    well_result_dict[well][index] = {}
                    if result:
                        well_result_dict[well][index]["condition"] = condition
                    well_result_dict[well][index]["result"] = result
            elif data_feed == "PRODUCTION":
                if operational_modifier:
                    if operational_modifier == "Mean": # Check if mean of source is greater than or less than "value" for window
                        for well, dict_value in well_result_dict.items():
                            well_result_dict[well][index] = {}
                            print("1 SENDING VALUE: ")
                            print(value)
                            result = check_value_against_operator_mean(well, window, source, value, conditional_operator)
                            if result:
                                well_result_dict[well][index]["condition"] = condition
                            well_result_dict[well][index]["result"] = result
                    elif operational_modifier == "STD Dev":
                        for well, dict_value in well_result_dict.items():
                            well_result_dict[well][index] = {}
                            print("2 SENDING VALUE: ")
                            print(value)
                            result = check_value_against_operator_std_dev(well, window, source, value, conditional_operator)
                            if result:
                                well_result_dict[well][index]["condition"] = condition
                            well_result_dict[well][index]["result"] = result
                    elif operational_modifier == "ValueRateOfChange":
                        for well, dict_value in well_result_dict.items():
                            well_result_dict[well][index] = {}
                            print("3 SENDING VALUE: ")
                            print(value)
                            result = check_value_against_operator_avg_percent_change(well, window, source, value, operator)
                            if result:
                                well_result_dict[well][index]["condition"] = condition
                            well_result_dict[well][index]["result"] = result
                else:
                    for well, dict_value in well_result_dict.items():
                        well_result_dict[well][index] = {}
                        print("4 SENDING VALUE: ")
                        print(value)
                        result = check_value_against_operator(well, window, source, value, conditional_operator)
                        well_result_dict[well][index] = {}
                        if result:
                            well_result_dict[well][index]["condition"] = condition
                        well_result_dict[well][index]["result"] = result
            elif data_feed == "SETPOINT":
                source = source.replace("_"," ")
                if source.lower() == "fillage":
                    # Check if a setpoint change occurs (change in value), then check the prior value, and determine if percent change is greater than the next value
                    # From Signals

                    for well, dict_value in well_result_dict.items():
                        well_result_dict[well][index] = {}
                        result = check_setpoint_change_signals(well, window, source, value, conditional_operator)
                        well_result_dict[well][index] = {}
                        if result:
                            well_result_dict[well][index]["condition"] = condition
                        well_result_dict[well][index]["result"] = result
                elif (
                    source.lower() != "fillage"
                    and source.lower() == "spm"
                    or source.lower() != "fillage"
                    and source.lower() != "spm"
                    and source.lower() == "stroke length"
                ):
                    # Check if a setpoint change occurs (change in value), then check the prior value, and determine if percent change is greater than the next value
                    for well, dict_value in well_result_dict.items():
                        well_result_dict[well][index] = {}
                        result = check_setpoint_change_card_data(well, window, source, value, conditional_operator)
                        well_result_dict[well][index] = {}
                        if result:
                            well_result_dict[well][index]["condition"] = condition
                        well_result_dict[well][index]["result"] = result
                elif (
                    source.lower() != "fillage"
                    and source.lower() != "spm"
                    and source.lower() != "stroke length"
                    and source.lower() == "offtime"
                ):
                    for well, dict_value in well_result_dict.items():
                        well_result_dict[well][index] = {}
                        result = check_setpoint_change_signals(well, window, "Calculated Run Status", value, conditional_operator)
                        well_result_dict[well][index] = {}
                        if result:
                            well_result_dict[well][index]["condition"] = condition
                        well_result_dict[well][index]["result"] = result
                                    # Check if a setpoint change occurs (change in value), then check the prior value, and determine if percent change is greater than the next value

                elif (
                    source.lower() != "fillage"
                    and source.lower() != "spm"
                    and source.lower() != "stroke length"
                    and source.lower() != "offtime"
                    and source.lower()
                    in ["po strokes", "consecutive pumpoff strokes allowed"]
                ):
                    for well, dict_value in well_result_dict.items():
                        well_result_dict[well][index] = {}
                        result = check_setpoint_change_signals(well, window, "Consecutive Pumpoff Strokes Allowed", value, conditional_operator)
                        well_result_dict[well][index] = {}
                        if result:
                            well_result_dict[well][index]["condition"] = condition
                        well_result_dict[well][index]["result"] = result
                                    # Check if a setpoint change occurs (change in value), then check the prior value, and determine if percent change is greater than the next value


            elif data_feed == "SIGNAL":
                print("[x] Checking if wells matche condition for Signal {}".format(source))
                if operational_modifier:
                    if operational_modifier == "Mean": # Check if mean of source is greater than or less than "value" for window
                        for well, dict_value in well_result_dict.items():
                            well_result_dict[well][index] = {}
                            print("5 SENDING VALUE: ")
                            print(value)
                            result = check_value_against_operator_mean(well, window, source, value, conditional_operator)
                            if result:
                                well_result_dict[well][index]["condition"] = condition
                            well_result_dict[well][index]["result"] = result
                    elif operational_modifier == "STD Dev":
                        for well, dict_value in well_result_dict.items():
                            well_result_dict[well][index] = {}
                            print("6 SENDING VALUE: ")
                            print(value)
                            result = check_value_against_operator_std_dev(well, window, source, value, conditional_operator)
                            if result:
                                well_result_dict[well][index]["condition"] = condition
                            well_result_dict[well][index]["result"] = result
                    elif operational_modifier == "ValueRateOfChange":
                        for well, dict_value in well_result_dict.items():
                            well_result_dict[well][index] = {}
                            result = check_value_against_operator_avg_percent_change(well, window, source, value, operator)
                            if result:
                                well_result_dict[well][index]["condition"] = condition
                            well_result_dict[well][index]["result"] = result
                else:
                    for well, dict_value in well_result_dict.items():
                        print("WELL RESULT DICT: ")
                        print(well_result_dict)
                        print("WELL: ")
                        print(well)
                        well_result_dict[well][index] = {}
                        result = check_value_against_operator(well, window, source, value, conditional_operator)
                        well_result_dict[well][index] = {}
                        if result:
                            well_result_dict[well][index]["condition"] = condition
                        well_result_dict[well][index]["result"] = result
            elif data_feed == "TASQ_PREDICTION":
                for well, dict_value in well_result_dict.items():
                    if value == "STATE_CHANGE":
                        result = check_state_change_condition_met(well, source, hour_ago, current_date_time)
                        well_result_dict[well][index] = {}
                        if result:
                            well_result_dict[well][index]["condition"] = condition
                        well_result_dict[well][index]["result"] = result
                    elif value in ["FAILURE", "PREDICTION"]:
                        result = check_failure_condition_met(well, hour_ago, current_date_time)
                        well_result_dict[well][index] = {}
                        if result:
                            well_result_dict[well][index]["condition"] = condition
                        well_result_dict[well][index]["result"] = result
        elif condition["type"] == "condition_operator":
            operator_value = condition["value"]
            for well, dict_value in well_result_dict.items():
                well_result_dict[well][index] = {}
                well_result_dict[well][index]["condition_operator"] = operator_value

    return well_result_dict




def group_conditions(condition_results_dict):
    previous_val = True
    previous_condition_operator = None
    # print(condition_results_dict)
    for key, condition_result in condition_results_dict.items():
        if "condition_operator" in condition_result:
            if condition_result["condition_operator"] == "OR":
                previous_condition_operator = "OR"
            else:
                previous_condition_operator = "AND"
        else:
            if previous_condition_operator:
                if previous_condition_operator == "OR":
                    previous_val = previous_val or condition_result["result"]
                else:
                    previous_val = previous_val and condition_result["result"]
            else:
                previous_val = condition_result["result"]


    return previous_val
