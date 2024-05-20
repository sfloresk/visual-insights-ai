import boto3
import json
import os
import logging
import sys
   
# Setup logging
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

client = boto3.client('sns')


def lambda_handler(event, context):
    logger.info("Received event: " + json.dumps(event, indent=2))
    for record in event['Records']:
        logger.info(record['eventID'])
        logger.info(record['eventName'])
        
        logger.info("DynamoDB Record: " + json.dumps(record['dynamodb'], indent=2))
        if 'NewImage' in record['dynamodb'].keys():
            client.publish(
                TopicArn=os.getenv('SNS_TOPIC'),
                Message=json.dumps(record['dynamodb']['NewImage']),
            )

    return f'Successfully published records to {os.getenv('SNS_TOPIC')}'
