import boto3
import logging
from botocore.exceptions import ClientError

# s3_utils.py
def get_s3_client(aws_access_key_id, aws_secret_access_key, aws_region):
    return boto3.client('s3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )

# Function to upload a file to S3
def upload_file_to_s3(file_obj, filename, session_id, aws_access_key_id, aws_secret_access_key, aws_region, s3_bucket):
    s3_client = get_s3_client(aws_access_key_id, aws_secret_access_key, aws_region)
    if not s3_bucket:
        logging.error("S3_BUCKET is not set in the configuration.")
        return None
    
    s3_path = f'{session_id}/{filename}'
    try:
        s3_client.upload_fileobj(file_obj, s3_bucket, s3_path)
        logging.info(f"File uploaded successfully to S3: {s3_path}")
        return s3_path
    except Exception as e:
        logging.error(f"Error uploading file to S3: {e}")
        return None

# Function to download a file from S3
def download_file_from_s3(s3_key, local_path, aws_access_key_id, aws_secret_access_key, aws_region, s3_bucket):
    s3_client = get_s3_client(aws_access_key_id, aws_secret_access_key, aws_region)
    if not s3_bucket:
        logging.error("S3_BUCKET is not set in the configuration.")
        return False

    try:
        s3_client.download_file(s3_bucket, s3_key, local_path)
        logging.info(f"File {s3_key} downloaded successfully from S3 to {local_path}")
        return True
    except Exception as e:
        logging.error(f"Error downloading file from S3: {e}")
        return False

# Function to upload a blank file to S3
def upload_blank_file_to_s3(missing_file, session_id, aws_access_key_id, aws_secret_access_key, aws_region, s3_bucket):
    s3_client = get_s3_client(aws_access_key_id, aws_secret_access_key, aws_region)
    if not s3_bucket:
        logging.error("S3_BUCKET is not set in the configuration.")
        return None
    
    s3_path = f'{session_id}/{missing_file}'

    try:
        blank_file_content = b''
        s3_client.put_object(Body=blank_file_content, Bucket=s3_bucket, Key=s3_path)
        logging.info(f"Blank file uploaded successfully to S3: {s3_path}")
        return s3_path
    except Exception as e:
        logging.error(f"Error uploading blank file to S3: {e}")
        return None

def download_file_from_s3_to_memory(s3_key, aws_access_key_id, aws_secret_access_key, aws_region, s3_bucket):
    s3_client = get_s3_client(aws_access_key_id, aws_secret_access_key, aws_region)
    try:
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        return response['Body'].read()
    except ClientError as e:
        logging.error(f"Error downloading file from S3: {e}")
        return None

def upload_bytes_to_s3(file_bytes, s3_key, aws_access_key_id, aws_secret_access_key, aws_region, s3_bucket):
    s3_client = get_s3_client(aws_access_key_id, aws_secret_access_key, aws_region)
    try:
        s3_client.put_object(Body=file_bytes, Bucket=s3_bucket, Key=s3_key)
        return True
    except ClientError as e:
        logging.error(f"Error uploading file to S3: {e}")
        return False
