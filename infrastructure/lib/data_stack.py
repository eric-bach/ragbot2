from dataclasses import dataclass
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_cognito as cognito,
    aws_ec2 as ec2,
    CfnOutput,
    RemovalPolicy,
)
from constructs import Construct
from dotenv import load_dotenv

@dataclass
class DataStackResources:
    vpc: ec2.Vpc
    knowledge_source_bucket_arn: str
    sessions_bucket_arn: str

class DataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, app_name: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load environment variables from .env file
        load_dotenv()
        
        # Get environment variables with fallbacks
        APP_NAME = app_name
        ENV_NAME = env_name

        #
        # AWS VPC
        # 

        # Create a VPC for our Fargate service
        vpc = ec2.Vpc(
            self, 
            "VPC",
            vpc_name=f"{APP_NAME}-AgentVpc-{ENV_NAME}",
            max_azs=2,
            nat_gateways=0,         # No NAT Gateway to save costs
            #cidr="172.16.0.0/16",  # Use a different CIDR block to avoid conflicts
        )

        #
        # Amazon S3
        # 

        # Add S3 bucket for Strands Agent sessions
        sessions_bucket = s3.Bucket(
            self,
            "SessionsBucket",
            bucket_name=f"{APP_NAME}-sessions-{ENV_NAME}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True,
        )

        # Add S3 bucket for knowledge base source data
        knowledge_source_bucket = s3.Bucket(
            self,
            "KnowledgeBaseDataSourceBucket",
            bucket_name=f"{APP_NAME}-knowledge-source-{ENV_NAME}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True,
        )
        # Add CORS configuration to allow browser uploads
        knowledge_source_bucket.add_cors_rule(
            allowed_methods=[s3.HttpMethods.PUT],
            allowed_origins=["*"],  # In production, specify your domain
            allowed_headers=["*"],  # Allow all headers for presigned URL uploads
            exposed_headers=["ETag"],
            max_age=3000,
        )

        #
        # Amazon Bedrock Knowledge Bases
        # 

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

        #
        # Amazon Cognito
        #

        # Add Cognito User Pool for ALB authentication
        user_pool = cognito.UserPool(
            self,
            "AgentUserPool",
            user_pool_name=f"{APP_NAME}-users-{ENV_NAME}",
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            self_sign_up_enabled=True,
            user_verification=cognito.UserVerificationConfig(
                email_subject="Verify your email for RAGBot 2",
                email_body="Welcome to RAGBot 2! Your verification code is: {####}",
                email_style=cognito.VerificationEmailStyle.CODE,
            ),
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
            "UserPoolClient",
            user_pool_client_name=f"{APP_NAME}-user-client-{ENV_NAME}",
            user_pool=user_pool
        )

        # alb_user_pool_client = cognito.UserPoolClient(
        #     self,
        #     "AgentUserPoolClient",
        #     user_pool=user_pool,
        #     generate_secret=True,  # Required for ALB integration
        #     auth_flows=cognito.AuthFlow(user_password=True),
        #     o_auth=cognito.OAuthSettings(
        #         flows=cognito.OAuthFlows(authorization_code_grant=True),
        #         scopes=[
        #             cognito.OAuthScope.OPENID, # Required for ALB integration
        #             cognito.OAuthScope.EMAIL # Optional
        #         ],
        #         callback_urls=[f"https://{APP_NAME}-public.ericbach.dev/oauth2/idpresponse"],
        #     ),
        # )
        
        user_pool_domain = cognito.UserPoolDomain(
            self,
            "UserPoolDomain",
            user_pool=user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"{APP_NAME}"  # Must be globally unique
            ),
        )

        #
        # Outputs
        #

        CfnOutput(
            self,
            "SessionsBucketName",
            value=sessions_bucket.bucket_name,
            description=f"{APP_NAME} Sessions Bucket Name",
            export_name=f"{APP_NAME}-sessions-bucket-name"
        )

        CfnOutput(
            self,
            "KnowledgeSourceBucketName",
            value=knowledge_source_bucket.bucket_name,
            description=f"{APP_NAME} Knowledge Base Data Source Bucket Name",
            export_name=f"{APP_NAME}-knowledge-source-bucket-name"
        )

        CfnOutput(
            self,
            "CognitoUserPoolId",
            value=user_pool.user_pool_id,
            description=f"{APP_NAME} Cognito User Pool ID",
            export_name=f"{APP_NAME}-cognito-user-pool-id"
        )

        # Output the React App Client ID
        CfnOutput(
            self,
            "CognitoReactAppClientId",
            value=user_pool_client.user_pool_client_id,
            description=f"{APP_NAME} Cognito React App Client ID",
            export_name=f"{APP_NAME}-cognito-react-app-client-id"
        )

        # # Output the ALB App Client ID
        # CfnOutput(
        #     self,
        #     "CognitoALBAppClientId",
        #     value=alb_user_pool_client.user_pool_client_id,
        #     description="Cognito ALB App Client ID",
        #     export_name="Ragbot2CognitoALBAppClientId"
        # )

        #
        # Properties
        #

        self.resources = DataStackResources(
            vpc=vpc,
            knowledge_source_bucket_arn=knowledge_source_bucket.bucket_arn,
            sessions_bucket_arn=sessions_bucket.bucket_arn
        )