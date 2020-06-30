from celery import Celery
from celery.utils.log import get_task_logger
import boto3
import pandas as pd
import numpy as np
from decimal import Decimal
import mysql.connector
import pytz
import json
import time
import os
import requests
import traceback
import decimal
import uuid
from boto3.dynamodb.conditions import Key, Attr
from scipy.signal import savgol_filter
from datetime import datetime
from datetime import datetime, timedelta
from copy import deepcopy

import helpers.Classes
from helpers.common_helpers import parse_message
from helpers.worker_helpers import get_ingest_done_message
from helpers.worker_helpers import get_default_user_for_node, \
    get_well_object, \
    get_user_to_assign_no_comms, \
    get_last_state_change_object, \
    get_route_for_node, \
    retrieve_default_user_assignment_dict, \
    assignment_decision_tree, get_well_state_details, \
    get_available_users_in_group, get_user_to_assign, \
    get_enabled_wells, check_condition_groups_req_met, group_conditions, get_single_user_details, \
    get_team_for_user, determine_if_is_tasq_prediction_type, populate_node_details_dict, \
    retrieve_single_user_from_role_dict, retrieve_single_user_from_team_dict

from tasq_logging_helper.handler import tasq_standard_logger

app = Celery(
    main='tasks',
    backend='amqp',
    broker='amqp://guest:guest@{}/'.format(os.environ['BROKER_HOST'])
)
app.conf['worker_prefetch_multiplier'] = 4
app.conf['task_acks_on_failure_or_timeout'] = False
app.conf['task_reject_on_worker_lost'] = True
data_done_topic_arn = os.environ['DATA_DONE_TOPIC_ARN']
sns_client = boto3.client('sns')
logger = get_task_logger(__name__)
logger = tasq_standard_logger(logger, os.environ["LOGGER_TOPIC_ARN"], setLevel="INFO")
prediction_table_string = os.environ['PREDICTIONS_LIST_TABLE']
workflow_output_historic_table_string = os.environ['WORKFLOW_HISTORIC_TABLE']
dynamodb_dest = os.environ["DYNAMODB_DEST_TABLE"]
workflow_output_table_string = os.environ['WORKFLOW_OUTPUT_TABLE']
workflow_details_table_string = os.environ['WORKFLOW_DETAILS_TABLE']
metadata_table_string = os.environ['DYNAMODB_METADATA']

