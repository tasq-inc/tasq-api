import json
import pandas as pd
import numpy as np
import boto3
import os
import pytz
from datetime import datetime
from datetime import timedelta
from boto3.dynamodb.conditions import Key, Attr
from timeit import default_timer as timer
from time import sleep
# from invitation_email_template import BODY_HTML
import uuid
from botocore.exceptions import ClientError

measurement = 'xspocdatahistory'
events_measurement = 'xspocdatahistory_events_backup'
infity_figure = 9999

SENDER = "Tasq Inc. <tasq@tasqinc.com>"

BODY_HTML = """<html>
<head>
    <meta charset="UTF-8">
    <meta content="width=device-width, initial-scale=1" name="viewport">
    <meta name="x-apple-disable-message-reformatting">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta content="telephone=no" name="format-detection">
    <title></title>

    <link href="https://fonts.googleapis.com/css?family=Open+Sans:400,400i,700,700i" rel="stylesheet">
    <!--<![endif]-->
</head>

<body>
    <div class="es-wrapper-color">
        <!--[if gte mso 9]>
			<v:background xmlns:v="urn:schemas-microsoft-com:vml" fill="t">
				<v:fill type="tile" color="#f6f6f6"></v:fill>
			</v:background>
		<![endif]-->
        <table class="es-wrapper" width="100%" cellspacing="0" cellpadding="0">
            <tbody>
                <tr>
                    <td class="esd-email-paddings" valign="top">
                        <table class="es-content" cellspacing="0" cellpadding="0" align="center">
                            <tbody>
                                <tr>
                                    <td class="esd-stripe esd-checked" style="background-image: -o-linear-gradient(bottom, rgb(9,40,105) 34%, rgb(1,9,82) 72%); background-image: -moz-linear-gradient(bottom, rgb(9,40,105) 34%, rgb(1,9,82) 72%); background-image: -webkit-gradient(linear, left bottom, left top, color-stop(0.34, rgb(9,40,105)), color-stop(0.72, rgb(1,9,82))); background-image: -webkit-linear-gradient(bottom, rgb(9,40,105) 34%, rgb(1,9,82) 72%); background-image: -ms-linear-gradient(bottom, rgb(9,40,105) 34%, rgb(1,9,82) 72%); background-image: linear-gradient(bottom, rgb(9,40,105) 34%, rgb(1,9,82) 72%); background-position: left top; background-repeat: no-repeat; background-size: cover; padding-top: 40px; padding-bottom: 80px; padding-left: 20px; padding-right: 20px;" bgcolor="#3d4c6b" align="center">
                                        <table class="es-content-body" style="background-color: transparent;" width="700" cellspacing="0" cellpadding="0" bgcolor="#f6f6f6" align="center">
                                            <tbody>
                                                <tr>
                                                    <td class="esd-structure es-p10t es-p20r es-p20l" align="left">
                                                        <table width="100%" cellspacing="0" cellpadding="0">
                                                            <tbody>
                                                                <tr>
                                                                    <td class="esd-container-frame" width="600" valign="top" align="center">
                                                                        <table width="100%" cellspacing="0" cellpadding="0">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td class="esd-block-image es-p40t es-p25b" align="center" style="padding-top: 10px; font-size:0"><a href="{invitation_link_url}" target="_blank"><img src="https://images.squarespace-cdn.com/content/5df418172575e24f9fd29c08/1576515161191-TERKI4PEIEFFWOU5MMBF/tasq-icons_192x192.png?content-type=image%2Fpng" style="display: block;" alt="Logo" title="Logo" width="50"></a></td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td align="center" class="esd-block-text es-p25t es-p30b">
                                                                                        <h1 style="color: #ffffff; font-family: 'open sans', 'helvetica neue', helvetica, arial, sans-serif;">Tasq Invitation</h1>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td class="esd-structure es-p40r es-p40l" esd-custom-block-id="6599" align="left">
                                                        <!--[if mso]><table width="560" cellpadding="0"
                            cellspacing="0"><tr><td width="182" valign="top"><![endif]-->
                                                        <table class="es-left" cellspacing="0" cellpadding="0" align="left">
                                                            <tbody>
                                                                <tr>
                                                                    <td class="es-m-p0r esd-container-frame" width="162" align="center">
                                                                        <table width="100%" cellspacing="0" cellpadding="0">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td class="esd-block-spacer es-p10t es-p20r es-p20l" align="center" style="font-size:0">
                                                                                        <table width="100%" height="100%" cellspacing="0" cellpadding="0" border="0">
                                                                                            <tbody>
                                                                                                <tr>
                                                                                                    <td style="border-bottom: 1px solid transparent; background: none; height: 1px; width: 100%; margin: 0px;"></td>
                                                                                                </tr>
                                                                                            </tbody>
                                                                                        </table>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                    <td class="es-hidden" width="20"></td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                        <!--[if mso]></td><td width="20"></td><td width="162" valign="top"><![endif]-->
                                                        <table class="es-right" cellspacing="0" cellpadding="0" align="right">
                                                            <tbody>
                                                                <tr>
                                                                    <td class="esd-container-frame" width="162" align="center">
                                                                        <table width="100%" cellspacing="0" cellpadding="0">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td class="esd-block-spacer es-p10t es-p20r es-p20l" align="center" style="font-size:0">
                                                                                        <table width="100%" height="100%" cellspacing="0" cellpadding="0" border="0">
                                                                                            <tbody>
                                                                                                <tr>
                                                                                                    <td style="border-bottom: 1px solid transparent; background: none; height: 1px; width: 100%; margin: 0px;"></td>
                                                                                                </tr>
                                                                                            </tbody>
                                                                                        </table>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                        <!--[if mso]></td></tr></table><![endif]-->
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td class="esd-structure es-p20t es-p15b es-p20r es-p20l" align="left">
                                                        <table width="100%" cellspacing="0" cellpadding="0">
                                                            <tbody>
                                                                <tr>
                                                                    <td class="esd-container-frame" width="600" valign="top" align="center">
                                                                        <table width="100%" cellspacing="0" cellpadding="0">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td esdev-links-color="#b7bdc9" class="esd-block-text es-p15t es-p20b" align="center">
                                                                                        <p style="color: #b7bdc9; font-size: 15px; padding-bottom: 40px; line-height: 1.7; font-family: 'open sans', 'helvetica neue', helvetica, arial, sans-serif;">{invitation_message}</p>
                                                                                    </td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td class="esd-block-button es-p5t es-p40b" align="center"><span class="es-button-border"><a href="{invitation_button_url}" class="es-button" target="_blank" style="color: #ffffff; font-size: 16px; font-weight: 400; font-family: 'open sans', 'helvetica neue'; background:#74B6C9; text-decoration: none; padding-left: 35px; padding-right: 35px; padding-bottom: 20px; padding-top: 20px; border-radius: 40px;"> View my Tasqs →</a></span></td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td class="esd-structure es-p20t es-p15b es-p20r es-p20l" style="padding-top:70px; padding-bottom:20px;" align="left">
                                                        <table width="100%" cellspacing="0" cellpadding="0">
                                                            <tbody>
                                                                <tr>
                                                                    <td class="esd-container-frame" width="600" height="1" style="background:rgba(255,255,255,0.4); margin-top:50px" valign="top" align="center">
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td class="esd-structure es-p20t es-p15b es-p20r es-p20l" align="left">
                                                        <table width="100%" cellspacing="0" cellpadding="0">
                                                            <tbody>
                                                                <tr>
                                                                    <td class="esd-container-frame" width="600" valign="top" align="center">
                                                                        <table width="100%" cellspacing="0" cellpadding="0">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td esdev-links-color="#b7bdc9" class="esd-block-text es-p15t es-p20b" align="center">
                                                                                        <p style="font-size: 13px; color: rgba(255,255,255,0.9); padding-bottom: 10px; line-height: 1.7; font-family: 'open sans', 'helvetica neue', helvetica, arial, sans-serif;">Application download steps:</p>
                                                                                        <p style="font-size: 12px; color: #b7bdc9; padding-bottom: 0px; line-height: 1.4; font-family: 'open sans', 'helvetica neue', helvetica, arial, sans-serif;">1. On your mobile device, <a style="color: rgba(255,255,255,1);" target="_blank" href="https://enerplus.tasqinc.com" class="view">visit our site</a> </p>
                                                                                        <p style="font-size: 12px; color: #b7bdc9; padding-bottom: 0px; line-height: 1.4; font-family: 'open sans', 'helvetica neue', helvetica, arial, sans-serif;">2. Tap the share icon <img style="height:16.5px;width:13.5px; margin-left:4px; margin-right:4px;" src="https://tasq-email-images.s3.us-east-2.amazonaws.com/share_icon_image.png"> at the bottom center of your browser</p>
                                                                                        <p style="padding-bottom: 0px; margin-bottom: 0px; font-size: 12px; color: #b7bdc9; padding-bottom: 0px; line-height: 1.4; font-family: 'open sans', 'helvetica neue', helvetica, arial, sans-serif;">3. Scroll to select the "Add to Home Screen" <img style="height:14.5px;width:14.5px; margin-bottom: -1px; margin-left:4px; margin-right:4px;" src="https://tasq-email-images.s3.us-east-2.amazonaws.com/add_to_homescreen_icon.png"> option</p>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <table cellpadding="0" cellspacing="0" class="es-footer" align="center">
                            <tbody>
                                <tr>
                                    <td class="esd-stripe" esd-custom-block-id="6564" align="center">
                                        <table style="background:rgba(248,248,248,1); padding-top: 10px; padding-bottom: 20px;" class="es-footer-body" width="740" cellspacing="0" cellpadding="0" align="center">
                                            <tbody>
                                                <tr>
                                                    <td class="esd-structure es-p40t es-p40b es-p20r es-p20l" align="left">
                                                        <table width="100%" cellspacing="0" cellpadding="0">
                                                            <tbody>
                                                                <tr>
                                                                    <td class="esd-container-frame" width="600" valign="top" align="center">
                                                                        <table width="100%" cellspacing="0" cellpadding="0">
                                                                            <tbody>
                                                                                <!-- <tr>
                                                                                    <td class="esd-block-image es-p5b" align="center" style="font-size:0; margin-top: 10px;"><a target="_blank" href="#"><img src="https://tasq-email-images.s3.us-east-2.amazonaws.com/tasq-triangle-outline.jpg" alt="Logo" style="display: block;" title="Logo" width="35"></a></td>
                                                                                </tr> -->
                                                                                <tr>
                                                                                    <td class="esd-block-text es-p15t es-p15b" align="center">
                                                                                        <p style="color: rgba(165,165,165,1); margin-bottom:4px; padding-bottom:0px; font-size:13px; font-family: 'open sans', 'helvetica neue', helvetica, arial, sans-serif;">1616 17th St</p>
                                                                                        <p style="color: rgba(165,165,165,1); margin-top:0px; padding-top:0px; font-size:13px; font-family: 'open sans', 'helvetica neue', helvetica, arial, sans-serif;">Denver, CO 80202</p>
                                                                                    </td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td align="center" class="esd-block-text">
                                                                                        <p style="color: rgba(140,140,140,1); font-size:13px; font-family: 'open sans', 'helvetica neue', helvetica, arial, sans-serif;"><u><a style="color: rgba(140,140,140,1);" target="_blank" href="https://tasqinc.com" class="view">View Online</a></u>&nbsp;&nbsp; • &nbsp;&nbsp;<u><a style="color: rgba(140,140,140,1);" class="unsubscribe" target="_blank" href>Unsubscribe</a></u></p>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</body>

</html>

            """





