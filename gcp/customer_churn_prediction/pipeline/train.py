import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from utils.config_reader import read_config

# Read configuration
config = read_config()
BUCKET_NAME = config["bucket_name"]

# Load the dataset from GCS
def load_data():
    gcs_data_path = f"gs://{BUCKET_NAME}/data/customer_churn.csv"
    df = pd.read_csv(gcs_data_path)
    features = df[["age", "tenure_months", "monthly_charges", "total_charges", "num_support_tickets"]]
    labels = df["is_churn"]
    return features, labels

# Training process...
