# flask_app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import threading
from queue import Queue
from dotenv import load_dotenv
import webbrowser
import signal
import sys

# Importing the utility function and data manager
from utils import format_filename
from data_manager import AnalysisData

app = Flask(__name__)

# Load environment variables
load_dotenv(r"C:\Users\jnhoward\OneDrive - Campbellsville University\Documents\transcript_training\.env")
openai_api_key = os.getenv('OPENAI_API_KEY')

# Initialize data manager
data_manager = AnalysisData()

repo_path = os.getcwd()  # Default repo path is the current working directory
progress = {"status": "", "details": ""}
gpt_processing = False  # Flag to track GPT processing status

# Set the output directories
main_transcript_dir = os.path.join(repo_path, 'processed_transcripts')
card_view_dir = os.path.join(main_transcript_dir, 'card_view')

def create_directories():
    """Create required directories if they do not exist."""
    os.makedirs(main_transcript_dir, exist_ok=True)
    os.makedirs(card_view_dir, exist_ok=True)

def analyze_repo_files(repo_path):
    """Analyzes repository files and processes them."""
    for root, dirs, files in os.walk(repo_path):
        for file_name in files:
            if file_name.endswith('.txt'):
                file_path = os.path.join(root, file_name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Add transcript to data manager
                    data_manager.add_transcript(file_name, content)
                    # Process the file and generate analysis card
                    save_analysis_card(content, file_name)

def save_analysis_card(content, card_name):
    """Save analysis content to a card file."""
    card_name = format_filename(card_name)  # Use the utility function to format the name
    card_path = os.path.join(card_view_dir, f"{card_name}.html")
    with open(card_path, 'w', encoding='utf-8') as file:
        file.write(f"<pre>{content}</pre>")

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle the repository analysis request."""
    global gpt_processing
    gpt_processing = True
    threading.Thread(target=analyze_repo_files, args=(repo_path,)).start()
    return redirect(url_for('status'))

@app.route('/status')
def status():
    """Check the status of the analysis."""
    return render_template('status.html', progress=progress)

@app.route('/view/<filename>')
def view_analysis(filename):
    """View analysis result."""
    content = data_manager.get_transcript(filename)
    return render_template('view_analysis.html', content=content)

@app.route('/gpt', methods=['POST'])
def send_to_gpt():
    """Send analyzed data to GPT."""
    # Your logic to send data to GPT
    pass

if __name__ == '__main__':
    create_directories()
    webbrowser.open('http://127.0.0.1:5000')
    app.run(debug=True, use_reloader=False)
