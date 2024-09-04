# data_manager.py

class AnalysisData:
    def __init__(self):
        self.repo_path = os.getcwd()
        self.transcripts = {}
        self.gpt_responses = {}

    def add_transcript(self, file_name, content):
        """Add transcript data to the storage."""
        self.transcripts[file_name] = content

    def add_gpt_response(self, file_name, response):
        """Add GPT response data to the storage."""
        self.gpt_responses[file_name] = response

    def get_transcript(self, file_name):
        """Retrieve a transcript by filename."""
        return self.transcripts.get(file_name, "")

    def get_gpt_response(self, file_name):
        """Retrieve a GPT response by filename."""
        return self.gpt_responses.get(file_name, "")
