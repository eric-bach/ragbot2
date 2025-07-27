import os
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_iam as iam,
    aws_ecr_assets as ecr_assets,
    aws_elasticloadbalancingv2 as elbv2,
    CfnOutput,
    Duration,
    RemovalPolicy,
)
from pathlib import Path
from constructs import Construct
from dotenv import load_dotenv

class Ragbot2Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load environment variables from .env file
        load_dotenv()
        
        # Get environment variables with fallbacks
        knowledge_base_id = os.getenv('KNOWLEDGE_BASE_ID', '')
        aws_region = os.getenv('AWS_REGION', 'us-east-1')
        linkup_api_key = os.getenv('LINKUP_API_KEY', '')

        bucket = s3.Bucket(
            self,
            "ragbot-source-bucket",
            bucket_name="ragbot-source-bucket"
        )

        # Create a VPC for our Fargate service
        vpc = ec2.Vpc(
            self, 
            "AgentVpc",
            max_azs=1,  # Use 1 Availability Zone to reduce costs
            nat_gateways=0,  # No NAT Gateway to save costs
        )

        # Create an ECS cluster
        cluster = ecs.Cluster(
            self, 
            "AgentCluster",
            vpc=vpc,
        )

        # Create a log group for the container
        log_group = logs.LogGroup(
            self, 
            "AgentServiceLogs",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )
             
        # Create a task execution role
        execution_role = iam.Role(
            self, 
            "AgentTaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ],
        )

        # Create a task role with permissions to invoke Bedrock APIs
        task_role = iam.Role(
            self, 
            "AgentTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        # Add permissions for the task to invoke Bedrock APIs
        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel", 
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:Retrieve",
                    "bedrock:RetrieveAndGenerate",
                    "bedrock:ListKnowledgeBases",
                    "bedrock:GetKnowledgeBase"],
                resources=["*"],
            )
        )
        
        # Create a task definition
        task_definition = ecs.FargateTaskDefinition(
            self, 
            "AgentTaskDefinition",
            memory_limit_mib=512,
            cpu=256,
            execution_role=execution_role,
            task_role=task_role,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
        )
 
        # This will use the Dockerfile in the docker directory
        docker_asset = ecr_assets.DockerImageAsset(
            self, 
            "AgentImage",
            directory=str(Path(__file__).parent.parent / "../src"),
            file="Dockerfile",
            platform=ecr_assets.Platform.LINUX_ARM64,
        )
 
        # Add container to the task definition
        task_definition.add_container(
            "AgentContainer",
            image=ecs.ContainerImage.from_docker_image_asset(docker_asset),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="agent-service",
                log_group=log_group,
            ),
            environment={
                # Add any environment variables needed by your application
                "LOG_LEVEL": "INFO",
                "AWS_REGION": aws_region,
                "KNOWLEDGE_BASE_ID": knowledge_base_id,
                "LINKUP_API_KEY": linkup_api_key
            },
            port_mappings=[
                ecs.PortMapping(
                    container_port=8000,  # The port your application listens on
                    protocol=ecs.Protocol.TCP,
                ),
            ],
        )
 
        # Create security group
        security_group = ec2.SecurityGroup(
            self, 
            "AgentServiceSG",
            vpc=vpc,
            description="Security group for Agent Fargate Service",
            allow_all_outbound=True,
        )
        
        # Add ingress rule for port 8000
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(8000),
            description="Allow inbound traffic on port 8000"
        )

        # Create a Fargate service
        service = ecs.FargateService(
            self, 
            "AgentService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,  # Run 1 instance to reduce costs
            assign_public_ip=True,  # Assign public IP to avoid needing NAT gateway
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            security_groups=[security_group],
            min_healthy_percent=0,
            max_healthy_percent=100,  # Allow up to 100% but minimum 0% for deployments
            health_check_grace_period=Duration.seconds(120),
        )
 
        # Output the service endpoint (you'll get the public IP from ECS console)
        CfnOutput(
            self,
            "AgentServiceEndpoint",
            value="Check ECS console for the public IP of the running task",
            description="The public IP of the Agent Service (check ECS console)",
        )