def get_user_details(event, context):

    if "input" in event:
        event = event["input"]

    username = None
    if "username" in event:
        username = event["username"]

    if not username:
        return({
            "statusCode": 200,
            "headers": {'Content-Type': 'application/json'},
            "success":False,
            "error": True,
            "error_msg":"No username was supplied"
        })

    secrets_client = boto3.client('secretsmanager')
    user_pool = os.environ['USER_POOL']
    secrets_response = secrets_client.get_secret_value(SecretId=user_pool)
    user_pool_config = json.loads(secrets_response['SecretString'])
    user_pool_id = user_pool_config['user_pool_id']
    user_pool_region = user_pool_config['user_pool_region']


    client = boto3.client('cognito-idp', region_name=user_pool_region)
    response = client.admin_get_user(
        UserPoolId=user_pool_id,
        Username=username
    )
    user_email = None
    user_phone_number = None
    sub = None
    is_accepting_tasqs = True

    for att in response["UserAttributes"]:
        if att["Name"] == "sub":
            sub = att["Value"]
        if att["Name"] == "email":
            user_email = att["Value"]
        if att["Name"] == "phone_number":
            user_phone_number = att["Value"]
        if att["Name"] == "accepting_tasqs":
            is_accepting_tasqs = att["Value"]
            if is_accepting_tasqs == "False" or is_accepting_tasqs == "false":
                is_accepting_tasqs = False
        if att["Name"] == "custom:accepting_tasqs":
            is_accepting_tasqs_val = att["Value"]
            if is_accepting_tasqs_val == "False" or is_accepting_tasqs_val == "false" or (not is_accepting_tasqs_val):
                is_accepting_tasqs = False

    response = client.admin_list_groups_for_user(
        Username=username,
        UserPoolId=user_pool_id
    )
    teams = []
    groups = response["Groups"]
    for group in groups:
        if "Team_" in group["GroupName"]:
            teams.append(group["GroupName"])


    return({
        "success":True,
        "error": False,
        "error_msg":"Success!",
        "username":username,
        "user_id":sub,
        "accepting_tasqs":is_accepting_tasqs,
        "teams":teams,
        "user_phone_number":user_phone_number
    })



