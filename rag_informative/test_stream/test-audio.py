from flask import Flask, Response, request
import requests
import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv('/socrates/server_model_interrogazione/test_stream/.env')
app = Flask(__name__)
# Load environment variables
endpoint = os.getenv("AZURE_REALTIME_ENDPOINT")
deployment = os.getenv("AZURE_TTS_NAME")
key = os.getenv("AZURE_OPENAI_API_KEY")

url = f"{endpoint}/openai/deployments/{deployment}/audio/speech?api-version=2024-05-01-preview"

"""
    Convert text to speech and stream the audio
"""
@app.route("/tts", methods=["POST"])
def convert_text_to_speech():
    try:
        # Example text to convert (replace with real input)
        input_text = "Hello, this is a test audio, I am fikrat, can you help with mathmetics!"  # Replace with dynamic content if needed

        # Prepare headers and data for Azure TTS API
        headers = {"api-key": key}
        data = {
            "model": "tts-hd",
            "input": input_text,
            "voice": "shimmer",
            "response_format": "wav",
        }

        # Call Azure TTS API
        response = requests.post(url, headers=headers, json=data, stream=True)

        if response.status_code == 200:
            # Stream the audio file back to the client
            return Response(
                response.iter_content(chunk_size=1024),
                content_type="audio/wav",
            )
        else:
            return Response(
                f"Error: {response.status_code} - {response.text}",
                status=response.status_code,
            )

    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)
    
if __name__ == "__main__":
    app.run(debug=True)
