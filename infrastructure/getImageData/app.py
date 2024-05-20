import boto3
import base64
import json
import os
import logging
import sys
from datetime import date
from datetime import datetime

# Setup logging
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

# Initialize the S3 client
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

        
# Bedrock Runtime client used to invoke and question the models
bedrock_client = boto3.client('bedrock-runtime')

def store_in_dynamodb(file_name, response_text, user_email_hash):
    table_name = os.getenv('DYNAMODB_RESULTS_TABLE_NAME')
    today = date.today()
    now = datetime.now()
    
    dynamodb.put_item(
        TableName=table_name,
        # TODO: DynamoDB model can be improved
        Item={
            'fileName': {'S': file_name},
            'extractedInfo': {'S': response_text},
            'date': {'S': f'{today.strftime("%b-%d-%Y")} {now.strftime("%H:%M:%S")}'},
            'userEmail': {'S': f"user#{user_email_hash}"}
        }
    )
    
def invoke_model(body, model_id, accept, content_type):
    response = bedrock_client.invoke_model(body=body, modelId=model_id, accept=accept, contentType=content_type)
    return response

def get_response_text(response):
    
    response_body = json.loads(response.get('body').read())
    response_text = response_body.get('content')[0]['text']
    return response_text

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
    response = invoke_model(body, 'anthropic.claude-3-sonnet-20240229-v1:0', accept, content_type)
    response_text = get_response_text(response)
    logger.info(f"Model response: {response_text}")
    return response_text

def upload_to_s3(file_name,file_content,hash_user_email):
    # create hash from user_email
    
    bucket_name = os.getenv('S3_BUCKET_NAME')
    logger.info(f"Using bucket name {bucket_name}")
    s3.put_object(Bucket=bucket_name, Key=f"{hash_user_email}/{file_name}", Body=file_content)
    

def lambda_handler(event, context):
    logger.info(f"Event: {json.dumps(event['requestContext'])}")
    
    response_lambda = {
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Headers': '*'
        }
    }
    # Get the file content from the event
    # Assume the file content is sent as a base64 encoded string in the 'file_content' field
    
    body = json.loads(event['body'])
    # Extract the 'file_content' field
    file_content_base64 = body['file_content']
    file_content = base64.b64decode(file_content_base64)
    
    # Assume the file name is sent in the 'file_name' field
    file_name = body['file_name']
    prompt = """
    Per each product item in the picture:
    1. Identify the name of the product. If you don't know the product, just say "unknown"
    2. Identify the brand of the product. If you don't know the brand, just say "unknown"
    3. Use the following schema
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
                    "products": {
                        "type": "array",
                        "items": { "$ref": "#/$defs/product" }
                    }
                },
                "$defs": {
                    "product": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the product."
                        },
                        "brand": {
                            "type": "string",
                            "description": "The brand of the product."
                        },
                        "content": {
                            "type": "string",
                            "description": "The content of the product."
                        }
                    }
                }
            }
    </result>

    Now, carefully review every item in Image 1.
    """
    system = """You are an image recognition AI assistant that identify food products."""
    messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Image 1:"
                        },
                        {
                                  "type": "image",
                                  "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": file_content_base64
                                  }
                        },
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
    response_llm_image = call_foundational_model(stop_squences,system,messages)
    #products = response_llm_image.split('<products>')[1].split('</products>')[0].strip()
    products = json.loads(response_llm_image)
    #convert xml to json
    #products = xmltodict.parse(f"<products>{products.replace('&','and')}</products>")

    # Get the bucket name
    user_email = event['requestContext']['authorizer']['claims']['email']
    hash_user_email = abs(hash(user_email))
    upload_to_s3(file_name,file_content,hash_user_email)
    store_in_dynamodb(file_name, json.dumps(products), hash_user_email)
    response_lambda['statusCode'] = 200
    response_lambda['body'] = json.dumps(products)
    return response_lambda

