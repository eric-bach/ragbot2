import json
import boto3
import os
from urllib.parse import unquote_plus
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Lambda function to sync uploaded PDF files with Bedrock Knowledge Base
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Get the S3 event details
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        
        logger.info(f"Processing file: {bucket_name}/{key}")
        
        # Only process PDF files
        if not key.lower().endswith('.pdf'):
            logger.info(f"Skipping non-PDF file: {key}")
            continue
            
        try:
            # Get the Knowledge Base ID from environment
            knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID')
            knowledge_base_data_source_id = os.environ.get('KNOWLEDGE_BASE_DATA_SOURCE_ID')
            if not knowledge_base_id or not knowledge_base_data_source_id:
                logger.error("ERROR: KNOWLEDGE_BASE_ID or KNOWLEDGE_BASE_DATA_SOURCE_ID environment variable not set")
                return {
                    'statusCode': 500,
                    'body': json.dumps('Knowledge Base ID or Data Source ID not configured')
                }
            
            # Initialize Bedrock client
            bedrock = boto3.client('bedrock-agent', region_name=os.environ.get('AWS_REGION', 'us-west-2'))
            
            # Get the S3 object details
            s3_client = boto3.client('s3')
            s3_object = s3_client.get_object(Bucket=bucket_name, Key=key)
            
            logger.info(f"Syncing file {key} with Knowledge Base {knowledge_base_id}")
            
            # Create a data source sync request
            # This is the actual sync operation with Bedrock Knowledge Base
            try:
                # Start an ingestion job to sync the new file
                response = bedrock.start_ingestion_job(
                    knowledgeBaseId=knowledge_base_id,
                    dataSourceId=knowledge_base_data_source_id,
                    description=f"Sync uploaded file: {key}"
                )
                
                ingestion_job_id = response['ingestionJob']['ingestionJobId']
                logger.info(f"Started ingestion job {ingestion_job_id} for file {key}")
                
                # Wait for the ingestion job to complete
                import time
                max_wait_time = 300  # 5 minutes
                wait_time = 0
                
                while wait_time < max_wait_time:
                    job_status = bedrock.get_ingestion_job(
                        knowledgeBaseId=knowledge_base_id,
                        dataSourceId=knowledge_base_data_source_id,
                        ingestionJobId=ingestion_job_id
                    )
                    
                    status = job_status['ingestionJob']['status']
                    logger.info(f"Ingestion job {ingestion_job_id} status: {status}")
                    
                    if status in ['COMPLETE', 'FAILED']:
                        break
                    
                    time.sleep(10)  # Wait 10 seconds before checking again
                    wait_time += 10
                
                if status == 'COMPLETE':
                    logger.info(f"Successfully synced file {key} with Knowledge Base")
                    return {
                        'statusCode': 200,
                        'body': json.dumps(f'Successfully synced {key} with Knowledge Base')
                    }
                else:
                    logger.error(f"Failed to sync file {key}: {status}")
                    return {
                        'statusCode': 500,
                        'body': json.dumps(f'Failed to sync file {key}: {status}')
                    }
                    
            except Exception as e:
                logger.error(f"Error syncing with Knowledge Base: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps(f'Error syncing with Knowledge Base: {str(e)}')
                }
            
        except Exception as e:
            logger.error(f"Error processing file {key}: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps(f'Error processing file: {str(e)}')
            }
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed all files')
    } 