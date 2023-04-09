import json
import requests
import pandas as pd
import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve sensitive information from environment variables
api_keys = [
    os.getenv("HUGGINGFACE_API_KEY_1"),
    os.getenv("HUGGINGFACE_API_KEY_2"),
    os.getenv("HUGGINGFACE_API_KEY_3")
]

db_config = {
    "user": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME")
}

def call_huggingface_api(model_name, api_key, data):
    endpoint = f"https://api.huggingface.co/models/{model_name}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.post(endpoint, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    
    return response.json()

def store_results_in_db(df, table_name, db_connection):
    df.to_sql(table_name, con=db_connection, if_exists="replace", index=False)

def load_data_from_db(table_name, db_connection):
    return pd.read_sql(f"SELECT * FROM {table_name}", db_connection)

def preprocess_data(text):
    vectorizer = TfidfVectorizer()
    return vectorizer.fit_transform(text)

def cluster_data(X, n_clusters=3, random_state=0):
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    kmeans.fit(X)
    return kmeans.labels_

# Define model names and API keys
model_names = ["bert-base-cased", "gpt-2", "xlnet-base-cased"]
api_keys = ["YOUR_API_KEY_1", "YOUR_API_KEY_2", "YOUR_API_KEY_3"]

# Define data to be processed by API
data = {
    "inputs": [
        {
            "text": "This is a sample input text."
        }
    ]
}

# Call HuggingFace API for each model
results = []
for model_name, api_key in zip(model_names, api_keys):
    try:
        result = call_huggingface_api(model_name, api_key, data)
        results.append(result)
        print(f"API request successful for model {model_name}.")
    except requests.HTTPError as e:
        print(f"API request failed for model {model_name}. Response code: {e.response.status_code}")

# Convert results to pandas DataFrame
df = pd.DataFrame(results)

# Database credentials
db_config = {
    "user": "YOUR_DB_USERNAME",
    "password": "YOUR_DB_PASSWORD",
    "host": "YOUR_DB_HOST",
    "database": "YOUR_DB_NAME"
}

# Store and load data using context manager
with mysql.connector.connect(**db_config) as cnx:
    store_results_in_db(df, "results", cnx)
    df = load_data_from_db("results", cnx)

# Preprocess and cluster data
X = preprocess_data(df["text"].values)
labels = cluster_data(X)

# Store cluster labels and update database
df["cluster"] = labels
with mysql.connector.connect(**db_config) as cnx:
    store_results_in_db(df, "results", cnx)
