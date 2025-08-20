# Knowledge Base Sync Lambda Function

This Lambda function is triggered by S3 events when PDF files are uploaded to the source bucket. It automatically syncs the uploaded files with your Bedrock Knowledge Base.

## How it works:

1. **S3 Event Trigger**: When a PDF file is uploaded to the S3 bucket, it triggers this Lambda function
2. **File Processing**: The function processes only PDF files (skips other file types)
3. **Knowledge Base Sync**: It starts an ingestion job to sync the new file with your Bedrock Knowledge Base
4. **Status Monitoring**: The function waits for the ingestion job to complete and logs the status

## Environment Variables:

- `KNOWLEDGE_BASE_ID`: Your Bedrock Knowledge Base ID
- `AWS_REGION`: AWS region (defaults to us-west-2)

## Permissions:

The Lambda function needs permissions to:

- Read from the S3 bucket
- Call Bedrock APIs for Knowledge Base operations

## Monitoring:

You can monitor the function execution in CloudWatch Logs. The function logs:

- File processing events
- Knowledge Base sync attempts
- Ingestion job status
- Success/failure messages

## Deployment:

This function is deployed as part of the CDK stack in `infrastructure/lib/ragbot2_stack.py`.

### Building the Lambda Package:

The Lambda function requires external dependencies (like `requests`) to be packaged with the deployment. The CDK stack will automatically build the package if it doesn't exist, but you can also build it manually:

```bash
cd infrastructure/lambda
python build_package.py
```

This creates a `package/` directory containing the Lambda function code and all its dependencies.

### Manual Deployment:

If you need to deploy manually, make sure to build the package first:

1. Build the package: `python build_package.py`
2. Deploy with CDK: `cdk deploy`
