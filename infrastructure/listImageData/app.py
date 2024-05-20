import boto3
import json
import os
import logging
import sys
from boto3.dynamodb.conditions import Key
   
# Setup logging
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

# Initialize a DynamoDB resource
dynamodb = boto3.resource('dynamodb')
# Specify your DynamoDB table name
table_name = os.getenv('DYNAMODB_RESULTS_TABLE_NAME')
table = dynamodb.Table(table_name)

s3_client = boto3.client('s3')

def generate_presigned_url(bucket_name, object_key, expiration=3600):
    """Generate a presigned URL for an S3 object."""
    try:
        response = s3_client.generate_presigned_url('get_object',Params={'Bucket': bucket_name,'Key': object_key},ExpiresIn=expiration)
    except Exception as e:
        print("Error generating presigned URL:", e)
        return None
    return response

def lambda_handler(event, context):
    response_lambda = {
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Headers': '*'
        }
    }
    user_email = event['requestContext']['authorizer']['claims']['email']
    user_email_hash = abs(hash(user_email))
    
    # Query dynamodb table using hash_user_email
    response = table.query(
        KeyConditionExpression=Key('userEmail').eq(f"user#{user_email_hash}"))
    
    # Update extracted_data to include a presigned URL for each item
    extracted_data = []
    for item in response['Items']:
        file_name = item.get('fileName', 'N/A')
        bucket_name = os.getenv('S3_BUCKET_NAME')
        object_key = f"{user_email_hash}/{file_name}"
        #TODO: This should be done with cognity identity pools
        presigned_url = generate_presigned_url(bucket_name, object_key)
        result = json.loads(item.get('extractedInfo', 'N/A'))
        extracted_data.append({
            'fileName': file_name,
            'result': result['products'],
            'presignedUrl': presigned_url,  # Add the presigned URL to the response
            'date':item.get('date', 'N/A')
        })
    
    response_lambda['statusCode'] = 200
    response_lambda['body'] = json.dumps(extracted_data, default=str)
    return response_lambda
