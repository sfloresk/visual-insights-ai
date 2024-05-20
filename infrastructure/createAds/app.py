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
table_name = os.getenv('ADS_TABLE_NAME')

# Bedrock Runtime client used to invoke and question the models
bedrock_client = boto3.client('bedrock-runtime')

def call_foundational_model(stop_sequences,system,messages):
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
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

def create_ad(products):
    system = """You are AI that create ads for similar products found in customer's kitchen."""
    prompt = """
    Rules:
    1. Identify what might be of interest for the customer.
    2. Select a product name and a brand based of the interest of the customer
    3. Return an ad string that can be put in front of customers while they browse for products
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
                        "ad_text": {
                            "type": "string",
                            "description": "Text ad to use with the customer"
                        }
                    }
                }
        </result>
    </schema>
    Now, provide an ad based on the following products:
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
    # remove scape characters to avoid issues with json.loads
    response_llm = json.loads(call_foundational_model(stop_squences,system,messages),strict=False)
    return response_llm['ad_text'], response_llm['thinking']

def add_to_ads_table(ad, analysis,user_email_hash_key):
    ad_id = f"adid#{abs(hash(ad))}"
    logger.info(f"Adding ad {ad_id} to table {table_name}")
    dynamodb_client.put_item(
        TableName=table_name,
        Item={
            'adId': {'S': ad_id},
            'analysis': {'S': analysis},
            'ad': {'S': ad},
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
                logger.info("Creating ad for:")
                logger.info(json.dumps(products))
                ad, analysis = create_ad(products)
                add_to_ads_table(ad, analysis, message_body['userEmail']['S'])
            except Exception as e:
                # print traceback
                logger.error(str(e))
                logger.error(traceback.format_exc())
                
                batch_item_failures.append({"itemIdentifier": record['messageId']})
        
        sqs_batch_response["batchItemFailures"] = batch_item_failures
        return sqs_batch_response


