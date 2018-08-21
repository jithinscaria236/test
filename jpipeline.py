import boto3
import time
import os
import sys

customer_default_region = sys.argv[1]
patch_scan_bucket_name = sys.argv[2]
dynamodb_table_name = sys.argv[3]
csv_report_lambda_name = sys.argv[4]
customer_cross_account_role_arn = sys.argv[5]
dynamodb_client = boto3.client('dynamodb', 'us-east-1')

def ca_assume_conn(type, service):
    sts_client = boto3.client('sts', customer_default_region)
    ca_assume_role = sts_client.assume_role(
        RoleArn=customer_cross_account_role_arn, RoleSessionName=service)
    if type == 'resource':
        connection = boto3.resource(service, aws_access_key_id=ca_assume_role['Credentials']['AccessKeyId'], aws_secret_access_key=ca_assume_role['Credentials']
                                    ['SecretAccessKey'], aws_session_token=ca_assume_role['Credentials']['SessionToken'], region_name=customer_default_region)
    elif type == 'client':
        connection = boto3.client(service, aws_access_key_id=ca_assume_role['Credentials']['AccessKeyId'], aws_secret_access_key=ca_assume_role['Credentials']
                                  ['SecretAccessKey'], aws_session_token=ca_assume_role['Credentials']['SessionToken'], region_name=customer_default_region)
    return connection


def dynamodb_table_cleanup(table_name):
    response = dynamodb_client.scan(TableName=table_name)
    for i in response['Items']:
        instance_id = i['InstanceID']
        dynamodb_client.delete_item(TableName=table_name,Key= {'InstanceID': instance_id})


def lambda_handler(event, context):
    dynamodb_table_cleanup(dynamodb_table_name)
    ec2_for_ssm_scan = []
    running_ec2_windows = ca_assume_conn('resource', 'ec2').instances.filter(
        Filters=[{'Name': 'platform', 'Values': ['windows']}, {'Name': 'instance-state-name', 'Values': ['running']}])
    # Filter Instance IDs for the Instances online under SSM.
    for instance in running_ec2_windows:
        try:
            ssm_response = ca_assume_conn('client', 'ssm').describe_instance_information(
                InstanceInformationFilterList=[{'key': 'InstanceIds', 'valueSet': [instance.id]}])
            if (ssm_response['InstanceInformationList'][0]['PingStatus']) == 'Online':
                ec2_for_ssm_scan.append(instance.id)
        except Exception as e:
            print("The Exception for the error:\n" + str(e))

    # Send command to each fleet of 50 instances
    print(len(ec2_for_ssm_scan))
    ssm_run_command_ids = {}
    for i in range(0, len(ec2_for_ssm_scan), 50):
        ec2_batch = ec2_for_ssm_scan[i:i+50]
        run_command_response = ca_assume_conn('client', 'ssm').send_command(Targets=[{'Key': 'instanceids', 'Values': ec2_batch}, ],
                                                                            DocumentName='AWS-FindWindowsUpdates', OutputS3BucketName=patch_scan_bucket_name)
        run_command_id = (run_command_response['Command']['CommandId'])
        print(run_command_id)
        ssm_run_command_ids[run_command_id] = ec2_batch

    # Keep checking the status until all the instances have changed the status from 'InProgress'
    while ssm_run_command_ids:
        empty_keys = []
        for command in ssm_run_command_ids.keys():
            for instanceid in ssm_run_command_ids[command]:
                response = ca_assume_conn('client', 'ssm').list_command_invocations(
                    CommandId=command, InstanceId=instanceid)
                status = response['CommandInvocations'][0]['StatusDetails']
                if status != 'InProgress':
                    ssm_run_command_ids[command].remove(instanceid)

            # Find out the empty command ids
            if not ssm_run_command_ids[command]:
                empty_keys.append(command)

        # Delete the empty commands
        for cmd in empty_keys:
            ssm_run_command_ids.pop(cmd)

    # Call the CSV generating Lambda now
    time.sleep(60)
    lambda_client = boto3.client('lambda', 'us-east-1')
    invoke_response = lambda_client.invoke(FunctionName=csv_report_lambda_name, InvocationType='Event')
    print(invoke_response)


if __name__ == '__main__':
    lambda_handler(None, None)