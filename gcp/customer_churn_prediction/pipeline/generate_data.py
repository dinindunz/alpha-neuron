import pandas as pd
import numpy as np
from google.cloud import storage
from utils.config_reader import read_config

# Read configuration
config = read_config()
PROJECT_ID = config["project_id"]
BUCKET_NAME = config["bucket_name"]
DATA_FILE = "data/customer_churn.csv"

# Generate synthetic data
def generate_data():
    np.random.seed(42)
    num_samples = 10_000
    customer_id = np.arange(1, num_samples + 1)
    age = np.random.randint(18, 80, size=num_samples)
    gender = np.random.choice(["Male", "Female"], size=num_samples)
    tenure_months = np.random.randint(0, 60, size=num_samples)
    monthly_charges = np.random.uniform(20, 120, size=num_samples).round(2)
    total_charges = (tenure_months * monthly_charges + np.random.uniform(0, 50, size=num_samples)).round(2)
    num_support_tickets = np.random.randint(0, 10, size=num_samples)
    is_churn = np.random.choice([0, 1], size=num_samples, p=[0.8, 0.2])  # 20% churn rate

    # Create DataFrame
    df = pd.DataFrame({
        "customer_id": customer_id,
        "age": age,
        "gender": gender,
        "tenure_months": tenure_months,
        "monthly_charges": monthly_charges,
        "total_charges": total_charges,
        "num_support_tickets": num_support_tickets,
        "is_churn": is_churn,
    })

    return df

# Upload dataset to GCS
def upload_to_gcs(local_path, gcs_path):
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path)
    print(f"Uploaded {local_path} to gs://{BUCKET_NAME}/{gcs_path}")

if __name__ == "__main__":
    data = generate_data()
    local_file_path = "customer_churn.csv"
    data.to_csv(local_file_path, index=False)
    upload_to_gcs(local_file_path, DATA_FILE)
