# ami_scheduled_snapshot

## ami_scheduled_snapshots
This function looks at *all* ec2 instances to find ones that have a "Backup" tag Key with a value of 'True'.
It create an AMI of matching instances, and sets a DeleteOn tag according to the Retention tag integer value (defaults to 7 days if not set)

## ami_scheduled_snapshot_expiration_worker
This function looks at *all* AMI's that have a "DeleteOn" tag containing the current day formatted as YYYY-MM-DD. It deletes matching AMIs and their backing EBS snapshots. This function should be run at least daily.

## How do I backup my AMI
Add tag(s) to the EC2 instance
| Key | Value |
| Backup | "True" or "true" will backup the AMI nightly. |
| Retention | Any n integer value will mark the AMI to be deleted after n days. It defaults to 7 days. |