def post_workflow(event, context):
    if "input" in event:
        event = event["input"]

    workflow_details_table = os.environ['WORKFLOW_DETAILS_TABLE']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(workflow_details_table)

    settings = event["Settings"]
    username = event["Username"]

    time = datetime.now(pytz.timezone('America/Denver')).strftime("%Y-%m-%dT%H:%M:%S")
    workflow_details_id = str(uuid.uuid4())
    item = {
        "WorkflowDetailsID": workflow_details_id,
        "Settings": settings,
        "Username": username,
        "time": time
    }

    table.put_item(Item=item)

    return({
        "Success":True,
        "Error": False,
        "ErrorMsg":"Success!",
        "Settings":settings,
        "WorkflowDetailsID":workflow_details_id
    })



def update_workflow(event, context):
    if "input" in event:
        event = event["input"]

    workflow_details_table = os.environ['WORKFLOW_DETAILS_TABLE']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(workflow_details_table)

    settings = event["Settings"]
    username = event["Username"]
    workflow_details_id = event["WorkflowDetailsID"]


    response = table.query(
        KeyConditionExpression=Key('WorkflowDetailsID').eq(workflow_details_id)
    )

    if len(response["Items"]) == 0:
        return({
            "Success":False,
            "Error": True,
            "ErrorMsg":"No workflow found with id {}".format(workflow_details_id),
            "Settings":"",
            "WorkflowDetailsID":workflow_details_id
        })

    modification_date = datetime.now(pytz.timezone('America/Denver')).strftime("%Y-%m-%dT%H:%M:%S")
    workflow_item = response["Items"][0]
    workflow_item["Settings"] = settings
    workflow_item["DateModified"] = modification_date
    table.put_item(Item=workflow_item)

    return({
        "Success":True,
        "Error": False,
        "ErrorMsg":"Success!",
        "Settings":settings,
        "WorkflowDetailsID":workflow_details_id
    })



def delete_workflow(event, context):
    if "input" in event:
        event = event["input"]

    workflow_details_table = os.environ['WORKFLOW_DETAILS_TABLE']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(workflow_details_table)

    workflow_details_id = event["WorkflowDetailsID"]

    try:
        response = table.delete_item(
            Key={
                'WorkflowDetailsID': workflow_details_id
            }
        )
        return({
            "Success":True,
            "Error": False,
            "ErrorMsg":"Success",
            "WorkflowDetailsID":workflow_details_id
        })
    except ClientError as e:
        return({
            "Success":False,
            "Error": True,
            "ErrorMsg":"Exception occurred seleting id {}.  Does this workflow still exist?".format(workflow_details_id),
            "WorkflowDetailsID":workflow_details_id
        })



def get_workflow(event, context):
    if "input" in event:
        event = event["input"]

    days_ago = 30
    if "AssignmentCountDays" in event:
        days_ago = event["AssignmentCountDays"]

    workflow_details_table = os.environ['WORKFLOW_DETAILS_TABLE']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(workflow_details_table)

    workflow_output_table = os.environ['WORKFLOW_OUTPUT_TABLE']
    output_table = dynamodb.Table(workflow_output_table)


    workflow_details_id = event["WorkflowDetailsID"]


    response = table.query(
        KeyConditionExpression=Key('WorkflowDetailsID').eq(workflow_details_id)
    )

    start_of_day = datetime.now()
    days_ago = start_of_day - timedelta(days=days_ago)
    days_ago_string = days_ago.strftime("%Y-%m-%dT00:00:00")
    fe       = Key('AssignmentTime').gte(days_ago_string) # & Key('time').lte(to_time);
    workflow_response = output_table.scan(
        FilterExpression=Attr("WorkflowDetailsID").eq(workflow_details_id) & fe
    )

    actioned_count = 0
    for item in workflow_response["Items"]:
        if "actioned" in item:
            if item["actioned"]:
                actioned_count = actioned_count + 1

    if len(response["Items"]) == 0:
        return({
            "Success":False,
            "Error": True,
            "ErrorMsg":"No workflow found with id {}".format(workflow_details_id),
            "DateCreated":"",
            "Workflow":"",
            "AssignmentCount":0,
            "ActionedPercentage":0,
            "WorkflowDetailsID":workflow_details_id
        })

    ActionedPercentage = 0
    if len(workflow_response["Items"]) != 0:
        ActionedPercentage = 1 - (float(actioned_count / len(workflow_response["Items"])))
    ActionedPercentage = ActionedPercentage * 100
    if actioned_count == 0:
        ActionedPercentage = 100
    return({
        "Success":True,
        "Error": False,
        "ErrorMsg":"Success",
        "DateCreated": response["Items"][0]["time"],
        "Workflow":response["Items"][0],
        "AssignmentCount":len(workflow_response["Items"]),
        "ActionedPercentage":ActionedPercentage,
        "WorkflowDetailsID":workflow_details_id
    })



def get_all_workflows(event, context):
    if "input" in event:
        event = event["input"]

    workflow_details_table = os.environ['WORKFLOW_DETAILS_TABLE']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(workflow_details_table)


    response = table.scan()




    if len(response["Items"]) == 0:
        return({
            "Success":False,
            "Error": True,
            "ErrorMsg":"No workflows found",
            "Workflows":[],
        })


    workflow_output_table = os.environ['WORKFLOW_OUTPUT_TABLE']
    output_table = dynamodb.Table(workflow_output_table)

    output_response = output_table.query(
        IndexName='PredictionType-index',
        KeyConditionExpression=Key('PredictionType').eq("Workflow")
    )

    output_response_items = output_response["Items"]

    workflow_count_dict = {}
    for item in output_response_items:
        if item["WorkflowDetailsID"] in workflow_count_dict:
            workflow_count_dict[item["WorkflowDetailsID"]] = workflow_count_dict[item["WorkflowDetailsID"]] + 1
        else:
            workflow_count_dict[item["WorkflowDetailsID"]] = 1

    for index, item in enumerate(response["Items"]):
        if item["WorkflowDetailsID"] in workflow_count_dict:
            response["Items"][index]["WorkflowCount"] = workflow_count_dict[item["WorkflowDetailsID"]]
        else:
            response["Items"][index]["WorkflowCount"] = 0

    return({
        "Success":True,
        "Error": False,
        "ErrorMsg":"Success",
        "Workflows":response["Items"]
    })



