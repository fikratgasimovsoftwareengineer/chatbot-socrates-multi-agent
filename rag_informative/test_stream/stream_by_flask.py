from flask import Flask, request, Response, stream_with_context, jsonify
from flask_cors import CORS
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import logging
import time
# Load environment variables from .env file
load_dotenv()

class StreamGpt:
    def __init__(self):
        self.app = Flask(__name__)  # Define Flask app
        CORS(self.app)  # Enable CORS for cross-origin requests
        
        # Get Azure OpenAI credentials from environment variables
        self.azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.api_version = os.getenv('AZURE_API_VERSION')

        if not self.azure_endpoint or not self.api_key:
            logging.error("Missing Azure Endpoint or API Key")

        # Initialize OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )

        # System message template
        self.system_message_template = """
            "You are an AI Assistant. You need to support students and professors with Socrates Motivational Conversations. 
            First ensure a deep understanding of the user's question by paraphrasing it. Always prioritize understanding the 
            semantic meaning of the question."
        """

        self.conversation_history = [
            {"role": "system", "content": self.system_message_template}
        ]

        # Define routes
        self.app.add_url_rule('/uninettuno_assistant', view_func=self.uninettuno_assistant, methods=['POST'])

    def uninettuno_assistant(self):
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        
        # Get streaming response
        return self.get_response(question)

    def get_response(self, question):
        # Append the user's question to the conversation history
        self.conversation_history.append({"role": "user", "content": question})
        
        

        # Make the OpenAI API call with streaming enabled
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.conversation_history,
            max_tokens=3000,  # Increase max tokens
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=True  # Enable streaming for real-time responses
        )

        def generate_stream():
            batch = ""  # Accumulate tokens in a batch
            for token in self.extract_content(response):
                batch += token
               
                if len(batch) > 4:  # Send tokens in batches for efficiency
                    logging.debug(f"Streaming batch:{batch}")
                    print("batch 1",  print(batch))
                    yield batch
                    batch = ""
                    time.sleep(0.2)
            if batch:  # Yield any remaining tokens
                logging.debug(f"final BATCH: {batch}")
                print("batch 2",batch)
                yield batch
                time.sleep(0.2)

        return Response(stream_with_context(generate_stream()), content_type='text/plain')

    def extract_content(self, response):
        for chunk in response:
            if hasattr(chunk,'choices') and chunk.choices:
                content = chunk.choices[0].delta.content
                if content:  # Ensure the content is not empty
                    yield content

# Run the app
if __name__ == "__main__":
    streaming = StreamGpt()
    streaming.app.run(debug=True)
