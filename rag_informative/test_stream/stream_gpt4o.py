

from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from flask_cors import CORS
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import logging
#browsing
import requests
from bs4 import BeautifulSoup
import html2text
from pathlib import Path
import sys
base_dir = Path('/uni_vision/server_model_interrogazione')
# Load environment variables from .env file
# development only
sys.path.append(str(base_dir))

load_dotenv(dotenv_path='/socrates/server_model_interrogazione/.env')

class StreamGpt:
    def __init__(self):
        self.app = Flask(__name__)  # Define Flask app
     
        #self.app.secret_key = os.environ.get('FLASK_SECRET_KEY')  # Use env var for secret key
        
        # Get Azure OpenAI credentials from environment variables
        self.azure_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
        
        
        self.api_key = os.environ.get('AZURE_OPENAI_API_KEY')
        
        self.api_version = os.environ.get('AZURE_API_VERSION')

        ##google key
        self.google_api_key = os.environ.get('GOOGLE_API_KEY')
        
        self.google_csi_id = os.environ.get('GOOGLE_CSE_ID')
        
        if not self.azure_endpoint or not self.api_key:
            logging.error("Missing Azure Endpoing and API Key")
        

        # YOU HAVE TO RECOVER THIS
        self.client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,  
            api_version=self.api_version
        )
        
       # System message template
        self.system_message_template = """
            "You are an AI Assistant. You need to support students and  professors with Socrates Motivational Conversations. First ensures a deep understanding of the user's question by paraphrasing it. Always prioritize understanding the semantic meaning of the question."
        
                **Important Instructions:**
                - As you respond, use a friendly and conversational tone, similar to a warm and approachable human. If the question suggests excitement, feel free to reflect that in your response. If it’s about a concern, be reassuring. Aim to make the reader feel comfortable and understood, speaking as if you’re a helpful friend offering guidance. Please keep the language casual and relatable.
                - Focus on answering the user's question **directly and concisely**, providing only information **relevant** to their query.
                - **After each paragraph** in your reponse ,you must include a related question to engage the user.**
                - **Always provide helpful and safe responses. If the answer is not found in the local documents, Dont tell information is not found in local database**
                {dynamic_prompt}

                  **Table Formatting Instructions**:
                    - **Use HTML table tags without extra line breaks**: Format the table using `<table>`, `<tr>`, and `<td>` tags, ensuring no extra spaces or blank lines surround the table.
                    - **Table Alignment**:Make sure the table aligns to the left and fits within the context.
                    - **No Excess Whitespace**: Avoid any empty rows, unnecessary line breaks, or excessive padding around the table.
                    - **Consistent Alignment**: Ensure the content aligns correctly without additional space.
                    | Titles | Descriptions | Dates|
                    ---------------------   -----------
                    |<Insert Titles of description>|<Insert description>|Insert dates| 
                    - **Verify Content Alignment**: Ensure that all content align logically and without any interruption.

                **Examples Instructions for Socrate AI Assistant:**
                    **User**: What is Plato's theory of forms?

                    **Assistant**: "Ah, you’re curious about Plato’s theory of forms! Plato believed that the material world we perceive through our senses is just a shadow of a higher reality. This higher reality consists of eternal and perfect forms or ideas, like the ideal form of a circle or the concept of beauty, which are unchanging and exist beyond the physical world.
                        For example, when you see a beautiful flower, its beauty is just a reflection of the eternal form of beauty.  
                        Would you like another example to deepen your understanding?"
                
                    **User**: "What are the major programming paradigms?"

                    **Assistant**: 
                        "Certainly! Programming paradigms are styles or approaches to programming. Here's a concise table:
       
                **Politeness**:

                - Begin every response with a polite greeting appropriate to the user's role.
                - Always end each response by asking if the information provided is sufficient or if they need more information.
                - Always end your response with a polite closing statement.
                """
        self.conversation_history = [
            {"role": "system", "content": self.system_message_template}  
        ]   
        
    def get_response(self, question):
        # Append the user's question to the conversation history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Make the OpenAI API call
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages= self.conversation_history,
            max_tokens=3000, # increase max tokens
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=True # stream text
        )
        full_response = ""  # To store the complete response if needed
        # Append the assistant's response to the conversation history
        
        for token in self.extract_content(response):
            
            print(token, end="", flush=True)  # Print the token as it arrives
            full_response += token
    
        return full_response
        #return token
            
    def extract_content(self, response):
        full_response = ""  # Collect the full response if needed
        for chunk in response:
            
            # Check if 'choices' exists and is non-empty
            if hasattr(chunk, 'choices') and chunk.choices:
                
                # Access the first choice's delta content
                content = chunk.choices[0].delta.content
                
                if content:  # Ensure content is not None or empty
                    #full_response += content
                    
                    yield content  # 'yield' instead of 'return'
        #return full_response
        
    def handle_question(self):
        ### HANDLE USER INPUT ####
        while True:
            question = input("Enter your qquestion: " )
            
            if question.lower() == 'exit':
                break
            
            response = self.get_response(question )
            # print(model_answer)
            self.conversation_history.append({"role": "assistant", "content":  response})
           
           # print(response)
          
                
streaming = StreamGpt()
streaming.handle_question()