def update_user_profile(event, context):
    if "input" in event:
        event = event["input"]

    Username = event["Username"]
    Roles = []
    Team = None
    UserEmail = None
    PhoneNumber = None
    AcceptingTasqs = None

    if "Team" in event:
        Team = event["Team"]
    if "Roles" in event:
        Roles = event["Roles"]
    if "UserEmail" in event:
        UserEmail = event["UserEmail"]
    if "PhoneNumber" in event:
        PhoneNumber = event["PhoneNumber"]
    if "AcceptingTasqs" in event:
        AcceptingTasqs = event["AcceptingTasqs"]

    secrets_client = boto3.client('secretsmanager')
    # user_pool = "dev/enerplus/cognito/pool"
    user_pool = os.environ['USER_POOL']
    secrets_response = secrets_client.get_secret_value(SecretId=user_pool)
    user_pool_config = json.loads(secrets_response['SecretString'])
    user_pool_id = user_pool_config['user_pool_id']
    user_pool_region = user_pool_config['user_pool_region']

    client = boto3.client('cognito-idp', region_name=user_pool_region)

    user_attrs = []
    if UserEmail:
        user_attrs.append({"Name": "email","Value": UserEmail})
        user_attrs.append({ "Name": "email_verified", "Value": "true" })

    if PhoneNumber:
        user_attrs.append({"Name": "phone_number","Value": PhoneNumber})
        user_attrs.append({ "Name": "phone_number_verified", "Value": "true" })

    if not (AcceptingTasqs is None):
        if "false" == AcceptingTasqs or "False" == AcceptingTasqs:
            AcceptingTasqs = False
        if "true" == AcceptingTasqs or "True" == AcceptingTasqs:
            AcceptingTasqs = True
        if AcceptingTasqs:
            user_attrs.append({"Name": "custom:accepting_tasqs","Value": "True"})
        else:
            user_attrs.append({"Name": "custom:accepting_tasqs","Value": "False"})

    if "Testing" in Roles:
        user_attrs.append({"Name": "custom:is_test_user","Value": True})

    response = client.admin_update_user_attributes(
        UserPoolId=user_pool_id,
        Username=Username,
        UserAttributes=user_attrs
    )

    if Roles:
        total_roles = ["Automation","Engineers","Testing","Operators","Maintenance","Intervention","SafetyCritical","FieldOperator","Optimizer"]
        for single_role in total_roles:
            try:
                response = client.admin_remove_user_from_group(
                    UserPoolId=user_pool_id,
                    Username=Username,
                    GroupName=single_role
                )
            except:
                continue

        for Role in Roles:
            reply = client.admin_add_user_to_group( UserPoolId=user_pool_id, Username=Username, GroupName=Role )


    if Team:
        response = client.list_groups(
            UserPoolId=user_pool_id
        )
        RemoveTeamsList = []
        TotalTeamsList = []
        for group in response["Groups"]:
            TotalTeamsList.append(group["GroupName"])
            if "Team_" in group["GroupName"]:
                RemoveTeamsList.append(group["GroupName"])


        GroupsToAdd = []
        if not Team in TotalTeamsList:
            GroupsToAdd.append(Team)

        # Add groups to allow a user to be assigned to it
        for GroupToAdd in GroupsToAdd:
            response = client.create_group(
                GroupName=GroupToAdd,
                UserPoolId=user_pool_id,
                Description="Custom Team"
            )

        for RemoveTeam in RemoveTeamsList:
            try:
                response = client.admin_remove_user_from_group(
                    UserPoolId=user_pool_id,
                    Username=Username,
                    GroupName=RemoveTeam
                )
            except:
                continue

        reply = client.admin_add_user_to_group( UserPoolId=user_pool_id, Username=Username, GroupName=Team )





    return({
        "Username": Username,
        "Error": False,
        "Success": True
    })



def sign_up_user(event, context):

    if "input" in event:
        event = event["input"]

    Username = event["Username"]
    UserEmail = event["UserEmail"]
    PhoneNumber = event["PhoneNumber"]
    Roles = event["Roles"]

    secrets_client = boto3.client('secretsmanager')

    user_pool = os.environ['USER_POOL']
    secrets_response = secrets_client.get_secret_value(SecretId=user_pool)
    user_pool_config = json.loads(secrets_response['SecretString'])
    user_pool_id = user_pool_config['user_pool_id']
    user_pool_region = user_pool_config['user_pool_region']

    client = boto3.client('cognito-idp', region_name=user_pool_region)

    user_attrs = [{"Name": "email","Value": UserEmail}, { "Name": "phone_number_verified", "Value": "true" }, { "Name": "email_verified", "Value": "true" }, { "Name": "phone_number", "Value": PhoneNumber }]

    if "Testing" in Roles:
        user_attrs.append({"Name": "custom:is_test_user","Value": True})

    response = client.admin_create_user(
    UserPoolId=user_pool_id,
    Username=Username,
    UserAttributes=user_attrs)

    user_id = None
    for attr in response["User"]["Attributes"]:
        if attr["Name"] == "sub":
            user_id = attr["Value"]
            break

    for Role in Roles:
        reply = client.admin_add_user_to_group( UserPoolId=user_pool_id, Username=UserEmail, GroupName=Role )

    return({
        "UserID": user_id,
        "Username": Username,
        "UserEmail": UserEmail,
        "UserPhoneNumber": PhoneNumber,
        "Roles": Roles
    })



def verify_invitation_id(event, context):
    USER_INVITE_OUTPUT_TABLE = os.environ['USER_INVITE_OUTPUT_TABLE']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(USER_INVITE_OUTPUT_TABLE)

    if "input" in event:
        event = event["input"]

    InvitationID = event["invitation_id"]
    response = table.query(
        KeyConditionExpression=Key('InvitationID').eq(InvitationID)
    )
    if len(response['Items']) > 0:
        return({
            "UserEmail":response['Items'][0]["RecipientEmail"],
            "Verified": True
        })
    else:
        return({
            "UserEmail":"-1",
            "Verified": False
        })



def send_invitation_email(event, context):
    USER_INVITE_OUTPUT_TABLE = os.environ['USER_INVITE_OUTPUT_TABLE']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(USER_INVITE_OUTPUT_TABLE)

    if "input" in event:
        event = event["input"]


    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    RECIPIENT_EMAIL = event["RecipientEmail"]
    USER_EMAIL = event["UserEmail"]
    USER_FIRST_NAME = event["UserFirstName"]
    OPERATOR = "enerplus"
    if "operator" in event:
        OPERATOR = event["Operator"]

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    # CONFIGURATION_SET = "ConfigSet"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"

    # The subject line for the email.
    SUBJECT = "You've Been Invited To Tasq"

    MESSAGE = "{invitee} has invited you to Tasq.  Tap the button below to sign up and get started.".format(invitee=USER_FIRST_NAME)

    INVITATION_UUID = str(uuid.uuid4())
    INVITATION_URL = "{operator}.tasqinc.com/signup?invitation_uuid={invitation_uuid}".format(operator=OPERATOR,invitation_uuid=INVITATION_UUID)

    item = {
        "InvitationID": INVITATION_UUID,
        "RecipientEmail": RECIPIENT_EMAIL,
        "InvitedByEmail": USER_EMAIL
    }
    table.put_item(Item=item)

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = (MESSAGE)

    # BODY_HTML.format(invitation_link_url="{operator}.tasqinc.com".format(operator=OPERATOR), invitation_message=MESSAGE, invitation_button_url=INVITATION_URL)

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT_EMAIL,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML.format(invitation_link_url="{operator}.tasqinc.com".format(operator=OPERATOR), invitation_message=MESSAGE, invitation_button_url=INVITATION_URL),
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        return({
            "Error":True,
            "ErrorMsg":"Failed to send email: " + str(e),
            "MessageID":"-1"
        })
    else:
        return({
            "Error":False,
            "ErrorMsg":"Success!",
            "MessageID":response['MessageId']
        })





