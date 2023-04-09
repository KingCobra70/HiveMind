from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import os
import sqlite3
import pandas as pd
from ai_hivemind import ingest_data_from_huggingface_api, preprocess_data, store_data_in_database

app = Flask(__name__)

# Define a function to create a table in SQLite database
def create_table():
    conn = sqlite3.connect('responses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            response TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Call create_table function to create a table in the database
create_table()

# Add other functions here

def store_question_and_response(question, response):
    conn = sqlite3.connect('responses.db')
    c = conn.cursor()
    c.execute('INSERT INTO responses (question, response) VALUES (?, ?)', (question, response))
    conn.commit()
    conn.close()

def model_interaction(input_text):
    model_name = "bert-base-cased"
    api_key = os.getenv("HUGGINGFACE_API_KEY")

    # Ingest data from Hugging Face API
    data = ingest_data_from_huggingface_api(model_name, api_key, input_text)

    # Preprocess data
    preprocessed_data = preprocess_data(data)

    # Store data in SQLite database
    store_data_in_database(preprocessed_data, "huggingface_results")

    # Extract output_text from preprocessed_data
    output_text = preprocessed_data["output_text"]

    return output_text
app.config['UPLOAD_FOLDER'] = 'uploads'

# Define the index route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        input_text = request.form.get('input_text')
        input_image = request.files.get('input_image')
        input_audio = request.files.get('input_audio')
        input_video = request.files.get('input_video')

        # Save uploaded files to disk
        if input_image:
            filename = secure_filename(input_image.filename)
            input_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        if input_audio:
            filename = secure_filename(input_audio.filename)
            input_audio.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        if input_video:
            filename = secure_filename(input_video.filename)
            input_video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Process input_text, input_image, input_audio, input_video as needed

        return redirect(url_for('results'))
    else:
        return render_template('index.html')
# Define the results route
@app.route("/results")
def results():
    conn = sqlite3.connect('responses.db')
    c = conn.cursor()
    c.execute('SELECT * FROM responses')
    responses = c.fetchall()
    conn.close()
    return render_template('results.html', responses=responses)

# Define the interact route to handle POST requests from the frontend
@app.route('/interact', methods=['POST'])
def interact():
    input_text = request.json.get('input_text')
    output_text = model_interaction(input_text)
    return jsonify({'output_text': output_text})

# Run the Flask app if this is the main module
if __name__ == "__main__":
    app.run(debug=True)