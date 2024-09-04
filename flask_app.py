from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import threading
from queue import Queue
from dotenv import load_dotenv
import openai
from tqdm import tqdm
import math

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from the .env file
load_dotenv(r"C:\Users\jnhoward\OneDrive - Campbellsville University\Documents\transcript_training\.env")
openai.api_key = os.getenv('OPENAI_API_KEY')

# List of excluded directories and files
EXCLUDE_DIRS = {
    '.git', 'venv', 'node_modules', '__pycache__', 'chapter_guidelines', 'formatted_notes', 'transcripts'
}
EXCLUDE_FILES = {
    '.env', '.DS_Store', 'Thumbs.db', '*.log', '*.pyc', '*.pyo', '*.pyd', 'pip-log.txt', 'pip-delete-this-directory.txt'
}

INCLUDE_FILES = {
    'requirements.txt', '*.py', '*.js', '*.ts', '*.java', '*.cpp', '*.c', '*.h', '*.rb', '*.go', '*.sh', '*.bash',
    '*.html', '*.css', '*.scss', '*.yml', '*.yaml', '*.json', '*.toml', '*.ini', '*.conf', '*.md', '*.rst', 'README*',
    'Makefile', 'Dockerfile', 'docker-compose.yml', '*.bat', 'Pipfile', 'Pipfile.lock', 'pyproject.toml', 
    'requirements.txt', 'package.json', 'package-lock.json', 'Cargo.toml', 'Cargo.lock', 'Gemfile', 'Gemfile.lock',
    'build.gradle', 'pom.xml'
}

# Global progress tracking
progress = {"status": "", "details": ""}

def should_include_file(file_name):
    """Determine if a file should be included based on its name and extension."""
    for pattern in EXCLUDE_FILES:
        if file_name.endswith(pattern) or file_name == pattern:
            return False
    for pattern in INCLUDE_FILES:
        if file_name.endswith(pattern) or file_name.startswith(pattern.split('*')[0]):
            return True
    return False

def analyze_repo_files(repo_path, file_queue, transcript_file_path):
    """Analyzes all files in the repository and writes their content to a transcript file."""
    global progress
    with open(transcript_file_path, 'w', encoding='utf-8') as transcript_file:
        for root, dirs, files in tqdm(os.walk(repo_path), desc="Analyzing repository", unit="files"):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file_name in files:
                if should_include_file(file_name):
                    file_path = os.path.join(root, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        transcript_file.write(f"\n\n--- File: {file_name} ---\n\n")
                        transcript_file.write(content[:1000])  # Limit to 1000 characters per file
                        print(f"Processed file: {file_name}")
                        
                        file_info = {"path": file_path, "name": file_name, "content": content[:1000]}
                        file_queue.put(file_info)
                    except Exception as e:
                        progress["status"] = f"Error reading {file_path}: {e}"
                        print(progress["status"])

def chunk_text(text, chunk_size):
    """Splits the text into chunks of a specified size."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def send_to_gpt(file_queue, result_queue):
    """Sends file contents to GPT and stores the overview in the result queue."""
    global progress
    while not file_queue.empty():
        file_info = file_queue.get()
        prompt = f"Analyze the following code file and provide an overview:\n\n{file_info['content']}"
        try:
            progress["status"] = f"Calling GPT for file: {file_info['name']}"
            print(progress["status"])
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            result = {"file": file_info['name'], "overview": response['choices'][0]['message']['content']}
            result_queue.put(result)
            progress["status"] = "The GPT has spoken!"
        except Exception as e:
            progress["status"] = f"Error processing {file_info['name']}: {e}"
            print(progress["status"])

@app.route("/", methods=["GET", "POST"])
def index():
    """Render the main page to start the repository analysis."""
    if request.method == "POST":
        repo_path = request.form["repo_path"]
        threading.Thread(target=analyze_repository, args=(repo_path,)).start()
        return redirect(url_for("status"))
    return render_template("index.html")

@app.route("/view_transcript")
def view_transcript():
    """Display the repository transcript."""
    repo_path = request.args.get('repo_path', '')
    transcript_file_path = os.path.join(repo_path, 'repo_transcript.txt')
    try:
        with open(transcript_file_path, 'r', encoding='utf-8') as f:
            transcript_content = f.read()
        return render_template("view_transcript.html", content=transcript_content)
    except Exception as e:
        return f"Error reading the transcript: {e}"

@app.route("/send_to_robot")
def send_to_robot():
    """Send the transcript to the 'repo robot'."""
    # Logic to send the transcript to the 'repo robot'
    return "Transcript sent to the Repo Robot!"

@app.route("/status")
def status():
    """Render the status page to show progress of the analysis."""
    return render_template("status.html", progress=progress)

def analyze_repository(repo_path):
    """Main function to analyze a repository and get overviews using GPT."""
    global progress
    file_queue = Queue()
    result_queue = Queue()
    transcript_file_path = os.path.join(repo_path, 'repo_transcript.txt')
    
    progress["status"] = "Starting repository analysis..."
    analyze_repo_files(repo_path, file_queue, transcript_file_path)
    progress["status"] = "Repository analysis complete. Preparing transcript..."

    with open(transcript_file_path, 'r', encoding='utf-8') as f:
        transcript_content = f.read()
    
    chunks = chunk_text(transcript_content, 1000)
    total_chunks = len(chunks)
    progress["status"] = f"Transcript prepared. Total chunks to process: {total_chunks}"

    # Send chunks to GPT
    for i, chunk in enumerate(chunks):
        progress["status"] = f"Sending chunk {i + 1} of {total_chunks}... Waiting for GPT response..."
        prompt = f"Analyze the following chunk of code from a repository:\n\n{chunk}"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response['choices'][0]['message']['content']
            print(f"Chunk {i + 1} of {total_chunks} analyzed successfully. The GPT has spoken!")
        except Exception as e:
            progress["status"] = f"Error processing chunk {i + 1} of {total_chunks}: {e}"

    progress["status"] = "The Repository Transcript is complete! You can view it here or send it to the 'repo robot'."

if __name__ == "__main__":
    app.run(debug=True)
