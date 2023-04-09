from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import os
import sqlite3
import pandas as pd
from ai_hivemind import ingest_data_from_huggingface_api, preprocess_data, store_data_in_database
from transformers import pipeline
import concurrent.futures
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user


app = Flask(__name__)


class User(UserMixin):
    def __init__(self, id):
        self.id = id

login_manager = LoginManager(app)
login_manager.login_view = 'google.login'

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

google_blueprint = make_google_blueprint(
    client_id="YOUR_GOOGLE_CLIENT_ID",
    client_secret="YOUR_GOOGLE_CLIENT_SECRET",
    scope=["profile", "email"]
)

app.register_blueprint(google_blueprint, url_prefix="/login")

@app.route("/results")
@login_required
def results():


@app.route("/login")
def login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    email = resp.json()["email"]
    user = User(email)
    login_user(user)
    return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

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

create_table()

def store_question_and_response(question, response):
    conn = sqlite3.connect('responses.db')
    c = conn.cursor()
    c.execute('INSERT INTO responses (question, response) VALUES (?, ?)', (question, response))
    conn.commit()
    conn.close()

def process_model(model_name, input_text):
    model = pipeline('text-generation', model=model_name)
    response = model(input_text)
    return response

def parallel_process_model(model_name, input_text, results):
    response = process_model(model_name, input_text)
    results[model_name] = response

def model_interaction(input_text):
    model_names = [
        'gpt2',
        'bert-base-uncased',
        'roberta-base'
    ]

    results = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(parallel_process_model, model_name, input_text, results) for model_name in model_names]
        concurrent.futures.wait(futures)

    model_responses = list(results.values())
    brain_output = find_consensus(model_responses)

    # Delegate to other models if needed
    final_output = delegate_to_models(input_text, brain_output)

    return final_output

def delegate_to_models(question, brain_output):
    if "delegate to model a" in brain_output.lower():
        return model_a(question)
    elif "delegate to model b" in brain_output.lower():
        return model_b(question)
    elif "delegate to model c" in brain_output.lower():
        return model_c(question)
    elif "get consensus" in brain_output.lower():
        responses = [model_a(question), model_b(question), model_c(question)]
        # You can use a function like find_consensus() to get a consensus from the responses
        consensus = find_consensus(responses)
        return consensus
    else:
        # If the brain model doesn't delegate to any specific model or ask for a consensus, return its response
        return brain_output
    

def find_consensus(model_responses):
    # For simplicity, this function just returns the first response from the list of model responses.
    # You can replace this with a more sophisticated approach to find the consensus among responses.
    return model_responses[0]

app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        input_text = request.form.get('input_text')
        input_image = request.files.get('input_image')
        input_audio = request.files.get('input_audio')
        input_video = request.files.get('input_video')

        if input_image:
            filename = secure_filename(input_image.filename)
            input_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        if input_audio:
            filename = secure_filename(input_audio.filename)
            input_audio.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        if input_video:
            filename = secure_filename(input_video.filename)
            input_video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        return redirect(url_for('results'))
    else:
        return render_template('index.html')

@app.route("/results")
def results():
    conn = sqlite3.connect('responses.db')
    c = conn.cursor()
    c.execute('SELECT * FROM responses')
    responses = c.fetchall()
    conn.close()
    return render_template('results.html', responses=responses)

@app.route('/interact', methods=['POST'])
def interact():
    input_text = request.json.get('input_text')
    output_text = model_interaction(input_text)
    return jsonify({'output_text': output_text})

if __name__ == "__main__":
    app.run(debug=True)