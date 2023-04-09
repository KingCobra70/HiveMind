from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3
import pandas as pd
from ai_hivemind import ingest_data_from_huggingface_api, preprocess_data, store_data_in_database

app = Flask(__name__)

def create_table():
    conn = sqlite3.connect('hivemind.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS huggingface_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        input_text TEXT NOT NULL,
        output_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

create_table()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get user input
        input_text = request.form["input_text"]

        # Fetch and process data from HuggingFace API
        model_name = "bert-base-cased"
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        data = ingest_data_from_huggingface_api(model_name, api_key, input_text)
        preprocessed_data = preprocess_data(data)

        # Store data in the database
        store_data_in_database(preprocessed_data, "huggingface_results")

        return redirect(url_for("results"))

    return render_template("index.html")

@app.route("/results")
def results():
    # Fetch data from the database
    with sqlite3.connect("ai_hivemind.db") as conn:
        results_df = pd.read_sql("SELECT * FROM huggingface_results", conn)

    return render_template("results.html", results=results_df.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)