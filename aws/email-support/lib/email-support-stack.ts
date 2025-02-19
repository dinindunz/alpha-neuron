import { EmailTextProcessor } from "@project-lakechain/email-text-processor";
import { CacheStorage } from "@project-lakechain/core";
import { S3EventTrigger } from "@project-lakechain/s3-event-trigger";
import { SqsStorageConnector } from "@project-lakechain/sqs-storage-connector";
import { join } from 'path';

import {
  aws_lambda as lambda,
  aws_sqs as sqs,
  aws_s3 as s3,
  aws_lambda_nodejs as nodejs,
  aws_iam as iam,
} from "aws-cdk-lib";

import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";

export class EmailSupportStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const bucket = new s3.Bucket(this, "Bucket", {});

    const cache = new CacheStorage(this, "Cache");
    const processedEmailsQueue = new sqs.Queue(this, "ProcessedEmailsQueue");
    const responseQueue = new sqs.Queue(this, "ResponseQueue");

    // Create the S3 event trigger.
    const trigger = new S3EventTrigger.Builder()
      .withScope(this)
      .withIdentifier("Trigger")
      .withCacheStorage(cache)
      .withBucket(bucket)
      .build();

    // Create the email text processor
    const emailProcessor = new EmailTextProcessor.Builder()
      .withScope(this)
      .withIdentifier("EmailProcessor")
      .withCacheStorage(cache)
      .withSource(trigger)
      .withOutputFormat("text")
      .withIncludeAttachments(false)
      .build();

    // Create the SQS storage connector for processed emails
    const processedEmailsConnector = new SqsStorageConnector.Builder()
      .withScope(this)
      .withIdentifier("ProcessedEmailsConnector")
      .withCacheStorage(cache)
      .withSource(emailProcessor)
      .withDestinationQueue(processedEmailsQueue)
      .build();

    const orchestratorLambda = new nodejs.NodejsFunction(
      this,
      "OrchestratorLambda",
      {
        entry: join("lambda", "index.ts"),
        handler: "handler",
        runtime: lambda.Runtime.NODEJS_20_X,
        environment: {
          RESPONSE_QUEUE_URL: responseQueue.queueUrl,
        },
        memorySize: 2048,
        timeout: cdk.Duration.minutes(10),
      }
    );

    orchestratorLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["bedrock:InvokeModel"],
        resources: ["*"],
      })
    );

    // Grant Lambda permissions to read from processedEmailsQueue and write to responseQueue
    processedEmailsQueue.grantConsumeMessages(orchestratorLambda);
    responseQueue.grantSendMessages(orchestratorLambda);
    processedEmailsConnector.grantReadProcessedDocuments(orchestratorLambda);
    emailProcessor.grantReadProcessedDocuments(orchestratorLambda);

    // Set up event source mapping for Lambda
    new lambda.EventSourceMapping(this, "OrchestratorEventSourceMapping", {
      target: orchestratorLambda,
      batchSize: 10,
      eventSourceArn: processedEmailsQueue.queueArn,
    });
  }
}
