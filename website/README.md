# Visual Insigths Website

Front end single page application to inference images. It is built for desktop and mobile clients.

## Project Setup

```sh
npm install
```

### Customize configuration and code

There are two files that need to be changed prior to run the solution:

1. [aws-exports.js](./src/aws-exports.js): The paremeters aws_project_region, aws_cognito_region (for example, us-east-1), aws_user_pools_id and aws_user_pools_web_client_id need to be changed for the AWS region, the cognito user pool ID and the client id to be used by this application. The user pool and the client id are created following the steps in [here](../infrastructure/README.md)

    Once they are created, you can find the pool ID in the console or executing this command:

    ```bash
    aws cognito-idp list-user-pools --max-results 60 --query "UserPools[?Name=='VisualInsightsAIUserPool']"
    ```

    The client id can be also be found in the console, in the App Integration tab, or using this command:

    ```bash
    aws cognito-idp list-user-pool-clients --user-pool-id CHANGE_ME_FOR_THE_USER_POOL_ID
    ```

    The aws-export.js file should look similar to this:

    ```json
    const awsmobile = {
        "aws_project_region": "us-east-1",
        "aws_cognito_region": "us-east-1",
        "aws_user_pools_id": "us-east-1_aabCCCCDD",
        "aws_user_pools_web_client_id": "1234564123456750hckp6pq0rf",
        (...)
    }
    ```

2. [App.vue](./src/App.vue): The API gateway URL needs to be added in place of all "CHANGE_ME" occurrences in this file. You can find the value in the output of the SAM template executed [here](../infrastructure/README.md) or in the console. The App.vue file should look similar to this:

```javascript
(...)
currentSession().then(idToken => {
          fetch("https://0123456789.execute-api.us-east-1.amazonaws.com/(...)", {
            "method": "POST",
            "body": body,
(...)
```

### Compile and Hot-Reload for local development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

### Upload to S3 for web serving

Once the build for production has been done, upload the dist directory to a S3 bucket and create a cloudfront distribution to serve the application. [Example](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/getting-started-secure-static-website-cloudformation-template.html)