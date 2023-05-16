import boto3
from boto3.dynamodb.conditions import Key, Attr
import os
from datetime import date, datetime
from datetime import timedelta
import secrets
import uuid

api_gateway_table_string = os.environ["API_GATEWAY_TOKENS_TABLE"]


def generatePolicy(principalId, effect, methodArn):
    authResponse = {}
    authResponse['principalId'] = principalId

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

