import { SQSEvent } from "aws-lambda";
import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";
import { orchestrator } from "./agents";
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { Readable } from "stream";

const sqs = new SQSClient({});
const s3 = new S3Client({});

export const lambda_handler = async (event: SQSEvent): Promise<void> => {
  for (const record of event.Records) {
    const eventData = JSON.parse(record.body);
    console.log("Event Data: ", JSON.stringify(eventData, null, 2));
    /* the event has the following format 
    /*
    {
        "specversion": "1.0",
        "id": "3c68ba6f-b915-4012-99de-45daa1444e0e",
        "type": "document-created",
        "time": "2024-09-11T14:38:16.586Z",
        "data": {
            "chainId": "2c6ee975-6727-4c85-8091-71fd041d6cfb",
            "source": {
                "url": "s3://my-bucket/my-email-file.eml",
                "type": "message/rfc822",
                "size": 22827,
                "etag": "a381b075bb19d0ed1c85231594cd648c"
            },
            "document": {
                "url": "s3://PATH",
                "type": "text/plain",
                "size": 1466,
                "etag": "b220a4cb8d4d3a632ca23495154eb9c6"
            },
            "metadata": {
                "properties": {
                    "kind": "text",
                    "attrs": {}
                },
                "createdAt": "2024-09-06T13:05:32.000Z",
                "authors": [
                    "sav"
                ],
                "title": "Where is my order?"
            },
            "callStack": [
                "email-text-processor",
                "s3-event-trigger"
            ]
        }
    }
    */

    const documentUrl = eventData.data.document.url;
    const subject = eventData.data.metadata.title;

    // Extract the S3 bucket and key from the URL
    const { bucketName, objectKey } = parseS3Url(documentUrl);
    console.log(`Bucket: ${bucketName}, Key: ${objectKey}`);

    try {
      // Retrieve the document from S3
      const objectContent = await getDocumentFromS3(bucketName, objectKey);
      console.log("Document Content:\n", objectContent);
      const response = await orchestrator.routeRequest(
        objectContent,
        "userId",
        "sessionId"
      );

      // Print the subject and text before sending the message
      console.log("Subject:", `Re: ${subject}`);
      console.log("Text:", response.output);

      const sendMessageCommand = new SendMessageCommand({
        QueueUrl: process.env.RESPONSE_QUEUE_URL!,
        MessageBody: JSON.stringify({
          subject: `Re: ${subject}`,
          text: response.output,
          handlingAgent: response.metadata.agentName,
        }),
      });

      await sqs.send(sendMessageCommand);
    } catch (error) {
      console.error("Error retrieving document from S3:", error);
    }
  }
};

// Helper function to parse S3 URL
const parseS3Url = (url: string): { bucketName: string; objectKey: string } => {
  const match = url.match(/^s3:\/\/([^\/]+)\/(.+)$/);
  if (!match) {
    throw new Error(`Invalid S3 URL: ${url}`);
  }
  return {
    bucketName: match[1],
    objectKey: match[2],
  };
};

// Helper function to retrieve the document from S3
const getDocumentFromS3 = async (
  bucketName: string,
  key: string
): Promise<string> => {
  const command = new GetObjectCommand({
    Bucket: bucketName,
    Key: key,
  });

  const response = await s3.send(command);

  const streamToString = (stream: Readable): Promise<string> =>
    new Promise((resolve, reject) => {
      const chunks: Uint8Array[] = [];
      stream.on("data", (chunk) => chunks.push(chunk));
      stream.on("end", () => resolve(Buffer.concat(chunks).toString("utf-8")));
      stream.on("error", reject);
    });

  return streamToString(response.Body as Readable);
};
