''' Module to send run command output to s3 bucket '''
# pylint: skip-file
import time

import boto3

CUSTOMER_DEFAULT_REGION = 'us-east-1'
PATCH_SCAN_BUCKET_NAME = 'rean-ms-ssm-patchscan-outputs-windows'
DYNAMODB_TABLE_NAME = 'rean-ms-ssm-patchscan-and-metadata-windows'
CSV_REPORT_LAMBDA_NAME = 'rean-ms-ssm-dynamodb-to-csv-report-windows'
CUSTOMER_CROSS_ACCOUNT_ROLE_ARN = 'dddddddddd'


def caAssumeConn(connectionType, service):
    ''' function to assume role '''
    stsClient = boto3.client('sts', CUSTOMER_DEFAULT_REGION)
    caAssumeRole = stsClient.assume_role(
        RoleArn=CUSTOMER_CROSS_ACCOUNT_ROLE_ARN, RoleSessionName=service)
    if connectionType == 'resource':
        connection = boto3.resource(service, aws_access_key_id=caAssumeRole['Credentials']['AccessKeyId'], aws_secret_access_key=caAssumeRole['Credentials']
                                    ['SecretAccessKey'], aws_session_token=caAssumeRole['Credentials']['SessionToken'], region_name=CUSTOMER_DEFAULT_REGION)
    elif connectionType == 'client':
        connection = boto3.client(service, aws_access_key_id=caAssumeRole['Credentials']['AccessKeyId'], aws_secret_access_key=caAssumeRole['Credentials']
                                  ['SecretAccessKey'], aws_session_token=caAssumeRole['Credentials']['SessionToken'], region_name=CUSTOMER_DEFAULT_REGION)
    return connection


def dynamodbTableCleanup(tableName):
    ''' function to cleanup processed data in dynamodb '''
    dynamodbClient = boto3.client('dynamodb', 'us-east-1')
    response = dynamodbClient.scan(TableName=tableName)
    for i in response['Items']:
        instanceId = i['InstanceID']
        dynamodbClient.delete_item(
            TableName=tableName,
            Key={'InstanceID': instanceId})


def lambdaHandler(event, context):
    ''' Handler function'''
    dynamodbTableCleanup(DYNAMODB_TABLE_NAME)
    ec2ForSsmScan = []
    runningEc2Windows = caAssumeConn('resource', 'ec2').instances.filter(
        Filters=[{'Name': 'platform', 'Values': ['windows']}, {'Name': 'instance-state-name', 'Values': ['running']}])
    # Filter Instance IDs for the Instances online under SSM.
    for instance in runningEc2Windows:
        try:
            ssmResponse = caAssumeConn('client', 'ssm').describe_instance_information(
                InstanceInformationFilterList=[{'key': 'InstanceIds', 'valueSet': [instance.id]}])
            if (ssmResponse['InstanceInformationList'][0]['PingStatus']) == 'Online':
                ec2ForSsmScan.append(instance.id)
        except Exception as error:
            print("The Exception for the error:\n" + str(error))

    # Send command to each fleet of 50 instances
    print(len(ec2ForSsmScan))
    ssmRunCommandIds = {}
    for i in range(0, len(ec2ForSsmScan), 50):
        ec2Batch = ec2ForSsmScan[i:i + 50]
        runCommandResponse = caAssumeConn('client', 'ssm').send_command(
            Targets=[{'Key': 'instanceids', 'Values': ec2Batch}, ],
            DocumentName='AWS-FindWindowsUpdates',
            OutputS3BucketName=PATCH_SCAN_BUCKET_NAME)
        runCommandId = (runCommandResponse['Command']['CommandId'])
        print(runCommandId)
        ssmRunCommandIds[runCommandId] = ec2Batch

    # Keep checking the status until all the instances have changed the status from 'InProgress'
    while ssmRunCommandIds:
        emptyKeys = []
        for command in ssmRunCommandIds:
            for instanceid in ssmRunCommandIds[command]:
                response = caAssumeConn('client', 'ssm').list_command_invocations(
                    CommandId=command, InstanceId=instanceid)
                status = response['CommandInvocations'][0]['StatusDetails']
                if status != 'InProgress':
                    ssmRunCommandIds[command].remove(instanceid)

            # Find out the empty command ids
            if not ssmRunCommandIds[command]:
                emptyKeys.append(command)

        # Delete the empty commands
        for cmd in emptyKeys:
            ssmRunCommandIds.pop(cmd)

    # Call the CSV generating Lambda now
    time.sleep(60)
    lambdaClient = boto3.client('lambda', 'us-east-1')
    invokeResponse = lambdaClient.invoke(
        FunctionName=CSV_REPORT_LAMBDA_NAME, InvocationType='Event')
    print(invokeResponse)


if __name__ == '__main__':
    lambdaHandler(None, None)