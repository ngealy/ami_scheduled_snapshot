import boto3
import collections
import datetime

# Boto is the AWS SDK for Python
ec = boto3.client('ec2')

"""
This function looks at *all* ec2 instances's to find ones that have 
a "Backup" tag Key with a value of 'True'
It create an AMI of matching instances, and sets a DeleteOn tag according to the
Retention tag integer value (defaults to 7 days if not set)
Run only once per day.
"""

def lambda_handler(event, context):
    # get a list of information about reservations that match your filter
    # Only backup up those that have Backup: True/true
    reservations = ec.describe_instances(
        Filters = [
        {'Name': 'tag-key', 'Values': ['Backup']},
        {'Name': 'tag-value', 'Values': ['True', 'true']},
    ]
    ).get(
        'Reservations', []
    )

    # get the intances information from the reservations
    instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])

    print "Found %d instance(s) that need backing up" % len(instances)

    # create a dictionary with key, values where the default value is a list
    to_tag = collections.defaultdict(list)

    for instance in instances:
        # if the Retention flag isn't set, default to 7 days
        try:
            retention_days = [
                int(t.get('Value')) for t in instance['Tags']
                if t['Key'] == 'Retention'][0]
        except IndexError:
            retention_days = 7

        # date that ami was created
        create_time = datetime.datetime.today()
        # cast to string and replace : since ":" is an illegal character for naming AMIs
        create_time = str(create_time).replace(":", "-")

        # get the instance name and append the datetime to use as the AMI name in the next step
        instance_name = (item['Value'] for item in instance['Tags'] if item['Key'] == "Name").next()
        instance_desc = instance_name + " " + create_time

        # create the AMI image
        ami = ec.create_image(
            InstanceId=instance['InstanceId'],
            NoReboot=True,
            Name=instance_desc,
            Description=instance_desc,
        )

        # When each key is encountered for the first time, it is not already in the mapping; 
        # so an entry is automatically created using the default_factory function which returns 
        # an empty list. The list.append() operation then attaches the value to the new list. 
        # When keys are encountered again, the look-up proceeds normally (returning the list for that key) 
        # and the list.append() operation adds another value to the list.
        to_tag[retention_days].append(ami['ImageId'])

        print "Retaining AMI image %s of instance %s (%s) for %d days" % (
            ami['ImageId'],
            instance_name,
            instance['InstanceId'],
            retention_days,
        )

    # for each value of retention_days
    for retention_days in to_tag.keys():
        delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
        delete_fmt = delete_date.strftime('%Y-%m-%d')
        print "Tagging %d AMI images for deletion on %s" % (len(to_tag[retention_days]), delete_fmt)
        # tag ALL resources (this is done in one command) sharing a retention_days value 
        ec.create_tags(
            Resources=to_tag[retention_days],
            Tags=[
                {'Key': 'DeleteOn', 'Value': delete_fmt},
            ]
        )
