import logging
import sys
import boto3
import json
import os
import traceback
# Setup logging
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

dynamodb_client = boto3.client('dynamodb')
table_name = os.getenv('ANALYTICS_TABLE_NAME')

# Bedrock Runtime client used to invoke and question the models
bedrock_client = boto3.client('bedrock-runtime')

def call_foundational_model(stop_sequences,system,messages):
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "stop_sequences":stop_sequences,
        "system":system,
        "messages": messages
    })
    
    accept = 'application/json'
    content_type = 'application/json'
    response = bedrock_client.invoke_model(body=body, modelId='anthropic.claude-3-sonnet-20240229-v1:0', accept=accept, contentType=content_type)
    response_body = json.loads(response.get('body').read())
    response_text = response_body.get('content')[0]['text']
    logger.info(f"Model response: {response_text}")
    return response_text

def create_analytics(products):
    system = """You are AI that create analytics from customer's food products identified in their kitchen"""
    prompt = """
    Rules:
    1. Identify insights from the food products
    2. Create a list of products that the customer might be interested in
    3. Return an analysis that can be used in a report
    4. Use the following schema for the result
    <schema>
        <result>
                {
                    "$id": "https://example.com/arrays.schema.json",
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "thinking": {
                            "type": "string",
                            "description": "Think step by step"
                        },
                        "analysis": {
                            "type": "string",
                            "description": "Text ad to use with the customer"
                        }
                    }
                }
        </result>
    </schema>
    Now, provide an analysis based on the following products:
    
    """
    prompt+=f"<products>{products}</products>"
    
    messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                },{
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "<result>"
                        }
                    ]
                }
            ]
    stop_squences = ["</result>"]
    response_llm = json.loads(call_foundational_model(stop_squences,system,messages),strict=False)
    return response_llm['analysis']

def add_to_analytics_table(analytics,user_email_hash_key):
    analyticsId = f"analyticsId#{abs(hash(analytics))}"
    logger.info(f"Adding analytics {analyticsId} to table {table_name}")
    dynamodb_client.put_item(
        TableName=table_name,
        Item={
            'analyticsId': {'S': analyticsId},
            'analytics': {'S': analytics},
            'userEmail': {'S': user_email_hash_key},   
        }
    )

def lambda_handler(event, context):
    if event:
        batch_item_failures = []
        sqs_batch_response = {}
     
        for record in event["Records"]:
            try:
                message_body = json.loads(json.loads(record['body'])['Message'])
                products = json.loads(message_body['extractedInfo']['S'])['products']
                logger.info("Creating analytics for:")
                logger.info(json.dumps(products))
                analytics = create_analytics(products)
                add_to_analytics_table(analytics, message_body['userEmail']['S'])
            except Exception as e:
                # print traceback
                logger.error(str(e))
                logger.error(traceback.format_exc())
                
                batch_item_failures.append({"itemIdentifier": record['messageId']})
        
        sqs_batch_response["batchItemFailures"] = batch_item_failures
        return sqs_batch_response
    
