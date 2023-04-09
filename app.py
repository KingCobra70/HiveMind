from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import os
import sqlite3
from transformers import pipeline
import concurrent.futures
from memory import ShortTermMemory, LongTermMemory, connect_to_database, create_table, insert_data_into_table, select_data_from_table, update_data_in_table

app = Flask(__name__)

def create_tables():
    conn = connect_to_database('responses.db')
    create_table(conn, 'responses')
    create_table(conn, 'short_term_memory')
    create_table(conn, 'long_term_memory')
    conn.close()

create_tables()

def store_question_and_response(question, response):
    conn = connect_to_database('responses.db')
    insert_data_into_table(conn, 'responses', (question, response))
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