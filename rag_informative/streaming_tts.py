import os
from time import sleep
import wave
import requests
import pyaudio
from dotenv import load_dotenv

###### Load environment variables

####################################################
endpoint = os.getenv("AZURE_REALTIME_ENDPOINT")
deployment = os.getenv("AZURE_TTS_NAME")
key = os.getenv("AZURE_OPENAI_API_KEY")
###################################################

url = f"{endpoint}/openai/deployments/{deployment}/audio/speech?api-version=2024-05-01-preview"
"""
    CONVERT TEXT TO AUDIO
"""
def get_text_to_audio(input_user):
    headers = {"api-key": key}
    data = {
        "model": "tts-hd",
        "input":input_user,
        "voice": "onyx",
        "response_format": "wav",
    }
    
    response = requests.post(url, headers=headers, json=data, stream=True)

    CHUNKS_SIZE=1024
    if response.status_code == 200:
        with wave.open(response.raw, 'rb') as wf:
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            input_device_index=11,
                            rate = wf.getframerate(),
                            output=True)
            
            while len(data := wf.readframes(CHUNKS_SIZE)): 
                stream.write(data)
            sleep(1)
            stream.close()
            p.terminate()
            
    else:
        response.raise_for_status()
        
