import boto3
import datetime

# Boto is the AWS SDK for Python
ec = boto3.client('ec2')

"""
This function looks at *all* AMI's that have a "DeleteOn" tag containing
the current day formatted as YYYY-MM-DD. It deletes matching AMIs and their 
backing EBS snapshots.  This function should be run at least daily.
"""

def lambda_handler(event, context):
    account_ids = list()
    
    # this is our aws account number
    account_ids.append("")

    # get today's date
    delete_on = datetime.date.today().strftime('%Y-%m-%d')
    
    # a filter for amis that have today's DeleteOn date tag
    filters = [
        {'Name': 'tag-key', 'Values': ['DeleteOn']},
        {'Name': 'tag-value', 'Values': [delete_on]},
    ]
    
    # get amis from our account that match the filter
    images = ec.describe_images(Owners=account_ids, Filters=filters)

    print "Found %d image(s) that need cleaned up" % len(images['Images'])

    # for each ami:
    #   deregister it
    #   and
    #   delete the associated ebs snapshots
    for ami in images['Images']:
        snap_ids = list()
        print "Getting info for \"%s\": %s" % (ami['Name'], ami['ImageId'])
        for dev in ami['BlockDeviceMappings']:
            if dev.get('Ebs', None) is None:
                continue
            snap_ids.append(dev['Ebs']['SnapshotId'])
        
        print "\tWill delete %s and %s" % (ami['ImageId'] ,snap_ids)    
                
        print "\tDeregistering AMI image %s" % ami['ImageId']
        ec.deregister_image(
            ImageId=ami['ImageId']
        )
        
        for snap_id in snap_ids:
            print "\tDeleting EBS snapshot %s" % snap_id
            ec.delete_snapshot(SnapshotId=snap_id)
            