def reassign_tasq(event, context):
    historic_table_name = os.environ['WORKFLOW_HISTORIC_TABLE']
    workflow_output_table_name = os.environ['WORKFLOW_OUTPUT_TABLE']
    dynamodb = boto3.resource('dynamodb')
    historic_table = dynamodb.Table(historic_table_name)
    workflow_output_table = dynamodb.Table(workflow_output_table_name)


    if "input" in event:
        event = event["input"]


    PredictionID = event["PredictionID"]
    Username = event["Username"]
    Comment = event["Comment"]

    UserID = None
    if "UserID" in event:
        UserID = event["UserID"]

    response = workflow_output_table.query(
        IndexName='PredictionID-index',
        KeyConditionExpression=Key('PredictionID').eq(PredictionID)
    )


    item = response['Items'][0]

    time = datetime.now(pytz.timezone('America/Denver')).strftime("%Y-%m-%dT%H:%M:%S")
    item["Username"] = Username
    if UserID:
        item["UserID"] = UserID
    reassignment_history_array = item["Assignee"]["reassignment_history"]
    if "reassignment" in item["Assignee"]:
        if not (item["Assignee"]["reassignment"] == {}):
            reassignment_history_array.append(item["Assignee"]["reassignment"])

    item["Assignee"]["reassignment"] = {"new_assignee":Username,"comment":Comment,"time":time} # {"initial_assignment": default_username, "reassignment":{}, "reassignment_history":[]}
    item["Assignee"]["reassignment_history"] = reassignment_history_array
    item["HistoricWorkflowID"] = str(uuid.uuid4())
    historic_table.put_item(Item=item)

    return({
        "PredictionID": PredictionID,
        "Username": Username,
        "Comment": Comment
    })



def get_tasq(event, context):
    dynamo_db_table_name = os.environ['WORKFLOW_OUTPUT_TABLE']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(dynamo_db_table_name)

    if "input" in event:
        event = event["input"]


    PredictionID = event["PredictionID"]

    response = table.query(
        IndexName='PredictionID-index',
        KeyConditionExpression=Key('PredictionID').eq(PredictionID)
    )

    item = response['Items'][0]

    return({
        "PredictionID": PredictionID,
        "Prediction": item
    })


















def calculate_user_dict_reassignment_list(prediction_type, item, user_count_dict, actioned, labeled, unlabeled, completed, locked):
    if "actioned" in item:
        if item["actioned"]:
            actioned = actioned + 1

            if item["Username"] in user_count_dict:
                if item["Role"] in user_count_dict[item["Username"]]:
                    user_count_dict[item["Username"]][item["Role"]]["actioned"] = user_count_dict[item["Username"]][item["Role"]]["actioned"] + 1
                    user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                else:
                    user_count_dict[item["Username"]][item["Role"]] = {"actioned":1,"labeled":0,"unlabeled":0,"completed":0,"locked":0,"reassignments":0,"snoozed":0,"manually_added":0 }
                    if "TotalCount" in user_count_dict[item["Username"]]:
                        user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                    else:
                        user_count_dict[item["Username"]]["TotalCount"] = 1
            else:
                user_count_dict[item["Username"]] = {item["Role"]:{"actioned":1,"labeled":0,"unlabeled":0,"completed":0,"locked":0,"reassignments":0,"snoozed":0,"manually_added":0 }}
                if "TotalCount" in user_count_dict[item["Username"]]:
                    user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                else:
                    user_count_dict[item["Username"]]["TotalCount"] = 1

    if "labeled" in item:
        if item["labeled"]:
            labeled = labeled + 1

            if item["Username"] in user_count_dict:
                if item["Role"] in user_count_dict[item["Username"]]:
                    user_count_dict[item["Username"]][item["Role"]]["labeled"] = user_count_dict[item["Username"]][item["Role"]]["labeled"] + 1
                    user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                else:
                    user_count_dict[item["Username"]][item["Role"]] = {"actioned":0,"labeled":1,"unlabeled":0,"completed":0,"locked":0,"reassignments":0,"snoozed":0,"manually_added":0 }
                    if "TotalCount" in user_count_dict[item["Username"]]:
                        user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                    else:
                        user_count_dict[item["Username"]]["TotalCount"] = 1
            else:
                user_count_dict[item["Username"]] = {item["Role"]:{"actioned":0,"labeled":1,"unlabeled":0,"completed":0,"locked":0,"reassignments":0,"snoozed":0,"manually_added":0 }}
                if "TotalCount" in user_count_dict[item["Username"]]:
                    user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                else:
                    user_count_dict[item["Username"]]["TotalCount"] = 1

        else:

            if item["Username"] in user_count_dict:
                if item["Role"] in user_count_dict[item["Username"]]:
                    user_count_dict[item["Username"]][item["Role"]]["unlabeled"] = user_count_dict[item["Username"]][item["Role"]]["unlabeled"] + 1
                    unlabeled = unlabeled + 1
                    user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                else:
                    user_count_dict[item["Username"]][item["Role"]] = {"actioned":0,"labeled":0,"unlabeled":1,"completed":0,"locked":0,"reassignments":0,"snoozed":0,"manually_added":0 }
                    unlabeled = unlabeled + 1
                    if "TotalCount" in user_count_dict[item["Username"]]:
                        user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                    else:
                        user_count_dict[item["Username"]]["TotalCount"] = 1

            else:
                user_count_dict[item["Username"]] = {item["Role"]:{"actioned":0,"labeled":0,"unlabeled":1,"completed":0,"locked":0,"reassignments":0,"snoozed":0,"manually_added":0 }}
                unlabeled = unlabeled + 1
                if "TotalCount" in user_count_dict[item["Username"]]:
                    user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                else:
                    user_count_dict[item["Username"]]["TotalCount"] = 1

    else:
        if item["Username"] in user_count_dict:
            if item["Role"] in user_count_dict[item["Username"]]:
                user_count_dict[item["Username"]][item["Role"]]["unlabeled"] = user_count_dict[item["Username"]][item["Role"]]["unlabeled"] + 1
                unlabeled = unlabeled + 1
                user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
            else:

                user_count_dict[item["Username"]][item["Role"]] = {"actioned":0,"labeled":0,"unlabeled":1,"completed":0,"locked":0,"reassignments":0,"snoozed":0,"manually_added":0 }
                unlabeled = unlabeled + 1
                if "TotalCount" in user_count_dict[item["Username"]]:
                    user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                else:
                    user_count_dict[item["Username"]]["TotalCount"] = 1

        else:

            user_count_dict[item["Username"]] = {item["Role"]:{"actioned":0,"labeled":0,"unlabeled":1,"completed":0,"locked":0,"reassignments":0,"snoozed":0,"manually_added":0 }}
            unlabeled = unlabeled + 1
            if "TotalCount" in user_count_dict[item["Username"]]:
                user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
            else:
                user_count_dict[item["Username"]]["TotalCount"] = 1

    if "completed" in item:
        if item["completed"]:
            completed = completed + 1

            if item["Username"] in user_count_dict:
                if item["Role"] in user_count_dict[item["Username"]]:
                    user_count_dict[item["Username"]][item["Role"]]["completed"] = user_count_dict[item["Username"]][item["Role"]]["completed"] + 1
                    user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                else:
                    user_count_dict[item["Username"]]["TotalCount"] = 0
                    user_count_dict[item["Username"]][item["Role"]] = {"actioned":0,"labeled":0,"unlabeled":0,"completed":1,"locked":0,"reassignments":0,"snoozed":0,"manually_added":0 }
            else:
                user_count_dict[item["Username"]]["TotalCount"] = 0
                user_count_dict[item["Username"]] = {item["Role"]:{"actioned":0,"labeled":0,"unlabeled":0,"completed":1,"locked":0,"reassignments":0,"snoozed":0,"manually_added":0 }}

    if "locked" in item:
        if item["locked"]:
            locked = locked + 1

            if item["Username"] in user_count_dict:
                if item["Role"] in user_count_dict[item["Username"]]:
                    user_count_dict[item["Username"]][item["Role"]]["locked"] = user_count_dict[item["Username"]][item["Role"]]["locked"] + 1
                    user_count_dict[item["Username"]]["TotalCount"] = user_count_dict[item["Username"]]["TotalCount"] + 1
                else:
                    user_count_dict[item["Username"]]["TotalCount"] = 0
                    user_count_dict[item["Username"]][item["Role"]] = {"actioned":0,"labeled":0,"unlabeled":0,"completed":0,"locked":1,"reassignments":0,"snoozed":0,"manually_added":0 }
            else:
                user_count_dict[item["Username"]]["TotalCount"] = 0
                user_count_dict[item["Username"]] = {item["Role"]:{"actioned":0,"labeled":0,"unlabeled":0,"completed":0,"locked":1,"reassignments":0,"snoozed":0,"manually_added":0 }}

    return user_count_dict, actioned, labeled, unlabeled, completed, locked









