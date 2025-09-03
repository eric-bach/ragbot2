import os
from constructs import Construct
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_iam as iam,
    aws_ecr_assets as ecr_assets,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
    aws_lambda as lambda_,
    aws_s3_notifications as s3n,
    CfnOutput,
    Duration,
    RemovalPolicy,
)
from pathlib import Path
from .data_stack import DataStackResources
from dotenv import load_dotenv

class AppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, app_name: str, env_name: str, data_resources: DataStackResources, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load environment variables from .env file
        load_dotenv()
        
        # Get environment variables with fallbacks
        APP_NAME = app_name
        ENV_NAME = env_name
        AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
        CERTIFICATE_ARN = os.getenv('CERTIFICATE_ARN', '')
        BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', '')
        KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID', '')
        KNOWLEDGE_BASE_DATA_SOURCE_ID = os.getenv('KNOWLEDGE_BASE_DATA_SOURCE_ID', '')
        LINKUP_API_KEY = os.getenv('LINKUP_API_KEY', '')

        # Extract resources from data stack
        vpc = data_resources.vpc
        
        # Lookup S3 buckets by ARN
        knowledge_source_bucket = s3.Bucket.from_bucket_arn(
            self,
            "KnowledgeSourceBucket",
            bucket_arn=data_resources.knowledge_source_bucket_arn
        )
        sessions_bucket = s3.Bucket.from_bucket_arn(
            self,
            "SessionsBucket", 
            bucket_arn=data_resources.sessions_bucket_arn
        )

        #
        # AWS ACM
        #

        certificate = acm.Certificate.from_certificate_arn(
            self,
            "Certificate",
            certificate_arn=CERTIFICATE_ARN
        )

        #
        # AWS Lambda
        #

        # Create Lambda function for processing uploaded files
        sync_knowledge_base = lambda_.Function(
            self,
            "SyncKnowledgeBaseFunction",
            function_name=f"{APP_NAME}-sync-knowledge-base-{ENV_NAME}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="sync_knowledge_base.handler",
            code=lambda_.Code.from_asset(str(Path(__file__).parent.parent / "../backend/lambda/syncKnowledgeBase")),
            environment={
                'KNOWLEDGE_BASE_ID': KNOWLEDGE_BASE_ID,
                'KNOWLEDGE_BASE_DATA_SOURCE_ID': KNOWLEDGE_BASE_DATA_SOURCE_ID,
            },
            timeout=Duration.seconds(300),
            memory_size=512,
        )
        # Grant the Lambda function permissions to read from S3
        knowledge_source_bucket.grant_read(sync_knowledge_base)
        # Grant the Lambda function permissions to call Bedrock APIs
        sync_knowledge_base.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:StartIngestionJob",
                    "bedrock:GetIngestionJob",
                    "bedrock:ListIngestionJobs",
                    "bedrock:GetKnowledgeBase",
                    "bedrock:ListKnowledgeBases",
                ],
                resources=["*"],
            )
        )
        # Add S3 event notification to trigger Lambda when files are uploaded
        knowledge_source_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED_PUT,
            s3n.LambdaDestination(sync_knowledge_base),
            s3.NotificationKeyFilter(suffix='.pdf')
        )

        #
        # ALB Security Groups
        # 

        # ALB security group
        alb_sg = ec2.SecurityGroup(
            self,
            "ALBSG",
            vpc=vpc,
            description="Allow HTTP and HTTPS in",
            allow_all_outbound=True,
        )
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP in")
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow HTTPS in")

        # Create security group
        security_group = ec2.SecurityGroup(
            self,
            "ALBServiceSG",
            vpc=vpc,
            description="Only allow traffic from ALB",
            allow_all_outbound=True,
        )
      
        # Add ingress rule for port 8000
        # security_group.add_ingress_rule(
        #     peer=ec2.Peer.any_ipv4(),
        #     connection=ec2.Port.tcp(8000),
        #     description="Allow inbound traffic on port 8000"
        # )
        security_group.add_ingress_rule(
            alb_sg,
            ec2.Port.tcp(8000),
            "Allow ALB to reach ECS task"
        )

        #
        # AWS ECS Fargate
        #
        
        # Create an ECS cluster
        cluster = ecs.Cluster(
            self, 
            "ECSCluster",
            vpc=vpc,
        )
             
        # Create a task execution role
        execution_role = iam.Role(
            self, 
            "ECSTaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ],
        )
        
        # Create a task role with permissions to invoke Bedrock APIs
        task_role = iam.Role(
            self, 
            "ECSTaskRole",
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

        # Add S3 permissions for the task to generate presigned URLs and upload files
        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                ],
                resources=[
                    f"{knowledge_source_bucket.bucket_arn}/*",
                    f"{sessions_bucket.bucket_arn}/*",
                ],
            )
        )
        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:ListBucket"
                ],
                resources=[
                    f"{knowledge_source_bucket.bucket_arn}",
                    f"{sessions_bucket.bucket_arn}",
                ],
            )
        )

        # Create a task definition
        task_definition = ecs.FargateTaskDefinition(
            self, 
            "ECSTaskDefinition",
            memory_limit_mib=4096,
            cpu=1024,
            execution_role=execution_role,
            task_role=task_role,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
        )
 
        # This will use the Dockerfile in the docker directory
        chat_agent = ecr_assets.DockerImageAsset(
            self, 
            "ECSAgentImage",
            directory=str(Path(__file__).parent.parent / "../backend/agent"),
            file="Dockerfile",
            platform=ecr_assets.Platform.LINUX_ARM64,
        )
        
        # Create a log group for the container
        log_group = logs.LogGroup(
            self, 
            "ECSLogGroup",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )
 
        # Add container to the task definition
        task_definition.add_container(
            "ECSAgentContainer",
            image=ecs.ContainerImage.from_docker_image_asset(chat_agent),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="agent-service",
                log_group=log_group,
            ),
            environment={
                # Add any environment variables needed by your application
                "LOG_LEVEL": "INFO",
                "AWS_REGION": AWS_REGION,
                "BEDROCK_MODEL_ID": BEDROCK_MODEL_ID,
                "KNOWLEDGE_BASE_ID": KNOWLEDGE_BASE_ID,
                "KNOWLEDGE_BASE_DATA_SOURCE_ID": KNOWLEDGE_BASE_DATA_SOURCE_ID,
                "KNOWLEDGE_SOURCE_BUCKET_NAME": knowledge_source_bucket.bucket_name,
                "SESSIONS_BUCKET_NAME": sessions_bucket.bucket_name,
                "LINKUP_API_KEY": LINKUP_API_KEY,
            },
            port_mappings=[
                ecs.PortMapping(
                    container_port=8000,  # The port your application listens on
                    protocol=ecs.Protocol.TCP,
                ),
            ],
        )

        # Create a Fargate service
        service = ecs.FargateService(
            self,
            "ECSAgentService",
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

        #
        # AWS ALB
        #
        
        # Create a load balancer
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "ALB",
            vpc=vpc,
            internet_facing=True,
            security_group=alb_sg,
            load_balancer_name=f"{APP_NAME}-public",
        )

        # Create a target group first (before the listener)
        target_group = elbv2.ApplicationTargetGroup(
            self,
            'ALBECSTargets',
            port=8000,
            vpc=vpc,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[service],
            health_check=elbv2.HealthCheck(
                path='/health',
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                healthy_http_codes='200'
            ),
            deregistration_delay=Duration.seconds(30),
        )

        # Create HTTPS listener with Cognito authentication
        https_listener_https = alb.add_listener(
            "ALBHTTPSListener",
            port=443,
            certificates=[certificate],
            default_action=elbv2.ListenerAction.forward([target_group]),
            # default_action=actions.AuthenticateCognitoAction(
            #     user_pool=user_pool,
            #     user_pool_client=user_pool_client,
            #     user_pool_domain=user_pool_domain,
            #     next=elbv2.ListenerAction.forward([target_group])
            # )
        )

        # Create HTTP listener that redirects to HTTPS
        http_listener_http = alb.add_listener(
            "ALBHTTPListener",
            port=80,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True
            )
        )

        #
        # Amazon API Gateway
        #

        # # Create API Gateway that proxies to ALB
        # api = apigateway.RestApi(
        #     self,
        #     "AgentApi",
        #     rest_api_name="ragbot-agent-api",
        #     description="API Gateway for RAGBot Agent Service",
        #     default_cors_preflight_options=apigateway.CorsOptions(
        #         allow_origins=apigateway.Cors.ALL_ORIGINS,
        #         allow_methods=apigateway.Cors.ALL_METHODS,
        #         allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
        #     ),
        # )

        # # Integration for root path
        # root_integration = apigateway.Integration(
        #     type=apigateway.IntegrationType.HTTP_PROXY,
        #     integration_http_method="ANY",
        #     uri=f"http://{alb.load_balancer_dns_name}",
        #     options=apigateway.IntegrationOptions(
        #         connection_type=apigateway.ConnectionType.INTERNET,
        #     ),
        # )

        # # Integration for proxy paths (removes stage name)
        # proxy_integration = apigateway.Integration(
        #     type=apigateway.IntegrationType.HTTP_PROXY,
        #     integration_http_method="ANY",
        #     uri=f"http://{alb.load_balancer_dns_name}/{{proxy}}",
        #     options=apigateway.IntegrationOptions(
        #         connection_type=apigateway.ConnectionType.INTERNET,
        #         request_parameters={
        #             "integration.request.path.proxy": "method.request.path.proxy"
        #         }
        #     ),
        # )

        # # Add ANY method to root (handles /prod -> ALB/)
        # api.root.add_method(
        #     "ANY", 
        #     root_integration,
        #     request_parameters={
        #         "method.request.path.proxy": False
        #     }
        # )

        # # Add catch-all greedy proxy route for any sub-paths (handles /prod/debug -> ALB/debug)
        # catch_all = api.root.add_resource("{proxy+}")
        # catch_all.add_method(
        #     "ANY", 
        #     proxy_integration,
        #     request_parameters={
        #         "method.request.path.proxy": True
        #     }
        # )

        #
        # Outputs
        #

        # Output the ALB DNS name for manual DNS configuration in Cloudflare
        CfnOutput(
            self,
            "ALBDNSName",
            value=alb.load_balancer_dns_name,
            description="ALB DNS Name - Create CNAME record in Cloudflare: ragbot2-public.ericbach.dev -> this value",
            export_name=f"{APP_NAME}-ALB-DNS-name-{ENV_NAME}"
        )

 

        