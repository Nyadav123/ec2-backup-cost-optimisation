import boto3
from datetime import datetime, timedelta, date
import pandas as pd
import os
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import time
from requests import HTTPError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ============================
# AWS REGION AND CLIENTS SETUP
# ============================
aws_region = 'ap-south-1'

ec2_client = boto3.client('ec2', region_name=aws_region)
s3_client = boto3.client('s3', region_name=aws_region)
s3_resource_ = boto3.resource('s3', region_name=aws_region)
cloudwatch_client = boto3.client('cloudwatch', region_name=aws_region)
cloudwatch_logs_client = boto3.client('logs', region_name=aws_region)
sns_client = boto3.client('sns', region_name=aws_region)

# Remove sensitive details
sns_topic_arn = ''  # Add your SNS topic ARN here
log_group_name = ''  # Add your CloudWatch log group name here
source_bucket_name = ''  # Add your S3 source bucket name here
destination_bucket = ''  # Add your S3 destination bucket name here

# Lists to store results
final_check = []
final_check2 = []
success_copy_to_s3_bukcet = []

# ========================================
# FUNCTION TO CREATE OR GET CLOUDWATCH LOG STREAM
# ========================================
def get_log_stream_name():
    """Get or create a CloudWatch log stream for the current date."""
    current_date = datetime.now().strftime('%Y-%m-%d')
    response = cloudwatch_logs_client.describe_log_streams(
        logGroupName=log_group_name,
        logStreamNamePrefix=current_date
    )
    log_streams = response.get('logStreams', [])
    if not log_streams:
        cloudwatch_logs_client.create_log_stream(
            logGroupName=log_group_name,
            logStreamName=current_date
        )
    else:
        return log_streams[0]['logStreamName']
    return current_date

# ============================
# GMAIL AUTHENTICATION
# ============================
def gmail_authentication():
    """Authenticate Gmail API using OAuth2."""
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    creds = None
    token_file = 'token.json'
    try:
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server()
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f'Google authentication failed: {e}')

# ============================
# EMAIL TRIGGER FUNCTION
# ============================
def email_trigger(mail_content, mail_subject, file_name):
    """Send an email with attachment using Gmail API."""
    try:
        receiver_address = ['example1@email.com', 'example2@email.com']  # Replace with your recipients
        service = gmail_authentication()
        message = MIMEMultipart()
        message['To'] = ','.join(receiver_address)
        message['from'] = 'automated@example.com'  # Replace with your sender
        message['Subject'] = mail_subject

        # Attach file
        with open(file_name, 'rb') as attach_file:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attach_file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={file_name}')
            message.attach(part)

        # Attach body
        message.attach(MIMEText(mail_content, 'plain'))

        create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        service.users().messages().send(userId="me", body=create_message).execute()
        print(f'{file_name} MAIL SENT')

    except HTTPError as error:
        print(f'Mail send failed: {error}')

# ============================
# FETCH AMI DETAILS
# ============================
responses___ = ec2_client.describe_images(Owners=['self'])  # Fetch all AMIs for account

today_ = date.today()
first_day_current_month = today_.replace(day=1)
last_month = first_day_current_month - timedelta(days=1)
crnt_month_year = last_month.strftime("%B-%Y")

# ============================
# FILTER MONTHLY AMIs
# ============================
ami_details_1 = []
all_ami_size_1 = 0