def determine_if_tasq_was_reassigned(item):
    return len(item["Assignee"]["reassignment_history"]) > 0

def determine_if_tasq_was_manually_added(item):
    return "ManuallyAssigned" in item


def determine_if_tasq_is_snoozed(item):
    if "snoozed" in item:
        if isinstance(item["snoozed"],dict):
            if item["snoozed"]["Status"] == True:
                snooze_until = datetime.strptime(item["snoozed"]["UntilDate"], '%Y-%m-%dT%H:%M:%S.%fZ')
                current_datetime = datetime.now()
                if current_datetime <= snooze_until:
                    return True
    return False






def get_user_tasq_dict(user, MAX_DAILY_COMPLETION, manually_added_clean_list_all, total_workflow_list_locked_all, total_workflow_list_all, total_no_comms_list_locked_all, total_no_comms_list_all, total_failure_list_locked_all, total_failure_list_all, total_state_change_list_locked_all, total_state_change_list_all, completed_array_all):
    manually_added_clean_list = []
    total_failure_list_locked = []
    total_failure_list = []
    total_state_change_list_locked = []
    total_state_change_list = []
    total_no_comms_list_locked = []
    total_no_comms_list = []
    total_workflow_list_locked = []
    total_workflow_list = []
    completed_array = []
    for item in total_no_comms_list_all:
        if user == item["Username"]:
            total_no_comms_list.append(item)

    for item in total_no_comms_list_locked_all:
        if user == item["Username"]:
            total_no_comms_list_locked.append(item)

    for item in total_failure_list_all:
        if user == item["Username"]:
            total_failure_list.append(item)

    for item in total_failure_list_locked_all:
        if user == item["Username"]:
            total_failure_list_locked.append(item)

    for item in total_state_change_list_locked_all:
        if user == item["Username"]:
            total_state_change_list_locked.append(item)

    for item in total_state_change_list_all:
        if user == item["Username"]:
            total_state_change_list.append(item)

    for item in total_workflow_list_locked_all:
        if user == item["Username"]:
            total_workflow_list_locked.append(item)

    for item in total_workflow_list_all:
        if user == item["Username"]:
            total_workflow_list.append(item)

    for item in completed_array_all:
        if user == item["Username"]:
            completed_array.append(item)



    available_for_today = MAX_DAILY_COMPLETION - len(completed_array)

    total_failure_list = total_failure_list_locked + total_failure_list
    total_state_change_list = total_state_change_list_locked + total_state_change_list
    total_no_comms_list = total_no_comms_list_locked + total_no_comms_list
    total_workflow_list = total_workflow_list_locked + total_workflow_list

    total_list = manually_added_clean_list + total_no_comms_list + total_failure_list + total_workflow_list + total_state_change_list
    total_list = total_list[:available_for_today]

    total_no_comms_list = []
    total_state_change_list = []
    total_failure_list = []
    total_workflow_list = []


    snoozed_count = 0
    rejected_count = 0
    delayed_count = 0
    locked_count = 0
    reassigned_count = 0
    completed_count = 0
    total_count = len(total_list)


    for item in total_list:
        if item["PredictionType"] == "state change":
            total_state_change_list.append(item)
        if item["PredictionType"] == "failure prediction":
            total_failure_list.append(item)
        if item["PredictionType"] == "No Comms":
            total_no_comms_list.append(item)
        if item["PredictionType"] == "Workflow":
            total_workflow_list.append(item)

        if "snoozed" in item:
            if item["snoozed"]["Status"] == True:
                snoozed_count = snoozed_count + 1

        if "rejected" in item:
            if isinstance(item["rejected"],dict):
                if item["rejected"]["Status"] == True:
                    rejected_count = rejected_count + 1
            else:
                if item["rejected"] == True:
                    rejected_count = rejected_count + 1

        if "delayed" in item:
            if item["delayed"] == True:
                delayed_count = delayed_count + 1

        if "locked" in item:
            if item["locked"] == True:
                locked_count = locked_count + 1


    return({
        "snoozed_count": snoozed_count,
        "rejected_count": rejected_count,
        "delayed_count": delayed_count,
        "locked_count": locked_count,
        "completed_count": len(completed_array),
        "manually_added_task_list": manually_added_clean_list,
        "total_failure_list": total_failure_list,
        "total_state_change_list": total_state_change_list,
        "total_no_comms_list": total_no_comms_list,
        "total_workflow_list": total_workflow_list,
        "tasq_list": total_list,
        "completed_list": completed_array
    })



