import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import { CfnResource } from 'aws-cdk-lib';

export class MugSupportStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Step 1: Create an S3 bucket for artifacts
    const artifactsBucket = new s3.Bucket(this, 'ArtifactsBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Step 2: Create a KMS Key for encryption
    const kmsKey = new kms.Key(this, 'KmsKey', {
      enableKeyRotation: true,
    });

    // Step 3: Create an IAM role for the Bedrock Agent
    const bedrockAgentRole = new iam.Role(this, 'BedrockAgentRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonBedrockFullAccess'),
      ],
    });

    // Allow the role to use the S3 bucket and KMS key
    artifactsBucket.grantReadWrite(bedrockAgentRole);
    kmsKey.grantEncryptDecrypt(bedrockAgentRole);

    // Step 4: Define a VPC for the agent
    const vpc = new ec2.Vpc(this, 'BedrockAgentVpc', {
      maxAzs: 2,
    });

    // Step 5: Create the Bedrock Agent using a custom resource
    const bedrockAgent = new CfnResource(this, 'BedrockAgent', {
      type: 'AWS::Bedrock::Agent',
      properties: {
        AgentName: 'MyBedrockAgent',
        RoleArn: bedrockAgentRole.roleArn,
        VpcId: vpc.vpcId,
        SubnetIds: vpc.privateSubnets.map((subnet) => subnet.subnetId),
        ArtifactsS3Bucket: artifactsBucket.bucketName,
        KmsKeyArn: kmsKey.keyArn,
      },
    });

    // Output the Agent ARN
    new cdk.CfnOutput(this, 'BedrockAgentArn', {
      value: bedrockAgent.getAtt('Arn').toString(),
    });
  }
}