# metadatastore = os.environ["DYNAMODB_METADATA"]
successful_execution_msg = "Message processed successfully"
@app.task(acks_late=True, ignore_result=True, bind=True)
def do_work(self, message, feature_name):
    try:

        dynamodb = boto3.resource('dynamodb')

        ### Read Inbound Message
        msg_dict, msg_uuid, status_message = parse_message(message)
        if msg_dict is None:
            logger.error("Invalid message", extra={"input_parameters": message})
            return "Invalid message: {}".format(message)

        ### Get max date from s3 data store

        query_kwarg = msg_dict
        query_kwarg["from_time"] = (pd.to_datetime(query_kwarg["to_time"]) - pd.Timedelta("90d")).strftime("%Y-%m-%dT%H:%M:%S")
        username_and_id_dict = query_kwarg["username_and_id_dict"]


        if query_kwarg["work_type"] == "workflow_decision":
            workflow_details_table = dynamodb.Table(workflow_details_table_string)
            workflow_output_table_read = dynamodb.Table(workflow_output_table_string)
            print("[x] Populating workflows array...")
            workflows_response = workflow_details_table.scan()

            workflows = []
            for workflow in workflows_response["Items"]:
                workflows.append(workflow)

            print("[x] Grabbing a list of enabled wells...")
            enabled_nodes = get_enabled_wells(metadata_table_string)



            node_details_dict = {}

            for index, node in enumerate(enabled_nodes):
                node_details_dict[node] = {}
                


            print("[x] Populating the node details dictionary...")
            node_details_dict = populate_node_details_dict(node_details_dict)

            # Format the event data for easier reading
            for key, value in node_details_dict.items():
                data = []
                print("node_details_dict[key]: ")
                print(node_details_dict[key]["EventData"])
                for row in node_details_dict[key]["EventData"]["dataset"]:
                    data.append([json.loads(row)["time"], {"Value":json.loads(row)["_value"]}])
                formatted_list = pd.DataFrame(data, columns=['time', 'Value'])
                formatted_list.sort_values(by=['time'], inplace=True, ascending=False)
                node_details_dict[key]["EventData"] = formatted_list


            # Format the data for easier reading
            # for key, value in node_details_dict.items():

            #     formatted_list = pd.DataFrame(
            #     {
            #      'time': node_details_dict[key]["CardData"]["dataset"]["time"],
            #      'SPM': node_details_dict[key]["CardData"]["dataset"]["SPM"],
            #      'StrokeLength': node_details_dict[key]["CardData"]["dataset"]["StrokeLength"]
            #     })
            #     # formatted_list = formatted_list.sort_index(inplace=True)
            #     formatted_list.sort_values(by=['time'], inplace=True, ascending=False)
            #     node_details_dict[key]["CardData"] = formatted_list

            # Should look like the following:
            # {'Bobbin 149-93-04D-03H TF': {'CardData':                     time  SPM  StrokeLength
            #     14  2020-06-18T01:45:00Z  3.2         306.0
            #     13  2020-06-17T17:45:00Z  3.0         306.0
            #     12  2020-06-17T09:45:00Z  3.2         306.0
            #     11  2020-06-17T01:45:00Z  3.2         306.0
            #     10  2020-06-16T17:45:00Z  3.2         306.0
            #     9   2020-06-16T09:45:00Z  2.1         306.0
            #     8   2020-06-16T01:45:00Z  3.0         306.0

            # Format the data for easier reading
            for key, value in node_details_dict.items():
                print("PRINTING VALUE: ")
                print(node_details_dict[key]["WellTestData"])
                if not node_details_dict[key]["WellTestData"]:
                    formatted_list = pd.DataFrame(
                    {
                        'date': [],
                        'oil_rate': [],
                        'water_rate': [],
                        'gas_rate': []
                    })
                    formatted_list.sort_values(by=['date'], inplace=True, ascending=False)
                    node_details_dict[key]["WellTestData"] = formatted_list
                else:
                    formatted_list = pd.DataFrame(
                    {
                        'date': node_details_dict[key]["WellTestData"]["date"],
                        'oil_rate': node_details_dict[key]["WellTestData"]["oil_rate"],
                        'water_rate': node_details_dict[key]["WellTestData"]["water_rate"],
                        'gas_rate': node_details_dict[key]["WellTestData"]["gas_rate"]
                    })
                    formatted_list.sort_values(by=['date'], inplace=True, ascending=False)
                    node_details_dict[key]["WellTestData"] = formatted_list


            for workflow in workflows:
                print("[x] Executing workflow {}".format(workflow["WorkflowDetailsID"]))

                settings_dict = workflow["Settings"]

                assign_to_dict = settings_dict["assign_to"]
                well_source = settings_dict["well_source"]
                conditions = settings_dict["conditions"]

                well_array_input = []
                if well_source == "ALL":
                    well_array_input = deepcopy(enabled_nodes)
                else:
                    well_array_input = well_source


                well_result_dict = check_condition_groups_req_met(node_details_dict, well_array_input, conditions)
                # print(well_result_dict)

                # Determine if well meets criteria
                for node_id, condition_results_dict in well_result_dict.items():
                    result = group_conditions(condition_results_dict)

                    if result:
                        # Check for other workflows that currently exist with this same NodeID



                        PredictionID = str(uuid.uuid4())

                        workflow_table_response = workflow_output_table_read.query(
                            IndexName='WorkflowDetailsID-index',
                            KeyConditionExpression=Key('WorkflowDetailsID').eq(workflow["WorkflowDetailsID"])
                        )

                        workflow_table_response_items = workflow_table_response["Items"]
                        workflow_table_response_items = list(reversed(sorted(workflow_table_response_items, key=lambda x: datetime.strptime(x['time'], '%Y-%m-%dT%H:%M:%S'))))
                        if len(workflow_table_response_items) > 0:
                            recent_workflow = workflow_table_response_items[0]
                            # Determine if we already created a tasq for this workflow, if so, and it was within the last 3 days, just skip it
                            three_days_after_last_assignment = datetime.strptime(recent_workflow['time'], '%Y-%m-%dT%H:%M:%S') + timedelta(days=3)
                            if datetime.now() < three_days_after_last_assignment:
                                print("[x] Workflow already exists for {} and {}, skipping...".format(workflow["WorkflowDetailsID"], node_id))
                                continue

                            PredictionID = recent_workflow["PredictionID"]



                        assignee_dict = {}
                        if assign_to_dict["assignment_type"] == "INDIVIDUAL":
                            assignee_dict = get_single_user_details(assign_to_dict["individual"])
                            # Need to get role and user id
                        if assign_to_dict["assignment_type"] == "ROLE":
                            assignee_dict = retrieve_single_user_from_role_dict(assign_to_dict["role"])
                            # get available user for role
                        if assign_to_dict["assignment_type"] == "TEAM":
                            assignee_dict = retrieve_single_user_from_team_dict(assign_to_dict["team"])
                            # get available user in team, along with role and user id
                        if assign_to_dict["assignment_type"] == "ALL":
                            assignee_dict = assignment_decision_tree(well_object)

                        default_user_assignment_dict = retrieve_default_user_assignment_dict()
                        well_object = get_well_object(node_id, -1, default_user_assignment_dict, "Workflow", username_and_id_dict)

                        print("USER EMAIL: ")
                        print(assignee_dict)
                        well_object.team = get_team_for_user(assignee_dict["UserEmail"])


                        unassigned_prediction = determine_if_is_tasq_prediction_type(condition_results_dict)
                        if unassigned_prediction:
                            unassigned_prediction["Assignee"] = {"initial_assignment": assignee_dict["UserEmail"], "reassignment":{}, "reassignment_history":[]}
                            unassigned_prediction["Username"] = assignee_dict["UserEmail"]
                            unassigned_prediction["UserID"] = assignee_dict["UserID"]
                            unassigned_prediction["ContactListID"] = well_object.route_object.contact_list_id
                            unassigned_prediction["Route"] = well_object.route_object.route_string
                            unassigned_prediction["RouteID"] = well_object.route_object.route_id
                            unassigned_prediction["Team"] = well_object.team


                            if "States" in unassigned_prediction:
                                for y in range(len(unassigned_prediction["States"])):
                                    with decimal.localcontext(boto3.dynamodb.types.DYNAMODB_CONTEXT) as ctx:
                                        ctx.traps[decimal.Inexact] = False
                                        ctx.traps[decimal.Rounded] = False
                                        unassigned_prediction["States"][y]["delta_state"] = ctx.create_decimal_from_float(unassigned_prediction["States"][y]["delta_state"])
                                        unassigned_prediction["States"][y]["post_state"] = ctx.create_decimal_from_float(unassigned_prediction["States"][y]["post_state"])
                                        unassigned_prediction["States"][y]["pre_state"] = ctx.create_decimal_from_float(unassigned_prediction["States"][y]["pre_state"])



                            if "Prediction" in unassigned_prediction:

                                with decimal.localcontext(boto3.dynamodb.types.DYNAMODB_CONTEXT) as ctx:
                                    ctx.traps[decimal.Inexact] = False
                                    ctx.traps[decimal.Rounded] = False
                                    decimal.getcontext().prec = 4
                                    unassigned_prediction["Prediction"]["Score"] = ctx.create_decimal_from_float(unassigned_prediction["Prediction"]["Score"])
                                    unassigned_prediction["Prediction"]["Trheshold"] = ctx.create_decimal_from_float(unassigned_prediction["Prediction"]["Trheshold"])
                                    unassigned_prediction["Prediction"]["Value"] = ctx.create_decimal_from_float(unassigned_prediction["Prediction"]["Value"])
                            predictions_table.put_item(
                                Item=unassigned_prediction
                            )

                            # Insert record into workflow output table
                            workflow_id = str(uuid.uuid4())
                            workflow_record = {}
                            workflow_record["Assignee"] = {"initial_assignment": assignee_dict["UserEmail"], "reassignment":{}, "reassignment_history":[]}
                            workflow_record["Username"] = assignee_dict["UserEmail"]
                            workflow_record["UserID"] = assignee_dict["UserID"]
                            workflow_record["Role"] = assignee_dict["Role"]
                            workflow_record["ContactListID"] = well_object.route_object.contact_list_id
                            workflow_record["Route"] = well_object.route_object.route_string
                            workflow_record["RouteID"] = well_object.route_object.route_id
                            workflow_record["NoComms"] = well_object.no_comms
                            workflow_record["ProductionAverage"] = well_object.production_average
                            workflow_record["NodeID"] = unassigned_prediction["NodeID"]
                            workflow_record["PredictionType"] = unassigned_prediction["PredictionType"]
                            workflow_record["PredictionID"] = unassigned_prediction["PredictionID"]
                            workflow_record["WorkflowDetailsID"] = workflow["WorkflowDetailsID"]


                            if "model" in unassigned_prediction:
                                workflow_record["model"] = unassigned_prediction["model"]
                            if "Prediction" in unassigned_prediction:
                                workflow_record["Prediction"] = unassigned_prediction["Prediction"]

                            if "States" in unassigned_prediction:
                                workflow_record["States"] = unassigned_prediction["States"]
                            if "StateChangeDate" in unassigned_prediction:
                                workflow_record["StateChangeDate"] = unassigned_prediction["StateChangeDate"]


                            workflow_record["AssignmentTime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")# current datetime
                            workflow_record["time"] = unassigned_prediction["time"]
                            workflow_record["HistoricWorkflowID"] = workflow_id
                            workflow_record["Team"] = well_object.team

                            if "Prediction" in unassigned_prediction:
                                if "Value" in unassigned_prediction["Prediction"]:
                                    if unassigned_prediction["Prediction"]["Value"] == 1:
                                        workflow_output_table = dynamodb.Table(workflow_output_historic_table_string)
                                        workflow_output_table.put_item(
                                            Item=workflow_record
                                        )

                                else:
                                    workflow_output_table = dynamodb.Table(workflow_output_historic_table_string)
                                    workflow_output_table.put_item(
                                        Item=workflow_record
                                    )
                            else:
                                workflow_output_table = dynamodb.Table(workflow_output_historic_table_string)
                                workflow_output_table.put_item(
                                    Item=workflow_record
                                )
                            continue


                        # Create tasq for node_id
                        workflow_id = str(uuid.uuid4())
                        workflow_record = {}
                        workflow_record["Assignee"] = {"initial_assignment": assignee_dict["UserEmail"], "reassignment":{}, "reassignment_history":[]}
                        workflow_record["Username"] = assignee_dict["UserEmail"]
                        workflow_record["UserID"] = assignee_dict["UserID"]
                        workflow_record["Role"] = assignee_dict["Role"]
                        workflow_record["ContactListID"] = well_object.route_object.contact_list_id
                        workflow_record["Route"] = well_object.route_object.route_string
                        workflow_record["RouteID"] = well_object.route_object.route_id
                        workflow_record["NoComms"] = well_object.no_comms
                        workflow_record["ProductionAverage"] = well_object.production_average
                        workflow_record["NodeID"] = node_id
                        workflow_record["PredictionType"] = "Workflow"
                        workflow_record["PredictionID"] = PredictionID
                        workflow_record["WorkflowDetailsID"] = workflow["WorkflowDetailsID"]
                        workflow_record["WorkflowCondition"] = json.dumps(condition_results_dict)


                        workflow_record["AssignmentTime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")# current datetime
                        workflow_record["time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        workflow_record["HistoricWorkflowID"] = workflow_id
                        if "team" in assign_to_dict:
                            workflow_record["Team"] = assign_to_dict["team"]
                        else:
                            workflow_record["Team"] = well_object.team


                        workflow_output_table = dynamodb.Table(workflow_output_historic_table_string)
                        workflow_output_table.put_item(
                            Item=workflow_record
                        )








        if query_kwarg["work_type"] == "check_no_comms":
            node_id = query_kwarg["node_id"]
            # Add code for one node here

            fe = Key('PredictionType').eq("No Comms")
            ae = Attr('NodeID').eq(node_id)

            workflow_output_table = dynamodb.Table(workflow_output_table_string)
            response = workflow_output_table.scan(
                IndexName="NodeID-index",
                FilterExpression=ae & fe
            )

            previous_record = None
            if len(response["Items"]) > 0:
                previous_record = response["Items"][0]



            default_user_assignment_dict = retrieve_default_user_assignment_dict()



            no_comms, production_average = get_well_state_details(node_id)
            if not no_comms:
                return "[x] Not in no comms status: {}".format(node_id)



            assignee_dict = {}
            available_automation_users = get_available_users_in_group('Automation')
            if len(available_automation_users) > 0:
                user_to_assign_task_dict = get_user_to_assign_no_comms("Automation", available_automation_users)
                assignee_dict = {
                    "Role": "Automation",
                    "UserID": user_to_assign_task_dict["UserID"],
                    "UserEmail": user_to_assign_task_dict["UserEmail"]
                }
            # if well_object.no_comms:
            #     return "Is no comms status, skipping... {}".format(message)

            default_user_team = username_and_id_dict[assignee_dict["UserEmail"]]["Team"]
            route_object = get_route_for_node(node_id)
            # Insert record into workflow output table

            workflow_id = str(uuid.uuid4())
            workflow_record = {}
            workflow_record["Assignee"] = {"initial_assignment": assignee_dict["UserEmail"], "reassignment":{}, "reassignment_history":[]}
            workflow_record["Username"] = assignee_dict["UserEmail"]
            workflow_record["UserID"] = assignee_dict["UserID"]
            workflow_record["Role"] = assignee_dict["Role"]
            workflow_record["ContactListID"] = route_object.contact_list_id
            workflow_record["Route"] = route_object.route_string
            workflow_record["RouteID"] = route_object.route_id
            workflow_record["NoComms"] = True
            workflow_record["ProductionAverage"] = production_average
            workflow_record["NodeID"] = node_id
            workflow_record["PredictionType"] = "No Comms"
            if previous_record:
                workflow_record["PredictionID"] = previous_record["PredictionID"]
            else:
                workflow_record["PredictionID"] = workflow_id


            workflow_record["AssignmentTime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")# current datetime
            workflow_record["time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            workflow_record["HistoricWorkflowID"] = workflow_id


            workflow_record["Team"] = default_user_team

            if previous_record:
                previous_record_completed = False
                response_time = None
                if "completed" in previous_record:
                    if previous_record["completed"]:
                        previous_record_completed = True
                        response_time = datetime.strptime(previous_record["ResponseData"]["ResponseTime"], '%Y-%m-%dT%H:%M:%S')



                if previous_record_completed :
                    #  then check if it was completed.  If it was completed, then only create a new row if it's been at least 3 days
                    current_date_time = datetime.now()
                    delta = current_date_time - response_time
                    if delta.days >= 3:
                        # Create a completely new row now
                        workflow_output_table = dynamodb.Table(workflow_output_historic_table_string)
                        workflow_output_table.put_item(
                            Item=workflow_record
                        )


                else:
                #  then check if has not been completed, update the row with the new details (overwrite everything except user assignment)
                    workflow_record["Assignee"] = previous_record["Assignee"]
                    workflow_record["Username"] = previous_record["Username"]
                    workflow_record["UserID"] = previous_record["UserID"]
                    workflow_record["Role"] = previous_record["Role"]
                    workflow_output_table = dynamodb.Table(workflow_output_historic_table_string)
                    workflow_output_table.put_item(
                        Item=workflow_record
                    )




            else:
                workflow_output_table = dynamodb.Table(workflow_output_historic_table_string)
                workflow_output_table.put_item(
                    Item=workflow_record
                )

            ingest_done_message = get_ingest_done_message(msg_dict)
            response = sns_client.publish(
                TopicArn=data_done_topic_arn,
                Message=ingest_done_message)
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                logger.error('[{}] Posting processing done topic failed with response: {}'.format(
                    msg_uuid, response), extra={"input_parameters": msg_dict})
            else:
                logger.info('[{}] Publishing assignment done message.'.format(
                    msg_uuid), extra={"input_parameters": msg_dict})

            return "{} Message: {}".format(response, message)




        else:

            # Add code for one node here
            unassigned_prediction = json.loads(query_kwarg["unassigned_prediction"])

            table_name = query_kwarg["table_name"]
            predictions_table = dynamodb.Table(table_name)
            default_user_assignment_dict = retrieve_default_user_assignment_dict()


            well_object = get_well_object(unassigned_prediction["NodeID"], unassigned_prediction["PredictionID"], default_user_assignment_dict, unassigned_prediction["PredictionType"], username_and_id_dict)


            assignee_dict = assignment_decision_tree(well_object)
            unassigned_prediction["Assignee"] = {"initial_assignment": assignee_dict["UserEmail"], "reassignment":{}, "reassignment_history":[]}
            unassigned_prediction["Username"] = assignee_dict["UserEmail"]
            unassigned_prediction["UserID"] = assignee_dict["UserID"]
            unassigned_prediction["ContactListID"] = well_object.route_object.contact_list_id
            unassigned_prediction["Route"] = well_object.route_object.route_string
            unassigned_prediction["RouteID"] = well_object.route_object.route_id
            unassigned_prediction["Team"] = well_object.team

            if "States" in unassigned_prediction:
                for y in range(len(unassigned_prediction["States"])):
                    with decimal.localcontext(boto3.dynamodb.types.DYNAMODB_CONTEXT) as ctx:
                        ctx.traps[decimal.Inexact] = False
                        ctx.traps[decimal.Rounded] = False
                        unassigned_prediction["States"][y]["delta_state"] = ctx.create_decimal_from_float(unassigned_prediction["States"][y]["delta_state"])
                        unassigned_prediction["States"][y]["post_state"] = ctx.create_decimal_from_float(unassigned_prediction["States"][y]["post_state"])
                        unassigned_prediction["States"][y]["pre_state"] = ctx.create_decimal_from_float(unassigned_prediction["States"][y]["pre_state"])


            if "Prediction" in unassigned_prediction:

                with decimal.localcontext(boto3.dynamodb.types.DYNAMODB_CONTEXT) as ctx:
                    ctx.traps[decimal.Inexact] = False
                    ctx.traps[decimal.Rounded] = False
                    decimal.getcontext().prec = 4
                    unassigned_prediction["Prediction"]["Score"] = ctx.create_decimal_from_float(unassigned_prediction["Prediction"]["Score"])
                    unassigned_prediction["Prediction"]["Trheshold"] = ctx.create_decimal_from_float(unassigned_prediction["Prediction"]["Trheshold"])
                    unassigned_prediction["Prediction"]["Value"] = ctx.create_decimal_from_float(unassigned_prediction["Prediction"]["Value"])

            # Insert record into workflow output table
            workflow_id = str(uuid.uuid4())
            workflow_record = {}
            workflow_record["Assignee"] = {"initial_assignment": assignee_dict["UserEmail"], "reassignment":{}, "reassignment_history":[]}
            workflow_record["Username"] = assignee_dict["UserEmail"]
            workflow_record["UserID"] = assignee_dict["UserID"]
            workflow_record["Role"] = assignee_dict["Role"]
            workflow_record["ContactListID"] = well_object.route_object.contact_list_id
            workflow_record["Route"] = well_object.route_object.route_string
            workflow_record["RouteID"] = well_object.route_object.route_id
            workflow_record["NoComms"] = well_object.no_comms
            workflow_record["ProductionAverage"] = well_object.production_average
            workflow_record["NodeID"] = unassigned_prediction["NodeID"]
            workflow_record["PredictionType"] = unassigned_prediction["PredictionType"]
            workflow_record["PredictionID"] = unassigned_prediction["PredictionID"]
            if "model" in unassigned_prediction:
                workflow_record["model"] = unassigned_prediction["model"]
            if "Prediction" in unassigned_prediction:
                workflow_record["Prediction"] = unassigned_prediction["Prediction"]

            if "States" in unassigned_prediction:
                workflow_record["States"] = unassigned_prediction["States"]
            if "StateChangeDate" in unassigned_prediction:
                workflow_record["StateChangeDate"] = unassigned_prediction["StateChangeDate"]


            workflow_record["AssignmentTime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")# current datetime
            workflow_record["time"] = unassigned_prediction["time"]
            workflow_record["HistoricWorkflowID"] = workflow_id
            workflow_record["Team"] = well_object.team
            if "Prediction" in unassigned_prediction:
                if "Value" in unassigned_prediction["Prediction"]:
                    if unassigned_prediction["Prediction"]["Value"] == 1:
                        workflow_output_table = dynamodb.Table(workflow_output_historic_table_string)
                        print("[x] Inserting {} type: {}...".format(workflow_record["PredictionType"], workflow_record["PredictionID"]))
                        workflow_output_table.put_item(
                            Item=workflow_record
                        )
                    else:
                        print("[x] Value for {} is not 1 for failure, skipping {}...".format(workflow_record["PredictionType"], workflow_record["PredictionID"]))

                else:
                    print("[x] Inserting {} type: {}...".format(workflow_record["PredictionType"], workflow_record["PredictionID"]))
                    workflow_output_table = dynamodb.Table(workflow_output_historic_table_string)
                    workflow_output_table.put_item(
                        Item=workflow_record
                    )
            else:
                print("[x] Inserting {} type: {}...".format(workflow_record["PredictionType"], workflow_record["PredictionID"]))
                workflow_output_table = dynamodb.Table(workflow_output_historic_table_string)
                workflow_output_table.put_item(
                    Item=workflow_record
                )

            print("[x] Updating unassigned prediction {} type: {}...".format(unassigned_prediction["PredictionType"], unassigned_prediction["PredictionID"]))
            predictions_table.put_item(
                Item=unassigned_prediction
            )

            ingest_done_message = get_ingest_done_message(msg_dict)
            response = sns_client.publish(
                TopicArn=data_done_topic_arn,
                Message=ingest_done_message)
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                logger.error('[{}] Posting processing done topic failed with response: {}'.format(
                    msg_uuid, response), extra={"input_parameters": msg_dict})
            else:
                logger.info('[{}] Publishing assignment done message.'.format(
                    msg_uuid), extra={"input_parameters": msg_dict})

            return "{} Message: {}".format(response, message)


    except:
        # shutdown worker instance in 1 min so that ECS automatically spins up a replacement
        # to currently crashed worker
        traceback.print_exc()
        app.control.shutdown(destination=[self.request.hostname])
        raise RuntimeError('Error encountered:\n{}'.format(traceback.format_exc(1)))
