# API Gateway Integration with DLM Solution
Using this solution we can integrate the API gatway with Data Lifecycle Manager. This solution assumes that all the required roles are present in the respective accounts for creating DLM policy.
[ Assumes that the role is created with the name AWSDataLifecycleManagerServiceRole eg: arn:aws:iam::639015714993:role/AWSDataLifecycleManagerServiceRole ]
  ```sh
Note:
DLM policy lambada functions work only on python3.7 verion on AWS.
```
# serverless.yml
This serverless file is used to deploy the below lambda functions.
  - decider_function.py
  - dlm_offboarding.py
  - dlm_onboarding.py
  
decide_function.py: This intermediate lambda function will decide which lambda  needs  to trigger whether dlm_offboarding or dlm_onboarding according to the API gateway triggers.
dlm_onboarding.py: This lambda function is used to on board the DLM policy.
dlm_offboarding.py: This lambda function is used to off board the DLM policy.

The environment variables used in serverless files are given below.
- targetMgmtRole  - Used to provide the role for executing Lambda functions on the respective account.
- notifyConfig - Used to provide the notify_email configuration settings.
- emailSubject - Used to provide the email subject.
- logLevel - Used for log  level indication.
- retentionCount - Used to provide the retention count for the ebs volumes on DLM policy.
- schedulingTime - Used to provide the scheduling time for DLM policy.
- tag - Provide the boolean value for Copy tags property of the DLM.
- dlmKey - Used to provide the key name the for DLM policy.
- dlmInterval  - Used to provide DLM policy time interval use either .
- dlmTablename      -  Used to provide Status tracker dynamodb table name.
- awsRegion          - Used to provide AWS region.







   


    