def get_full_user_list(event, context):
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
    response = client.list_users(
        UserPoolId=user_pool_id,
        AttributesToGet=[
            'sub',
            'email',
            'custom:is_test_user'
        ],
    )
    available_users = []

    check_string_val = "false"
    if should_assign_test_user and should_assign_test_user != "false" and should_assign_test_user != "False":
        check_string_val = "true"
    for User in response["Users"]:
        contains_test_user_attr = False
        should_add_user = False
        for Attribute in User["Attributes"]:
            if (Attribute["Name"] == "custom:is_test_user"):
                contains_test_user_attr = True
                if (Attribute["Value"] == check_string_val):
                    should_add_user = True
        if (not contains_test_user_attr) and (not should_assign_test_user):
            should_add_user = True

        if should_add_user:
            available_users.append(User)



    return({
        "full_user_list": available_users,
        "success": True,
        "error": False,
        "error_msg": "Success"
    })





def get_reassignment_list(event, context):

    if "input" in event:
        event = event["input"]

    dynamodb = boto3.resource('dynamodb')
    dynamo_db_table_name = os.environ['WORKFLOW_OUTPUT_TABLE']
    table = dynamodb.Table(dynamo_db_table_name)
    if "input" in event:
        event = event["input"]

    MAX_DAILY_COMPLETION = 20

    if "input" in event:
        event = event["input"]

    prediction_minimum_non_locked_results = 3
    failure_minimum_non_locked_results = 3
    state_change_minimum_non_locked_results = 3
    completed_minimum_non_locked_results = 3

    prediction_soft_limit = 1000
    failure_soft_limit = 1000
    state_change_soft_limit = 1000
    completed_soft_limit = -1

    show_completed_from_midnight = True
    if "show_completed_from_midnight" in event:
        show_completed_from_midnight = event["show_completed_from_midnight"]
    if "prediction_minimum_non_locked_results" in event:
        prediction_minimum_non_locked_results = event["prediction_minimum_non_locked_results"]
    if "failure_minimum_non_locked_results" in event:
        failure_minimum_non_locked_results = event["failure_minimum_non_locked_results"]
    if "state_change_minimum_non_locked_results" in event:
        state_change_minimum_non_locked_results = event["state_change_minimum_non_locked_results"]
    if "prediction_soft_limit" in event:
        prediction_soft_limit = event["prediction_soft_limit"]
    if "failure_soft_limit" in event:
        failure_soft_limit = event["failure_soft_limit"]
    if "state_change_soft_limit" in event:
        state_change_soft_limit = event["state_change_soft_limit"]



    start_of_day = datetime.now()
    three_days_ago = start_of_day - timedelta(days=3)
    start_of_day_string = three_days_ago.strftime("%Y-%m-%dT00:00:00")
    fe       = Key('AssignmentTime').gte(start_of_day_string) # & Key('time').lte(to_time);
    response = table.scan(
        IndexName='NodeID-AssignmentTime-index',
        FilterExpression= fe
    )
    completed_array = []
    node_id_state_change_dict = {}
    node_id_failure_dict = {}
    node_id_workflow_dict = {}
    no_comms_dict = {}
    manually_added_tasks = []
    user_array = []
    for response_item in response["Items"]:
        if not (response_item["Username"] in user_array):
            user_array.append(response_item["Username"])
        if "completed" in response_item:
            if response_item["completed"]:
                if "ResponseData" in response_item:
                    if "ResponseTime" in response_item["ResponseData"]:
                        reponse_time = datetime.strptime(response_item["ResponseData"]["ResponseTime"], '%Y-%m-%dT%H:%M:%S')
                        start_of_day = datetime.now(pytz.timezone('America/Denver'))
                        start_of_day_string = start_of_day.strftime("%Y-%m-%dT00:00:00")
                        start_of_day = datetime.strptime(start_of_day_string, '%Y-%m-%dT%H:%M:%S')
                        if reponse_time > start_of_day:
                            completed_array.append(response_item)

                continue
        if "ManuallyAssigned" in response_item:
            if response_item["ManuallyAssigned"]:
                manually_added_tasks.append(response_item)
                continue
        if "rejected" in response_item:
            if isinstance(response_item["rejected"],dict):
                if response_item["rejected"]["Status"] == True:
                    continue
            else:
                continue
        if "snoozed" in response_item:
            if isinstance(response_item["snoozed"],dict):
                if response_item["snoozed"]["Status"] == True:
                    snooze_until = datetime.strptime(response_item["snoozed"]["UntilDate"], '%Y-%m-%dT%H:%M:%S.%fZ')
                    current_datetime = datetime.now()
                    if current_datetime <= snooze_until:
                        continue
            else:
                continue
        is_failure_type = False
        if response_item["PredictionType"] == "failure prediction":
            failure_end = datetime.strptime(response_item['Prediction']['FailureEnd'], '%Y-%m-%dT%H:%M:%S')
            is_failure_type = True
            if datetime.now() > failure_end:
                continue


        if response_item["PredictionType"] == "Workflow":
            if response_item["NodeID"] in node_id_workflow_dict:
                node_id_workflow_dict[response_item["NodeID"]].append(response_item)
            else:
                node_id_workflow_dict[response_item["NodeID"]] = []
                node_id_workflow_dict[response_item["NodeID"]].append(response_item)
            continue

        if response_item["PredictionType"] == "No Comms":
            if response_item["NodeID"] in no_comms_dict:
                no_comms_dict[response_item["NodeID"]].append(response_item)
            else:
                no_comms_dict[response_item["NodeID"]] = []
                no_comms_dict[response_item["NodeID"]].append(response_item)
            continue

        if is_failure_type:
            # Failure types always take precedence over state changes, clear the state changes if failure type exists
            if response_item["NodeID"] in node_id_state_change_dict:
                node_id_state_change_dict["NodeID"] = []

            if response_item["NodeID"] in node_id_failure_dict:
                node_id_failure_dict[response_item["NodeID"]].append(response_item)
            else:
                node_id_failure_dict[response_item["NodeID"]] = []
                node_id_failure_dict[response_item["NodeID"]].append(response_item)
        else:
            # Failure types always take precedence over state changes, skip if a failure exists for this node
            if response_item["NodeID"] in node_id_failure_dict:
                continue
            if response_item["NodeID"] in node_id_state_change_dict:
                node_id_state_change_dict[response_item["NodeID"]].append(response_item)
            else:
                node_id_state_change_dict[response_item["NodeID"]] = []
                node_id_state_change_dict[response_item["NodeID"]].append(response_item)





    total_failure_list_locked = []
    total_failure_list = []
    total_state_change_list = []
    total_state_change_list_locked = []
    total_no_comms_list = []
    total_no_comms_list_locked = []
    total_workflow_list = []
    total_workflow_list_locked = []


    for key, value in node_id_workflow_dict.items():

        sorted_by_production_avg = sorted(value, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)
        if len(sorted_by_production_avg) == 0:
            continue
        if "locked" in sorted_by_production_avg[0]:
            total_workflow_list_locked.append(sorted_by_production_avg[0])
        else:
            total_workflow_list.append(sorted_by_production_avg[0])

    for key, value in no_comms_dict.items():

        sorted_by_production_avg = sorted(value, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)
        if len(sorted_by_production_avg) == 0:
            continue
        if "locked" in sorted_by_production_avg[0]:
            total_no_comms_list_locked.append(sorted_by_production_avg[0])
        else:
            total_no_comms_list.append(sorted_by_production_avg[0])

    for key, value in node_id_failure_dict.items():

        sorted_by_production_avg = sorted(value, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)
        if len(sorted_by_production_avg) == 0:
            continue
        if "locked" in sorted_by_production_avg[0]:
            total_failure_list_locked.append(sorted_by_production_avg[0])
        else:
            total_failure_list.append(sorted_by_production_avg[0])

    for key, value in node_id_state_change_dict.items():
        sorted_by_production_avg = sorted(value, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)
        if len(sorted_by_production_avg) == 0:
            continue
        if "locked" in sorted_by_production_avg[0]:
            total_state_change_list_locked.append(sorted_by_production_avg[0])
        else:
            total_state_change_list.append(sorted_by_production_avg[0])

    total_failure_list = sorted(total_failure_list, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)
    total_failure_list_locked = sorted(total_failure_list_locked, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)
    total_state_change_list = sorted(total_state_change_list, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)
    total_state_change_list_locked = sorted(total_state_change_list_locked, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)
    total_no_comms_list = sorted(total_no_comms_list, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)
    total_no_comms_list_locked = sorted(total_no_comms_list_locked, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)
    total_workflow_list = sorted(total_workflow_list, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)
    total_workflow_list_locked = sorted(total_workflow_list_locked, key=lambda x: x["ProductionAverage"] if x["ProductionAverage"] else -1, reverse=True)


    manually_added_clean_list = []
    for user in manually_added_tasks:
        if "completed" in user:
            if not user["completed"]:
                manually_added_clean_list.append(user)
        else:
            manually_added_clean_list.append(user)



    user_dict = {}
    for user in user_array:
        user_dict[user] = get_user_tasq_dict(user, MAX_DAILY_COMPLETION, manually_added_clean_list, total_workflow_list_locked, total_workflow_list, total_no_comms_list_locked, total_no_comms_list, total_failure_list_locked, total_failure_list, total_state_change_list_locked, total_state_change_list, completed_array)

    completed_count = 0
    locked_count = 0
    delayed_count = 0
    rejected_count = 0
    snoozed_count = 0
    total_failure_list = []
    total_state_change_list = []
    total_workflow_list = []
    total_no_comms_list = []
    completed_list = []
    manually_added_clean_list = []
    for key, value in user_dict.items():
        total_failure_list.extend(value["total_failure_list"])
        total_state_change_list.extend(value["total_state_change_list"])
        total_workflow_list.extend(value["total_workflow_list"])
        total_no_comms_list.extend(value["total_no_comms_list"])
        completed_list.extend(value["completed_list"])
        manually_added_clean_list.extend(value["manually_added_task_list"])
        completed_count = completed_count + value["completed_count"]
        locked_count = locked_count + value["locked_count"]
        delayed_count = delayed_count + value["delayed_count"]
        rejected_count = rejected_count + value["rejected_count"]
        snoozed_count = snoozed_count + value["snoozed_count"]

    total_list = manually_added_clean_list + total_no_comms_list + total_failure_list + total_workflow_list + total_state_change_list


    return_total_list = []
    actioned = 0
    labeled = 0
    unlabeled = 0
    completed = 0
    locked = 0



    user_count_dict = {}
    for item in total_list:

        if "PredictionType" in item:

            if "No Comms" in item["PredictionType"]:
                return_total_list.append(item)
                user_count_dict, actioned, labeled, unlabeled, completed, locked = calculate_user_dict_reassignment_list("NoCommCounts", item, user_count_dict, actioned, labeled, unlabeled, completed, locked)

            if "Workflow" in item["PredictionType"]:
                return_total_list.append(item)
                user_count_dict, actioned, labeled, unlabeled, completed, locked = calculate_user_dict_reassignment_list("WorkflowCounts", item, user_count_dict, actioned, labeled, unlabeled, completed, locked)


            if "state change" in item["PredictionType"]:
                return_total_list.append(item)
                user_count_dict, actioned, labeled, unlabeled, completed, locked = calculate_user_dict_reassignment_list("StateChangeCounts", item, user_count_dict, actioned, labeled, unlabeled, completed, locked)

            if "failure prediction" in item["PredictionType"]:
                return_total_list.append(item)
                user_count_dict, actioned, labeled, unlabeled, completed, locked = calculate_user_dict_reassignment_list("FailureCounts", item, user_count_dict, actioned, labeled, unlabeled, completed, locked)



            if item["Username"] in user_count_dict:
                user_count_dict[item["Username"]][item["Role"]]["reassignments"] = user_count_dict[item["Username"]][item["Role"]]["reassignments"] + (1 if determine_if_tasq_was_reassigned(item) else 0)
                user_count_dict[item["Username"]][item["Role"]]["manually_added"] = user_count_dict[item["Username"]][item["Role"]]["manually_added"] + (1 if determine_if_tasq_was_manually_added(item) else 0)
                user_count_dict[item["Username"]][item["Role"]]["snoozed"] = user_count_dict[item["Username"]][item["Role"]]["manually_added"] + (1 if determine_if_tasq_is_snoozed(item) else 0)







    secrets_client = boto3.client('secretsmanager')
    # user_pool = "dev/enerplus/cognito/pool"
    user_pool = os.environ['USER_POOL']
    should_assign_test_user = os.environ['SHOULD_ASSIGN_TEST_USER']
    # should_assign_test_user = "true"
    secrets_response = secrets_client.get_secret_value(SecretId=user_pool)
    user_pool_config = json.loads(secrets_response['SecretString'])
    user_pool_id = user_pool_config['user_pool_id']
    user_pool_region = user_pool_config['user_pool_region']

    client = boto3.client('cognito-idp', region_name=user_pool_region)
    sleep(4)
    response = client.list_users(
        UserPoolId=user_pool_id,
        AttributesToGet=[
            'sub',
            'email',
            'custom:is_test_user'
        ],
    )
    available_users = []

    check_string_val = "false"
    if should_assign_test_user and should_assign_test_user != "false" and should_assign_test_user != "False":
        check_string_val = "true"
    for User in response["Users"]:
        contains_test_user_attr = False
        should_add_user = False
        user_email = None
        for Attribute in User["Attributes"]:
            if (Attribute["Name"] == "email"):
                user_email = Attribute["Value"]
            if (Attribute["Name"] == "custom:is_test_user"):
                contains_test_user_attr = True
                if (Attribute["Value"] == check_string_val):
                    should_add_user = True
        if (not contains_test_user_attr) and (not should_assign_test_user):
            should_add_user = True

        if should_add_user:
            available_users.append(user_email)



    for available_user in available_users:
        if not (available_user in user_count_dict):
            user_count_dict[available_user] = {"TotalCount":0}




    return({
        "UserDict": user_count_dict
    })
