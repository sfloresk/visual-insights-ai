# Visual Insights AI

This code provides an example of how to create an end-to-end solution to inference images provided by the user. It uses dynamodb streams to fan out changes (via lambda and SNS) to multiple SQS queues that can be consumed by downstream systems such as Ads and Analytics.

## Infrastructure

1. Amazon API Gateway - Entry point to send images and text 
2. Amazon Lambda functions - Handle requests to read images, process DynamoDB streams and consume example SQS queues
3. Amazon Cognito - Provides authentication for the API
5. Amazon Bedrock - Used for inference requests to Anthropic Claude 3
6. Amazon S3 - Host the web application and stores the uploaded images
7. Amazon Cloudfront - Content delivery network for the web application
8. DynamoDB - Stores image metadata and results
9. SNS - Used to publish new items in DynamoDB
10. SQS - Queue updates to be processed by additional integrations


[Solution Architecture](./docs/solution_architecture.png)

Most of the deployment of the infrastructure is automated using the Serverless Application Model. For detail instructions, follows the steps [here](./infrastructure/README.md)

## Web portal

Example single page application built in Vue JS and Amplify - it is integrated with Cognito to provide a seamlessly login experience, allowing users to sign up and sign in.

Detail instructions to install the web app can be found [here](./website/README.md)

## Support

Please open an issue for any questions or issues
