import os
import openai
import threading
from queue import Queue
from dotenv import load_dotenv
import argparse
from tqdm import tqdm  # For progress bars
import math

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

# List of included files/extensions
INCLUDE_FILES = {
    'requirements.txt', '*.py', '*.js', '*.ts', '*.java', '*.cpp', '*.c', '*.h', '*.rb', '*.go', '*.sh', '*.bash',
    '*.html', '*.css', '*.scss', '*.yml', '*.yaml', '*.json', '*.toml', '*.ini', '*.conf', '*.md', '*.rst', 'README*',
    'Makefile', 'Dockerfile', 'docker-compose.yml', '*.bat', 'Pipfile', 'Pipfile.lock', 'pyproject.toml', 
    'requirements.txt', 'package.json', 'package-lock.json', 'Cargo.toml', 'Cargo.lock', 'Gemfile', 'Gemfile.lock',
    'build.gradle', 'pom.xml'
}

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
    with open(transcript_file_path, 'w', encoding='utf-8') as transcript_file:
        for root, dirs, files in tqdm(os.walk(repo_path), desc="Analyzing repository", unit="files"):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file_name in files:
                if should_include_file(file_name):
                    file_path = os.path.join(root, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # Write content to transcript file
                        transcript_file.write(f"\n\n--- File: {file_name} ---\n\n")
                        transcript_file.write(content[:1000])  # Limit to 1000 characters per file

                        # Add the content to the queue for further processing
                        file_info = {
                            "path": file_path,
                            "name": file_name,
                            "content": content[:1000]  # Limit content to prevent large payloads
                        }
                        file_queue.put(file_info)
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")

def chunk_text(text, chunk_size):
    """Splits the text into chunks of a specified size."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def send_to_gpt(file_queue, result_queue):
    """Sends file contents to GPT and stores the overview in the result queue."""
    while not file_queue.empty():
        file_info = file_queue.get()
        prompt = f"Analyze the following code file and provide an overview:\n\n{file_info['content']}"
        try:
            print(f"Calling GPT for file: {file_info['name']}")
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            result = {
                "file": file_info['name'],
                "overview": response['choices'][0]['message']['content']
            }
            result_queue.put(result)
            print("The GPT has spoken!")
        except Exception as e:
            print(f"Error processing {file_info['name']}: {e}")

def analyze_repository(repo_path):
    """Main function to analyze a repository and get overviews using GPT."""
    file_queue = Queue()
    result_queue = Queue()
    transcript_file_path = os.path.join(repo_path, 'repo_transcript.txt')

    # Analyze files and create a transcript
    print("Starting repository analysis...")
    analyze_repo_files(repo_path, file_queue, transcript_file_path)
    print("Repository analysis complete.")

    # Read the transcript file content
    with open(transcript_file_path, 'r', encoding='utf-8') as f:
        transcript_content = f.read()

    # Chunk the transcript for GPT
    chunk_size = 1000  # Example chunk size
    chunks = chunk_text(transcript_content, chunk_size)
    total_chunks = len(chunks)
    print(f"Calling GPT... Total chunks to process: {total_chunks}")

    # Send chunks to GPT
    for i, chunk in enumerate(chunks):
        print(f"Sending chunk {i + 1} of {total_chunks}... Waiting for GPT response...")
        prompt = f"Analyze the following chunk of code from a repository:\n\n{chunk}"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response['choices'][0]['message']['content']
            print(f"Chunk {i + 1} of {total_chunks} analyzed successfully. The GPT has spoken!")
        except Exception as e:
            print(f"Error processing chunk {i + 1} of {total_chunks}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze a GitHub repository and provide an overview of its contents.')
    parser.add_argument('repo_path', type=str, help='Path to the repository to be analyzed')
    args = parser.parse_args()

    analyze_repository(args.repo_path)
