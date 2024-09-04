from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import threading
from queue import Queue
from dotenv import load_dotenv
import webbrowser
import time
import signal
import subprocess
from utils import format_filename, remove_extension
from data_manager import AnalysisData

app = Flask(__name__)

# Add a custom filter to use in the Jinja2 template
app.jinja_env.filters['remove_extension'] = remove_extension

# Load environment variables
load_dotenv(r"C:\Users\jnhoward\OneDrive - Campbellsville University\Documents\transcript_training\.env")
openai_api_key = os.getenv('OPENAI_API_KEY')

# Initialize data manager
data_manager = AnalysisData()

repo_path = os.getcwd()  # Default repo path is the current working directory
progress = {"status": "", "details": "", "percent": 0, "lines_analyzed": 0, "characters_analyzed": 0}
gpt_processing = False  # Flag to track GPT processing status

# Set the output directory
main_transcript_dir = os.path.join(repo_path, 'processed_transcripts')
summary_file_path = os.path.join(main_transcript_dir, 'repo_summary.txt')

def create_directories():
    """Create required directories if they do not exist."""
    if not os.path.exists(main_transcript_dir):
        os.makedirs(main_transcript_dir)

def analyze_repo_files(repo_path):
    """Analyzes repository files and processes them."""
    global progress
    progress['status'] = 'Analyzing'
    progress['details'] = 'Repository analysis is in progress...'
    progress['percent'] = 0
    progress['lines_analyzed'] = 0
    progress['characters_analyzed'] = 0

    include_extensions = ['.py', '.gitignore', 'Dockerfile', '.yaml', '.yml', 'docker-compose', '.html', '.md', '.txt']
    exclude_dirs = {'venv', '.env', '__pycache__', '.git', '.github'}
    exclude_files = {'.env', '.DS_Store'}

    analysis_content = []
    total_files = 0
    processed_files = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file_name in files:
            if any(file_name.endswith(ext) for ext in include_extensions) and file_name not in exclude_files:
                total_files += 1

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file_name in files:
            if any(file_name.endswith(ext) for ext in include_extensions) and file_name not in exclude_files:
                file_path = os.path.join(root, file_name)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    data_manager.add_transcript(file_name, content)
                    analysis_content.append(f"<div class='file-section'><h2>{file_name}</h2><p>### File Path: {file_path}</p><pre><code class='language-python'>{content}</code></pre></div>")
                    progress['lines_analyzed'] += content.count('\n') + 1
                    progress['characters_analyzed'] += len(content)

                processed_files += 1
                progress['percent'] = int((processed_files / total_files) * 100)
                progress['details'] = f"Processing file {processed_files} of {total_files}..."

    create_directories()  # Ensure the directory exists before writing the summary file
    with open(summary_file_path, 'w', encoding='utf-8') as summary_file:
        summary_file.write('\n\n'.join(analysis_content))

    progress['status'] = 'Complete'
    progress['details'] = 'The repository analysis has been completed successfully.'
@app.route('/')
def index():
    """Render the main page with the contents of the current directory."""
    files = os.listdir(repo_path)
    return render_template('index.html', files=files, root_directory=repo_path)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle the repository analysis request."""
    global gpt_processing
    gpt_processing = True

    directory_to_analyze = request.form.get('directory', repo_path)
    threading.Thread(target=analyze_repo_files, args=(directory_to_analyze,)).start()

    return redirect(url_for('analysis_complete'))

@app.route('/analysis_complete')
def analysis_complete():
    """Check the status of the analysis and show the complete results."""
    report_content = ""

    if os.path.exists(summary_file_path):
        with open(summary_file_path, 'r', encoding='utf-8') as summary_file:
            report_content = summary_file.read()

    return render_template('analysis_complete.html', progress=progress, report_content=report_content)

@app.route('/trigger_gpt')
def trigger_gpt():
    """Trigger the GPT processing."""
    # Implement the GPT processing logic here
    return "GPT processing initiated."

def open_browser():
    """Open the Flask app in a new browser window and monitor the process."""
    url = 'http://127.0.0.1:5000'
    browser_process = subprocess.Popen(['python', '-m', 'webbrowser', '-t', url])
    return browser_process

if __name__ == '__main__':
    create_directories()
    browser_process = open_browser()
    try:
        app.run(debug=True, use_reloader=False)
    finally:
        browser_process.terminate()
        browser_process.wait()