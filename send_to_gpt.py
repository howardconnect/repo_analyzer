import os
import openai
from dotenv import load_dotenv

def load_env():
    """Load environment variables from the .env file."""
    load_dotenv(r"C:\Users\jnhoward\OneDrive - Campbellsville University\Documents\transcript_training\.env")
    openai.api_key = os.getenv('OPENAI_API_KEY')

def chunk_text(text, chunk_size):
    """Splits the text into chunks of a specified size."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def send_to_gpt(transcript_file_path):
    """Sends file contents to GPT and stores the overview in the result file."""
    load_env()
    gpt_response_path = os.path.join(os.path.dirname(transcript_file_path), 'gpt_response.txt')

    # Read transcript content
    with open(transcript_file_path, 'r', encoding='utf-8') as f:
        transcript_content = f.read()
    
    chunks = chunk_text(transcript_content, 4000)  # Adjust the chunk size if needed
    total_chunks = len(chunks)

    # Send chunks to GPT and save responses
    with open(gpt_response_path, 'w', encoding='utf-8') as output_file:
        for i, chunk in enumerate(chunks):
            prompt = f"Analyze the following chunk of code from a repository:\n\n{chunk}"
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",  # Use your preferred model
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    n=1,
                    temperature=0.5
                )
                result = response.choices[0].message['content'].strip()
                output_file.write(f"\n\n--- Response for chunk {i + 1} of {total_chunks} ---\n\n{result}\n")
                print(f"Chunk {i + 1} of {total_chunks} analyzed successfully.")
            except Exception as e:
                print(f"Error processing chunk {i + 1}: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python send_to_gpt.py <repo_path>")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    transcript_file_path = os.path.join(repo_path, 'repo_transcript.txt')
    send_to_gpt(transcript_file_path)
