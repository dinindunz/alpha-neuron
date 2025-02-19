import os
import yaml
from google.cloud import aiplatform
from kfp.v2 import dsl
from kfp.v2.google.client import AIPlatformClient
from kfp.v2.dsl import Dataset, Model, Input, Output

# Load configuration from config.yaml
def load_config(config_path="config/config.yaml"):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

# Read config
config = load_config()
PROJECT_ID = config["project_id"]
REGION = config["region"]
BUCKET_NAME = config["bucket_name"]
PIPELINE_ROOT = f"gs://{BUCKET_NAME}/pipeline_root"

@dsl.pipeline(
    name=config["pipeline_name"],
    pipeline_root=PIPELINE_ROOT,
)
def churn_prediction_pipeline():
    # Step 1: Generate synthetic data
    generate_data_task = dsl.ContainerOp(
        name="generate-data",
        image="python:3.9",
        command=["python", "pipeline/generate_data.py"],
        arguments=[],
        file_outputs={"output": "/tmp/output"},
    )

    # Step 2: Train model
    train_task = dsl.ContainerOp(
        name="train-model",
        image="python:3.9",
        command=["python", "pipeline/train.py"],
        arguments=[],
    ).after(generate_data_task)

    # Step 3: Deploy model
    deploy_task = dsl.ContainerOp(
        name="deploy-model",
        image="python:3.9",
        command=["python", "pipeline/deploy.py"],
        arguments=[],
    ).after(train_task)

# Compile the pipeline
def compile_pipeline():
    pipeline_file = "churn_prediction_pipeline.json"
    from kfp.v2.compiler import Compiler

    Compiler().compile(
        pipeline_func=churn_prediction_pipeline,
        package_path=pipeline_file,
    )
    print(f"Pipeline compiled to {pipeline_file}")

# Run the pipeline
def run_pipeline():
    aiplatform.init(project=PROJECT_ID, location=REGION)

    client = AIPlatformClient(project_id=PROJECT_ID, region=REGION)

    response = client.create_run_from_job_spec(
        job_spec_path="churn_prediction_pipeline.json",
        pipeline_root=PIPELINE_ROOT,
        parameter_values={},
    )

    print("Pipeline run details:")
    print(response)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=["compile", "run"], help="Compile or run the pipeline"
    )
    args = parser.parse_args()

    if args.action == "compile":
        compile_pipeline()
    elif args.action == "run":
        run_pipeline()
