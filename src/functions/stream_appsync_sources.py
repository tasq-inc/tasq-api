import os
import boto3

dynamodb = boto3.resource('dynamodb')
workflow_output_table_string = os.environ['WORKFLOW_OUTPUT_TABLE']
workflow_output_table = dynamodb.Table(workflow_output_table_string)

def handler(event, context):

    if len(event["Records"]) == 0:
        return

    record = event["Records"][0]

    # Was a new record inserted?
    dynamodb_item = record["dynamodb"]["NewImage"]
    if "HistoricWorkflowID" in dynamodb_item:
        del dynamodb_item["HistoricWorkflowID"]

    response = workflow_output_table.query(
        IndexName='PredictionID-index',
        KeyConditionExpression=Key('PredictionID').eq(dynamodb_item["PredictionID"]["S"])
    )


    item = response['Items'][0]
    item_workflow_task_id = item["WorkflowTaskID"]

    item = {}
    for parent_key, parent_value in dynamodb_item.items():
        for key, value in parent_value.items():
            item[parent_key] = value

    dynamodb_item["WorkflowTaskID"] = item_workflow_task_id
    item["WorkflowTaskID"] = item_workflow_task_id

    workflow_output_table.put_item(
        ConditionExpression=Key('WorkflowTaskID').eq(item_workflow_task_id),
        Item=item
        # ConditionExpression= Attr("PredictionID").eq(dynamodb_item["PredictionID"]) # 'attribute_not_exists(foo) AND attribute_not_exists(bar)'
    )
