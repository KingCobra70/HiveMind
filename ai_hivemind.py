import os
import requests
import json
import pandas as pd
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

def ingest_data_from_huggingface_api(model_name, api_key, input_text):
    api_url = f"https://api-inference.huggingface.co/models/{model_name}"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = json.dumps({"inputs": input_text})
    
    response = requests.post(api_url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching data from Hugging Face API: {response.status_code}")

def preprocess_data(data):
    # Assuming that the API response has a field called 'generated_text'
    # You may need to adjust this based on the actual API response structure
    output_text = data.get("generated_text")
    preprocessed_data = {"output_text": output_text}
    
    return preprocessed_data

def store_data_in_database(preprocessed_data, table_name):
    conn = sqlite3.connect('huggingface_results.db')
    c = conn.cursor()

    c.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, output_text TEXT NOT NULL)")

    c.execute(f"INSERT INTO {table_name} (output_text) VALUES (?)", (preprocessed_data["output_text"],))

    conn.commit()
    conn.close()

def cluster_data():
    conn = sqlite3.connect('huggingface_results.db')
    df = pd.read_sql_query("SELECT * FROM huggingface_results", conn)
    conn.close()

    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(df["output_text"])

    kmeans = KMeans(n_clusters=3, random_state=42)
    kmeans.fit(X)

    df["cluster"] = kmeans.labels_

    return df