
List all running notebook instances in dev

```sh
aws sagemaker list-notebook-instances --region ap-southeast-2
```


```json
{
    "NotebookInstances": [
        {
            "NotebookInstanceName": "digital-elevation-model",
            "NotebookInstanceArn": "arn:aws:sagemaker:ap-southeast-2:948263829143:notebook-instance/digital-elevation-model",
            "NotebookInstanceStatus": "InService",
            "Url": "digital-elevation-model.notebook.ap-southeast-2.sagemaker.aws",
            "InstanceType": "ml.t3.medium",
            "CreationTime": "2024-02-06T15:10:56.074000+11:00",
            "LastModifiedTime": "2024-02-06T15:14:52.753000+11:00"
        }
    ]
}
```

stop notebook instance

```sh
aws sagemaker stop-notebook-instance --notebook-instance-name digital-elevation-model --region ap-southeast-2
```

describe the instance

```sh
aws sagemaker describe-notebook-instance --notebook-instance-name digital-elevation-model --region ap-southeast-2
```


```json
{
    "NotebookInstanceArn": "arn:aws:sagemaker:ap-southeast-2:948263829143:notebook-instance/digital-elevation-model",
    "NotebookInstanceName": "digital-elevation-model",
    "NotebookInstanceStatus": "InService",
    "Url": "digital-elevation-model.notebook.ap-southeast-2.sagemaker.aws",
    "InstanceType": "ml.t3.medium",
    "SubnetId": "subnet-0a14dc64cff041487",
    "SecurityGroups": [
        "sg-02cb1c5f615500d5a"
    ],
    "RoleArn": "arn:aws:iam::948263829143:role/sagemaker-execution-test",
    "NetworkInterfaceId": "eni-02f62b425354b6fa2",
    "LastModifiedTime": "2024-02-07T11:06:59.367000+11:00",
    "CreationTime": "2024-02-06T15:10:56.074000+11:00",
    "DirectInternetAccess": "Enabled",
    "VolumeSizeInGB": 5,
    "RootAccess": "Enabled",
    "PlatformIdentifier": "notebook-al2-v2",
    "InstanceMetadataServiceConfiguration": {
        "MinimumInstanceMetadataServiceVersion": "2"
    }
}
```
