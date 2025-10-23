🗂️ AWS EC2 AMI Export & S3 Management Automation

Automates monthly AMI exports, moves older AMIs to Glacier, and sends email reports using AWS and Gmail. Logs activities in CloudWatch and notifies via SNS.

🚀 Features

🔹 Automatic AMI Export – Exports AMIs tagged as "Monthly" or "Pre/Post_Monthly" to S3.

🔹 Size Checks – Only AMIs smaller than 5000 GB are exported.

🔹 Email Reporting – Sends Gmail notifications for successful exports, deletions, and Glacier transfers.

🔹 CloudWatch Logging – Logs detailed progress, errors, and completion messages.

🔹 SNS Notifications – Notifies stakeholders about export status.

🔹 Bucket Management – Moves older AMIs to Glacier and deletes source AMIs automatically.

🔹 Snapshot Cleanup – Deregisters AMIs and deletes associated snapshots.

🛠️ Prerequisites

Python 3.10+

AWS IAM User with permissions for EC2, S3, SNS, CloudWatch Logs

Gmail credentials (OAuth) for sending emails

Python packages:

pip install boto3 pandas google-auth google-auth-oauthlib google-api-python-client requests openpyxl

⚙️ Setup Instructions

AWS Setup

Configure AWS credentials via environment or ~/.aws/credentials.

Create CloudWatch log group and SNS topic for notifications.

Create S3 buckets:

Source bucket: ami-backups-last-6months

Destination/Glacier bucket: ec2ami-backups

Gmail Setup

Download credentials.json from Google Cloud Console.

Ensure the Gmail account allows API sending.

The script will generate token.json for OAuth token.

Update Script Constants

aws_region = 'ap-south-1'
source_bucket_name = 'ami-backups-last-6months'
destination_bucket = 'ec2ami-backups'
sns_topic_arn = 'YOUR_SNS_TOPIC_ARN'
log_group_name = 'YOUR_CLOUDWATCH_LOG_GROUP'

📄 How It Works

Fetch all AMI details owned by your account.

Filter monthly AMIs and compute size.

Export eligible AMIs to S3, logging progress in CloudWatch.

Send Gmail reports for:

Monthly AMI list

Successfully exported AMIs

AMIs moved to Glacier

Delete exported AMIs and snapshots.

Move AMIs older than 6 months to Glacier bucket and clean source bucket.

Send final SNS and CloudWatch logs indicating completion.

📂 File Structure
.
├── ami_export.py            # Main automation script
├── credentials.json         # Gmail OAuth credentials
├── token.json               # Gmail token (auto-generated)
├── README.md                # Documentation
└── requirements.txt         # Python dependencies

✨ Sample Workflow Diagram
[Fetch AMIs] ---> [Filter Monthly AMIs] ---> [Check Size <5000GB] ---> [Export to S3] 
        |                                         |
        v                                         v
  [Send Email Report]                     [Log in CloudWatch / SNS]
        |
        v
  [Move >6 months old AMIs to Glacier] ---> [Delete Source AMIs & Snapshots] ---> [Send Email Report]

📧 Email Notifications

Sent via Gmail API.

Reports include:

AMI ID, Name, Creation Date

Size before and after export

S3 path

URLs (pre-signed links)

⚠️ Notes

The script handles retries for export tasks.

Logs are grouped by current date in CloudWatch.

Errors trigger SNS alerts and logs.

Ensure all AWS IAM policies are correct for EC2, S3, SNS, and CloudWatch.

📸 Screenshots
<img width="1920" height="913" alt="s3" src="https://github.com/user-attachments/assets/4e3d858f-f811-4c3c-9b85-2b63a4004386" />


🧑‍💻 Author

Nipun Yadav 💼 DevOps & Cloud Engineer
🌐 [LinkedIn](https://www.linkedin.com/in/nipun-yadav-5bb736178/) | [GitHub](https://github.com/Nyadav123)
