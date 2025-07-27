from aws_cdk import (
    Stack,
    aws_s3 as s3,
    Duration,
)
from constructs import Construct

class Ragbot2Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self,
            "ragbot-source-bucket",
            bucket_name="ragbot-source-bucket",
            default_storage_class=s3.StorageClass.ONE_ZONE_IA
        )
            
