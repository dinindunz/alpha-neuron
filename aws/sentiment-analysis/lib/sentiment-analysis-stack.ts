import * as cdk from 'aws-cdk-lib';
import { Stack, StackProps } from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import { Construct } from 'constructs';
import { join } from "path";

export class SentimentAnalysisStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // Create an S3 bucket
    const bucket = new s3.Bucket(this, 'Bucket', {
      bucketName: "sentiment-analysis-bucket-dini",
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Create bucket policy needed for the lambda functions.
    const bucketPolicy = new iam.PolicyStatement({
      actions: [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
      ],
      effect: iam.Effect.ALLOW,
      resources: [
        bucket.bucketArn,
        bucket.bucketArn + "/*",
      ],
      sid: "AllowBucketAccess",
    });

    // Create python layer
    const sharedLayer = new lambda.LayerVersion(this, "SharedLayer", {
      code: lambda.Code.fromAsset("./python_layers"),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      layerVersionName: "python-shared-layer",
    });

    // Create a transcribe Lambda function
    const transcribeLambda = new lambda.Function(this, 'TranscribeLambda', {
      functionName: "transcribe-lambda",
      runtime: lambda.Runtime.PYTHON_3_12,
      code: lambda.Code.fromAsset(join(__dirname, "..", "handler")),
      handler: 'transcribe.lambda_handler',
      layers: [sharedLayer],
      timeout: cdk.Duration.minutes(15),
    });

    // Grant transcribe permissions
    transcribeLambda.addToRolePolicy(new iam.PolicyStatement({      
      actions: [
        'transcribe:StartTranscriptionJob',
        'transcribe:GetTranscriptionJob',
        'transcribe:ListTranscriptionJobs',
      ],
      effect: iam.Effect.ALLOW,
      resources: [
        `arn:aws:transcribe:${this.region}:${this.account}:transcription-job/*`,
      ],
    }))

    // Create a summarise Lambda function
    const summariseLambda = new lambda.Function(this, 'SummariseLambda', {
      functionName: "summarise-lambda",
      runtime: lambda.Runtime.PYTHON_3_12,
      code: lambda.Code.fromAsset(join(__dirname, "..", "handler")),
      handler: 'summarise.lambda_handler',
      layers: [sharedLayer],
      timeout: cdk.Duration.minutes(15),
    });

    // Grant Bedrock permissions
    summariseLambda.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['bedrock:InvokeModel'],
      resources: [`arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-text-express-v1`],
    }));

    // Grant the Lambda functions required permissions to the bucket
    transcribeLambda.addToRolePolicy(bucketPolicy);
    summariseLambda.addToRolePolicy(bucketPolicy);
    bucket.grantRead(transcribeLambda);
    bucket.grantRead(summariseLambda);

    // Add an event notification for the Lambda function when an object is created
    bucket.addEventNotification(
      s3.EventType.OBJECT_CREATED_PUT,
      new s3n.LambdaDestination(transcribeLambda), {
        suffix: ".mp3"
      }
    );
    bucket.addEventNotification(
      s3.EventType.OBJECT_CREATED_PUT,
      new s3n.LambdaDestination(summariseLambda), {
        suffix: "transcript.json"
      }
    );

    // Output the bucket name
    new cdk.CfnOutput(this, 'BucketName', {
      value: bucket.bucketName,
    });
  }
}
