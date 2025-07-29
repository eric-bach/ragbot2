import os
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_bedrock as bedrock,
    aws_cognito as cognito,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_iam as iam,
    aws_ecr_assets as ecr_assets,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_actions as actions,
    aws_certificatemanager as acm,
    aws_apigateway as apigateway,
    aws_route53 as route53,
    aws_route53_targets as targets,
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
        certificate_arn = os.getenv('CERTIFICATE_ARN', '')

        # Add S3 bucket for source data
        bucket = s3.Bucket(
            self,
            "ragbot-source-bucket",
            bucket_name=f"ragbot-source-bucket-{self.account}-{self.region}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True,
        )

        # # TODO Add Knowledge Bases with Vector S3 (when supported in CloudFormation)
        # bedrock_role = iam.Role(
        #     self,
        #     "bedrock-role",
        #     assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
        #     managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")]
        # )

        # # Add S3 permissions for the specific buckets
        # bedrock_role.add_to_policy(
        #     iam.PolicyStatement(
        #         actions=[
        #             "s3:GetObject",
        #             "s3:PutObject",
        #             "s3:DeleteObject",
        #             "s3:ListBucket"
        #         ],
        #         resources=[
        #             f"{bucket.bucket_arn}",
        #             f"{bucket.bucket_arn}/*",
        #         ]
        #     )
        # )
        
        # knowledge_base = bedrock.CfnKnowledgeBase(
        #     self,
        #     "ragbot-knowledge-base",
        #     name="ragbot-knowledge-base",
        #     description="RAGBot Knowledge Base",
        #     knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
        #         type="VECTOR",
        #         vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
        #             embedding_model_arn="arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v2:0"
        #         )
        #     ),
        #     role_arn=bedrock_role.role_arn,
        #     storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
        #         type="VECTOR",
        #         s3_configuration=bedrock.CfnKnowledgeBase.S3ConfigurationProperty(
        #             # TODO S3 is not supported for Vector Knowledge Base in CloudFormation yet    
        #         )
        #     )
        # )

        # Create a VPC for our Fargate service
        vpc = ec2.Vpc(
            self, 
            "AgentVpc",
            max_azs=2,
            nat_gateways=0,  # No NAT Gateway to save costs
            #cidr="172.16.0.0/16",  # Use a different CIDR block to avoid conflicts
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
            directory=str(Path(__file__).parent.parent / "../backend/aws"),
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
 
        # ALB security group
        alb_sg = ec2.SecurityGroup(
            self, "ALBSG",
            vpc=vpc,
            description="Allow HTTP and HTTPS in",
            allow_all_outbound=True,
        )
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP in")
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow HTTPS in")

        # Create security group
        security_group = ec2.SecurityGroup(
            self, 
            "AgentServiceSG",
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

        # Create a load balancer
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "AgentALB",
            vpc=vpc,
            internet_facing=True,
            security_group=alb_sg,
            load_balancer_name="agent-alb",
        )
    
        certificate = acm.Certificate.from_certificate_arn(
            self,
            "AgentCertificate",
            certificate_arn=certificate_arn
        )

        # Add Cognito User Pool for ALB authentication
        user_pool = cognito.UserPool(
            self,
            "AgentUserPool",
            user_pool_name="ragbot-users",
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        user_pool_client = cognito.UserPoolClient(
            self,
            "AgentUserPoolClient",
            user_pool=user_pool,
            generate_secret=True,  # Required for ALB integration
            auth_flows=cognito.AuthFlow(user_password=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[
                    cognito.OAuthScope.OPENID, # Required for ALB integration
                    cognito.OAuthScope.EMAIL # Optional
                ],
                #callback_urls=[f"https://{alb.load_balancer_dns_name}/oauth2/idpresponse"],
                callback_urls=["https://ragbot2.ericbach.dev/oauth2/idpresponse"],
            ),
        )
        
        user_pool_domain = cognito.UserPoolDomain(
            self,
            "AgentUserPoolDomain",
            user_pool=user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix="ragbot2"  # Must be globally unique
            ),
        )

        # Create a target group first (before the listener)
        target_group = elbv2.ApplicationTargetGroup(
            self,
            'AgentTargets',
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
            "AgentHTTPSListener",
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
            "AgentHTTPListener",
            port=80,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True
            )
        )

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

        # Lookup the existing hosted zone
        hosted_zone = route53.HostedZone.from_lookup(
            self,
            "HostedZone",
            domain_name="ericbach.dev"
        )

        # Create an alias record pointing to the ALB
        route53.ARecord(
            self,
            "ALBAliasRecord",
            zone=hosted_zone,
            record_name="ragbot2",  # This creates ragbot.ericbach.dev
            target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(alb)),
            comment="Alias record for RAGBot ALB"
        )