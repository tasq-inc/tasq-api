import boto3
from boto3.dynamodb.conditions import Key, Attr
import os
from datetime import date, datetime
from datetime import timedelta
import secrets
import uuid
import botocore
import json

api_gateway_table_string = os.environ["API_GATEWAY_TOKENS_TABLE"]


def generatePolicy(principalId, effect, methodArn):
    authResponse = {'principalId': principalId}
    if effect and methodArn:
        policyDocument = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Sid': 'FirstStatement',
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': "*"
                }
            ]
        }

        authResponse['policyDocument'] = policyDocument

    return authResponse

def authorize_api_user(event, context):
    try:
        # Verify and get information from id_token
        token = event['authorizationToken']
        print("EVENT: ")
        print(event)
        print(context)
        # token = token.replace("token ", "")

        # Check that token exists in DB
        dynamodb = boto3.resource('dynamodb')
        ae = Attr('AccessToken').eq(token)
        api_gateway_table = dynamodb.Table(api_gateway_table_string)
        response = api_gateway_table.scan(
            IndexName="AccessToken-index",
            FilterExpression=ae
        )
        if len(response["Items"]) == 0:
            return generatePolicy(None, 'Deny', event['methodArn'])

    except ValueError as err:
        # Deny access if the token is invalid
        print(err)
        return generatePolicy(None, 'Deny', event['methodArn'])

    return generatePolicy(token, 'Allow', event['methodArn'])



def create_new_auth_token(event, context):
    if "input" in event:
        event = event["input"]

    username_passed = event["Username"]
    token_name = event["TokenName"]
    dynamodb = boto3.resource('dynamodb')
    api_gateway_table = dynamodb.Table(api_gateway_table_string)

    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # object = s3.Object(analytics_bucket, "load_time/" + username + "/" + page + "/{}.txt".format(current_date))
    operator = event["operator"]

    AccessToken = secrets.token_hex(40)
    TokenID = str(uuid.uuid4())
    data = {
      "TokenID":TokenID,
      "time":current_date,
      "Username": username_passed,
      "AccessToken":AccessToken,
      "TokenName":token_name,
      "Operator":operator
    }
    api_gateway_table.put_item(
        Item=data
    )

    return(data)



def get_auth_token(event, context):
    if "input" in event:
        event = event["input"]

    username_passed = event["Username"]
    dynamodb = boto3.resource('dynamodb')
    api_gateway_table = dynamodb.Table(api_gateway_table_string)


    fe       = Key('Username').eq(username_passed)
    response = api_gateway_table.scan(
        FilterExpression=fe
    )
    response_items = response["Items"]
    for index, response_item in enumerate(response_items):
        del response_item["AccessToken"]
        response_items[index] = response_item

    return({
        "TokenData":response_items
    })




''' Fetch dynamodb data by scan or query

    :param table: String - <DYNAMODB_TABLE_NAME>
    :param kce: KeyConditionExpression - Key("<KEY>").eq("<VALUE>") & Key("<KEY_TWO>").eq("<VALUE_TWO>")
    :param index_name: String - "<FIELD>-index"
    :param mode: String - "query" | "scan"
    :return results: Array - [<WORKFLOW_RECORED_ONE>, <WORKFLOW_RECORED_TWO>, ...]
'''
def _query_dynamodb(table: str, kce=None, index_name=None, mode="query"):
    results = []
    table = boto3.resource("dynamodb").Table(table)
    if mode == "query" and kce and index_name:
        query = {}
        while not query or "LastEvaluatedKey" in query:
            if query:
                query = table.query(
                    IndexName=index_name,
                    ExclusiveStartKey=query["LastEvaluatedKey"],
                    KeyConditionExpression=kce,
                )
            else:
                query = table.query(IndexName=index_name, KeyConditionExpression=kce)
            results.extend(query["Items"])
    elif mode == "query" and kce:
        query = {}
        while not query or "LastEvaluatedKey" in query:
            if query:
                query = table.query(
                    ExclusiveStartKey=query["LastEvaluatedKey"],
                    KeyConditionExpression=kce,
                )
            else:
                query = table.query(KeyConditionExpression=kce)
            results.extend(query["Items"])
    elif mode == "scan" and kce is None:
        scan = {}
        while not scan or "LastEvaluatedKey" in scan:
            if scan:
                scan = table.scan(
                    ExclusiveStartKey=scan["LastEvaluatedKey"],
                )
            else:
                scan = table.scan()
            results.extend(scan["Items"])
    elif mode == "scan":
        scan = {}
        while not scan or "LastEvaluatedKey" in scan:
            if scan:
                scan = table.scan(
                    ExclusiveStartKey=scan["LastEvaluatedKey"],
                    FilterExpression=kce
                )
            else:
                scan = table.scan(FilterExpression=kce)
            results.extend(scan["Items"])
    return results