for image in responses___['Images']:
    ami_id = image['ImageId']
    ami_name = image['Name']
    ami_creation_date_utc = datetime.strptime(image['CreationDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
    instance_name = ""
    monthly_backup_check = ""

    # Extract tags
    if 'Tags' in image:
        for tag in image['Tags']:
            if tag['Key'] == 'Name':
                instance_name = tag['Value']
            if tag['Key'] == 'Backup Type':
                monthly_backup_check = tag['Value']

    if monthly_backup_check.lower() in ['monthly', 'pre/post_monthly']:
        # Calculate total AMI size
        block_device_mappings = ec2_client.describe_images(ImageIds=[ami_id])['Images'][0]['BlockDeviceMappings']
        total_size = sum([mapping.get('Ebs', {}).get('VolumeSize', 0) for mapping in block_device_mappings])
        if total_size < 5000:  # Skip very large AMIs
            ami_details_1.append({
                "Instance Name": instance_name,
                "AMI ID": ami_id,
                "AMI Name": ami_name,
                "AMI Creation date": ami_creation_date_utc,
                "AMI Size": total_size
            })
            all_ami_size_1 += total_size

# ============================
# EXPORT AMI REPORT TO EXCEL AND SEND EMAIL
# ============================
df__1 = pd.DataFrame(ami_details_1)
file_name_list_monthly = 'ami_list.xlsx'
df__1.to_excel(file_name_list_monthly, sheet_name='AMI_IDs', index=False)

mail_content1 = f'''Hi All,
Please refer the attached report of all the last month monthly AMI
and the total size of all the last month AMI's is {all_ami_size_1} GB
All the above AMI now starts to export into S3 bucket.'''
mail_subject1 = 'List of all last month monthly AMI'
email_trigger(mail_content1, mail_subject1, file_name_list_monthly)

# ============================
# FUNCTIONS TO PROCESS S3 OBJECTS
# ============================
def copy_Bucket(copy_source, object_key):
    """Copy an S3 object to another bucket."""
    check_res = s3_resource_.meta.client.copy(copy_source, destination_bucket, object_key)
    return 0

def delete_amis(to_delete, bucket_name):
    """Delete AMIs from S3 bucket."""
    for object_key in to_delete:
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        delete_message = f"{object_key} has been successfully deleted from {bucket_name}"
        print(delete_message)
        log_stream_name = get_log_stream_name()
        cloudwatch_logs_client.put_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            logEvents=[{'timestamp': int(time.time() * 1000), 'message': delete_message}]
        )

def process_s3_objects(bucket_name, filter_date=None, copy_to_bucket=None):
    """Process S3 objects: list, filter by month, copy or delete."""
    list_ami = []
    list_copy_ami = []
    paginator = s3_client.get_paginator('list_objects_v2')
    for response in paginator.paginate(Bucket=bucket_name):
        if 'Contents' in response:
            for obj in response['Contents']:
                object_key = obj['Key']
                object_size = float(obj['Size'] / 1073741824)
                url_ = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_key}, ExpiresIn=3600)
                ami_id = object_key.split("/")[-1].split(".")[0]
                instance_name = object_key.split("/")[0]
                creat_month = object_key.split("/")[1]

                if filter_date and creat_month == filter_date:
                    if copy_to_bucket is None:
                        list_ami.append({
                            "Instance name": instance_name,
                            "AMI ID": ami_id,
                            "AMI creation Month": creat_month,
                            "Object Size": object_size,
                            "Object Key": object_key,
                            "URL": url_
                        })
                    else:
                        copy_source = {'Bucket': bucket_name, 'Key': object_key}
                        copy_Bucket(copy_source, object_key)
                        success_copy_to_s3_bukcet.append(object_key)
                        print(f'Copied {object_key} from {bucket_name} to {copy_to_bucket}')

    return list_ami if copy_to_bucket is None else list_copy_ami

# ============================
# PROCESS CURRENT MONTH AND SIX-MONTH OLD AMIs
# ============================
# Example: Process last month AMI list
last_months_ago_str = last_month.strftime("%B-%Y")
six_months_ago = first_day_current_month - timedelta(days=31*6)
six_months_ago_str = six_months_ago.strftime("%B-%Y")

# Process last month
list_current_month_ami = process_s3_objects(source_bucket_name, filter_date=last_months_ago_str)
df_current_month = pd.DataFrame(list_current_month_ami)
df_current_month.to_excel('Ami_copy_to_s3_list.xlsx', sheet_name='AMI_IDs', index=False)

# Process last 6 months old AMIs
process_s3_objects(source_bucket_name, filter_date=six_months_ago_str, copy_to_bucket=destination_bucket)

# ============================
# FINAL SUCCESS MESSAGE
# ============================
success_full = "The monthly whole process has been completed"
print(success_full)
sns_client.publish(
    TopicArn=sns_topic_arn,
    Subject='The AMI export process has been completed',
    Message=success_full
)
