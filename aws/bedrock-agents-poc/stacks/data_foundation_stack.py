from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    CfnOutput,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3d,
    aws_glue as glue,
    aws_athena as athena,
)
from cdk_nag import NagPackSuppression, NagSuppressions
from constructs import Construct
import hashlib


class DataFoundationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a unique string to create unique resource names
        hash_base_string = self.account + self.region
        hash_base_string = hash_base_string.encode("utf8")

        ### 1. Create data-set resources

        # Create S3 bucket for the data set
        data_bucket = s3.Bucket(
            self,
            "DataLake",
            bucket_name=(
                "data-bucket-" + str(hashlib.sha384(hash_base_string).hexdigest())[:15]
            ).lower(),
            auto_delete_objects=True,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            intelligent_tiering_configurations=[
                s3.IntelligentTieringConfiguration(
                    name="my_s3_tiering",
                    archive_access_tier_time=Duration.days(90),
                    deep_archive_access_tier_time=Duration.days(180),
                    prefix="prefix",
                    tags=[s3.Tag(key="key", value="value")],
                )
            ],
            lifecycle_rules=[s3.LifecycleRule(noncurrent_version_expiration=Duration.days(7))],
        )

        # Create S3 bucket policy for bedrock permissions
        add_s3_policy = data_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject", "s3:PutObject", "s3:AbortMultipartUpload"],
                resources=[data_bucket.arn_for_objects("*")],
                principals=[iam.ServicePrincipal("bedrock.amazonaws.com")],
            )
        )

        NagSuppressions.add_resource_suppressions(
            data_bucket,
            [
                NagPackSuppression(
                    id="AwsSolutions-S1",
                    reason="The bucket is not for production and should not require debug.",
                )
            ],
            True,
        )

        # Upload a sample data-sest from asset to S3 bucket - with the prefix for incoming "raw" data
        s3d.BucketDeployment(
            self,
            "DataDeployment",
            sources=[s3d.Source.asset("assets/data-set/")],
            destination_bucket=data_bucket,
            destination_key_prefix="data-set/",
        )

        # Export the data set bucket name
        CfnOutput(
            self,
            "DataSetBucketName",
            value=data_bucket.bucket_name,
            export_name="DataSetBucketName",
        )

        ### 2. Create glue resources

        # Create Glue Service Role
        glue_service_role = iam.Role(
            self,
            "GlueServiceRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")
            ],
        )

        # Create Glue Database
        glue_database_name = "data_set_db"

        glue.CfnDatabase(
            self,
            "DataSetDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(name=glue_database_name),
        )

        # Create Glue role for the etl job
        glue_job_role = iam.Role(
            self,
            "GlueEtlJobRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
            ],
        )

        # Grant read and write access to the data bucket
        data_bucket.grant_read_write(glue_job_role)

        # Upload glue etl script from asset to S3 bucket. The script will be used by the Glue etl job, creates compressed parquet files, creates a schema, and creates a glue db table partitions
        s3d.BucketDeployment(
            self,
            "GlueJobScript",
            sources=[s3d.Source.asset("assets/glue/")],
            destination_bucket=data_bucket,
            destination_key_prefix="scripts/",
        )

        # Create a Glue etl job that processes the data set
        etl_job = glue.CfnJob(
            self,
            "DataSetETLJob",
            role=glue_job_role.role_arn,
            execution_class="FLEX",
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                script_location="s3://{}/scripts/etl.py".format(data_bucket.bucket_name),
                python_version="3",
            ),
            default_arguments={
                "--job-bookmark-option": "job-bookmark-enable",
                "--enable-metrics": "true",
                "--enable-observability-metrics": "true",
                "--enable-continuous-cloudwatch-log": "true",
                "--customer-driver-env-vars": f"CUSTOMER_BUCKET_NAME={data_bucket.bucket_name}",
                "--customer-executor-env-vars": f"CUSTOMER_BUCKET_NAME={data_bucket.bucket_name}",
            },
            glue_version="4.0",
            max_retries=0,
            number_of_workers=2,
            worker_type="G.1X",
        )

        # Create a Glue schedule for the etl job that processes the data set with the bookmark option enabled
        glue_schedule = glue.CfnTrigger(
            self,
            "DataSetETLSchedule",
            name="DataSetETLSchedule",
            description="Schedule for the DataSetETLJob to discover and process incoming data",
            type="SCHEDULED",
            start_on_creation=True,
            actions=[
                glue.CfnTrigger.ActionProperty(
                    job_name=etl_job.ref,
                    arguments={
                        "--job-bookmark-option": "job-bookmark-enable",
                        "--enable-metrics": "true",
                        "--enable-observability-metrics": "true",
                        "--enable-continuous-cloudwatch-log": "true",
                        "--customer-driver-env-vars": f"CUSTOMER_BUCKET_NAME={data_bucket.bucket_name}",
                        "--customer-executor-env-vars": f"CUSTOMER_BUCKET_NAME={data_bucket.bucket_name}",
                    },
                )
            ],
            schedule="cron(0 1 * * ? *)",  # Run once a day at 1am
        )

        ### 3. Create Athena resources

        # Create S3 athena destination bucket
        athena_bucket = s3.Bucket(
            self,
            "AthenaDestination",
            bucket_name=(
                "athena-destination-" + str(hashlib.sha384(hash_base_string).hexdigest())[:15]
            ).lower(),
            auto_delete_objects=True,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            intelligent_tiering_configurations=[
                s3.IntelligentTieringConfiguration(
                    name="my_s3_tiering",
                    archive_access_tier_time=Duration.days(90),
                    deep_archive_access_tier_time=Duration.days(180),
                    prefix="prefix",
                    tags=[s3.Tag(key="key", value="value")],
                )
            ],
            lifecycle_rules=[s3.LifecycleRule(noncurrent_version_expiration=Duration.days(7))],
        )

        athena_bucket.grant_read_write(iam.ServicePrincipal("athena.amazonaws.com"))

        # Export the athena destination bucket name
        CfnOutput(
            self,
            "AthenaDestBucketName",
            value=athena_bucket.bucket_name,
            export_name="AthenaDestinationBucketName",
        )

        # Set the query result location for Athena
        athena_bucket_uri = f"s3://{athena_bucket.bucket_name}/query-results/"

        athena_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:GetBucketLocation"],
                resources=[athena_bucket.bucket_arn],
                principals=[iam.ServicePrincipal("athena.amazonaws.com")],
            )
        )
        athena_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:ListBucket"],
                resources=[athena_bucket.bucket_arn],
                principals=[iam.ServicePrincipal("athena.amazonaws.com")],
                conditions={"StringEquals": {"s3:prefix": ["query-results/"]}},
            )
        )
        athena_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:PutObject", "s3:GetObject"],
                resources=[f"{athena_bucket.bucket_arn}/query-results/*"],
                principals=[iam.ServicePrincipal("athena.amazonaws.com")],
            )
        )
        athena_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:PutObject"],
                resources=[f"{athena_bucket.bucket_arn}/query-results/*"],
                principals=[iam.ServicePrincipal("athena.amazonaws.com")],
                conditions={"StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}},
            )
        )

        NagSuppressions.add_resource_suppressions(
            athena_bucket,
            [
                NagPackSuppression(
                    id="AwsSolutions-S1",
                    reason="AwsSolutions-S1: The bucket is not for production and should not require access logs.",
                )
            ],
            True,
        )

        # Configure Athena Query Editor and set the athena destination bucket
        athena_workgroup = athena.CfnWorkGroup(
            self,
            "AthenaWorkGroup",
            name="bedrock-workgroup",
            recursive_delete_option=True,
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                enforce_work_group_configuration=True,
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=athena_bucket_uri,
                    encryption_configuration=athena.CfnWorkGroup.EncryptionConfigurationProperty(
                        encryption_option="SSE_S3"
                    ),
                ),
            ),
        )

        # Export the athena workgroup name
        CfnOutput(
            self,
            "AthenaWorkGroupName",
            value=athena_workgroup.name,
            export_name="AthenaWorkGroupName",
        )