def _resolve_operator_syntax(operator, mode=None):
    operator_map = {
        "Enerplus": ["enerplus"],
        "Red Wolf": [
            "redwolf",
            "red-wolf",
            "Redwolf",
            "RedWolf",
            "Red-Wolf",
            "red wolf",
        ],
        "Riley": ["riley"],
        "Extraction": ["extraction", "civitas", "Civitas"],
        "SWN": ["swn"],
        "pdce": ["pdc", "PDC", "PDCE"],
        "FC": ["fc"],
        "Validus": ["validus"],
        "caerus": ["Caerus"],
        "taprock": ["Taprock", "taprock"],
        "petronas": ["petronascanada", "Petronascanada", "PetronasCanada", "Petronas Canada", "petronas canada"],
    }
    resolved_operator = [
        k for k, v in operator_map.items() if operator in v or operator == k
    ]
    if len(resolved_operator) > 1 or not resolved_operator:
        raise ValueError("Could not resolve Operator")
    else:
        return (
            resolved_operator[0].replace(" ", "-")
            if mode == "github"
            else resolved_operator[0]
        )



def get_signals_from_api(event, context):
    print(event)
    print(context)

    kce = Key("AccessToken").eq(event["headers"]['Authorization'])
    records = _query_dynamodb(api_gateway_table_string, kce=kce, index_name="AccessToken-index", mode="query")

    event_body = event["body"]
    event_body["operator"] = _resolve_operator_syntax(records[0]["Operator"])

    config = botocore.config.Config(
        read_timeout=11000,
        connect_timeout=11000,
    )

    # tasq-data-service-dev-CleanDataAppSyncSourcev2
    session = boto3.Session()
    client = session.client("lambda", config=config)
    response = client.invoke(
        FunctionName='tasq-data-service-{env}-CleanDataAppSyncSourcev2'.format(env=os.environ["STAGE"]),
        Payload=json.dumps(event_body),
    )

    return json.loads(response['Payload'].read())



def get_production_data_from_api(event, context):
    print(event)
    print(context)

    kce = Key("AccessToken").eq(event["headers"]['Authorization'])
    records = _query_dynamodb(api_gateway_table_string, kce=kce, index_name="AccessToken-index", mode="query")

    event_body = event["body"]
    event_body["operator"] = _resolve_operator_syntax(records[0]["Operator"])

    config = botocore.config.Config(
        read_timeout=11000,
        connect_timeout=11000,
    )

    # tasq-data-service-dev-CleanDataAppSyncSourcev2
    session = boto3.Session()
    client = session.client("lambda", config=config)
    response = client.invoke(
        FunctionName='tasq-data-service-{env}-CleanDataAppSyncSource5v2'.format(env=os.environ["STAGE"]),
        Payload=json.dumps(event_body),
    )

    return json.loads(response['Payload'].read())




def get_meta_data_from_api(event, context):
    print(event)
    print(context)

    kce = Key("AccessToken").eq(event["headers"]['Authorization'])
    records = _query_dynamodb(api_gateway_table_string, kce=kce, index_name="AccessToken-index", mode="query")

    event_body = event["body"]
    event_body["operator"] = _resolve_operator_syntax(records[0]["Operator"])

    config = botocore.config.Config(
        read_timeout=11000,
        connect_timeout=11000,
    )

    # tasq-data-service-dev-CleanDataAppSyncSourcev2
    session = boto3.Session()
    client = session.client("lambda", config=config)
    response = client.invoke(
        FunctionName='tasq-data-service-{env}-MetadataNodeMetaAppSyncSource1'.format(env=os.environ["STAGE"]),
        Payload=json.dumps(event_body),
    )

    return json.loads(response['Payload'].read())



def get_enabled_wells_from_api(event, context):
    print(event)
    print(context)

    kce = Key("AccessToken").eq(event["headers"]['Authorization'])
    records = _query_dynamodb(api_gateway_table_string, kce=kce, index_name="AccessToken-index", mode="query")

    event_body = event["body"]
    event_body["operator"] = _resolve_operator_syntax(records[0]["Operator"])

    config = botocore.config.Config(
        read_timeout=11000,
        connect_timeout=11000,
    )

    # tasq-data-service-dev-CleanDataAppSyncSourcev2
    session = boto3.Session()
    client = session.client("lambda", config=config)
    response = client.invoke(
        FunctionName='tasq-data-service-{env}-MetadataEnabledWellsAppSyncSource1'.format(env=os.environ["STAGE"]),
        Payload=json.dumps(event_body),
    )

    return json.loads(response['Payload'].read())



def get_description_from_api(event, context):
    print(event)
    print(context)

    kce = Key("AccessToken").eq(event["headers"]['Authorization'])
    records = _query_dynamodb(api_gateway_table_string, kce=kce, index_name="AccessToken-index", mode="query")

    event_body = event["body"]
    event_body["operator"] = _resolve_operator_syntax(records[0]["Operator"])

    config = botocore.config.Config(
        read_timeout=11000,
        connect_timeout=11000,
    )

    # tasq-data-service-dev-CleanDataAppSyncSourcev2
    session = boto3.Session()
    client = session.client("lambda", config=config)
    response = client.invoke(
        FunctionName='tasq-data-service-{env}-CleanDataAppSyncSource3v2'.format(env=os.environ["STAGE"]),
        Payload=json.dumps(event_body),
    )

    return json.loads(response['Payload'].read())