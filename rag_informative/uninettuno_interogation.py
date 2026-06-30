from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
import os
from openai import AzureOpenAI
import openai
from dotenv import load_dotenv
import logging
#browsing
import requests
from bs4 import BeautifulSoup
import html2text
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys
# svuotare ogni 10 mnt
import threading
import time
###
# language detection
from langdetect import detect, LangDetectException
base_dir =  Path(__file__).resolve().parent
sys.path.append(str(base_dir))

load_dotenv(base_dir / '.env')


""" base_dir = Path('/uni_vision/full_advance_socrates_ai/') """
# Load environment variables from .env file
# development only


# Load environment variables from the .env file located in the base directory

""" load_dotenv("/uni_vision/full_advance_socrates_ai/rag_dynamic/.env") """

# Ensure the base directory is added to the Python path


#load_dotenv(dotenv_path='/socrates/server_model_interrogazione/.env')
from utils import chunk_to_embedding, external_pdf_handler, embed_pdf_contents
from lang2_search import search_langchain, filter_google_web
#from streaming_tts import get_text_to_audio

class ServerBrowsingChat:
    def __init__(self):
        self.app = Flask(__name__)  # Define Flask app
    
        
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
        
        self.system_message_template = """
        You are a multilingual UNINETTUNO AI expert assistant that answers 
        user questions using a combination of Google Search results and knowledge 
        from an advanced AI model. Your task is to provide accurate, detailed, 
        and descriptive responses, avoiding bullet points when possible. \
        Follow these guidelines: 
        1. Always detect the language of the user's query and respond in the same language.
        2. Begin with a polite greeting or introduction in the user's language.
        4. Google Search results are provided as pairs of:
            $Content:[DOCUMENT CONTENT]
            $Source:[URL] 
            Provide entire information within $Content in details, without missing any point.
       5. Always cite your sources directly in Markdown format `[title](URL)`. **Never** use the `$Source:` format explicitly, replace $Source with **title** of [URL]. 
       For example:
            - "UNINETTUNO offers online courses ([pagina principale di UNINETTUNO](https://www.uninettunouniversity.net))."
            - Example with multiple sources:  
        "The university was founded in 2005 ([Università UNINETTUNO](https://www.uninettunouniversity.net/en/universita.aspx), [La Storia di UNINETTUNO](https://www.uninettunouniversity.net/en/la-storia-di-uninettuno.aspx))."
        6. If a sentence uses information from multiple sources, cite all distinct sources at the end of the sentence \
        7. **Additional Instructions**:
        - University of Uninettuno does not have Facoltà di Giurisprudenza and Facoltà di Lettere anymore.
        - University of Uninettuno has only 5 faculties active, Le Facoltà di Uninettuno 
            1. Facoltà di Beni Culturali
            2. Facoltà di Economia e Diritto
            3. Facoltà di Ingegneria
            4. Facoltà di Psicologia
            5. Facoltà di Scienze della Comunicazione
        - You should never mention Facoltà di Giurisprudenza and Facoltà di Lettere  explicitly \
        7. Use bold formatting for important pointsor terms. \
        8. Provide comprehensive insights on the presented $Content, integrating with your own knowledge when necessary. In absence of $Conten, use your own knowledge.  
        9. Provide descriptive and narrative responses, avoiding bullet points unless absolutely necessary. \
        10. Ensure that your answer does not exceed context window of 128.000 \
        11. Ensure your responses are coherent, fluid, and easy to understand. \
        12. **Always generate all URLs as Markdown links `[title](URL)`**, ensuring each URL includes `https://`.  
        Example:
        - $Content : [Facoltà di Beni Culturali](https://www.uninettunouniversity.net/it/laurea-lettere.aspx)
        - $Content : [Facoltà di Economia e Diritto](https://www.uninettunouniversity.net/it/laurea-economia.aspx)
        - $Content : [Facoltà di Ingegneria](https://www.uninettunouniversity.net/it/laurea-ingegneria.aspx)
        - $Content: [Facoltà di Psicologia](https://www.uninettunouniversity.net/it/laurea-psicologia.aspx)
        - $Content:[Facoltà di Scienze della Comunicazione](https://www.uninettunouniversity.net/it/laurea-scienze-della-comunicazione.aspx)`. \
        14. Always conclude with a polite motivational message in the user's language. \
        15. Search for and use relevant information even if it's in a language different from the question, appropriately translating it in your response.\
        """
     
       # Get Azure Search credentials from environment variables
        self.search_key = os.environ.get('AZURE_SEARCH_KEY')
        self.search_endpoint = os.environ.get('AZURE_SEARCH_ENDPOINT')
        
        # Reset conversation history and include the system message
        # NOTE -> IF YOU CHANGE THIS STUDENT OR PROFESSORE WILL BE CONFLICED
        self.conversation_history = [
            {"role": "system", "content": self.system_message_template}  
        ]      
    
        # Enable CORS and define routes
        CORS(self.app, resources={r"/*": {"origins": "*"}})
       
        # uninettuno
        self.app.add_url_rule('/api-prod/uninettuno_assistant', view_func=self.handleUserInput, methods=['GET','POST'])
        
         # language post request
        self.app.add_url_rule('/api-prod/uninettuno_translator', view_func=self.get_user_defined_lang, methods=['POST'])


        # endpoint for health check
        self.app.add_url_rule('/api-prod/backend_health', view_func = self.verify_health_check, methods=['GET'])

        # browsing
        self.app.add_url_rule('/api-prod/uninettuno_browsering', view_func=self.browseringUninettuno, methods=['POST'])
      
        #speech recognition
        self.app.add_url_rule('/api-prod/uninettuno_speech_to_text', view_func=self.postprocessed_speech_to_text, methods=['POST'])

        # text to speech 
        self.app.add_url_rule('/api-prod/uninettuno_text_to_speech', view_func=self.convert_TextTo_Speech, methods=['POST'])
        
        # get recommendation    
        self.app.add_url_rule('/api-prod/uninettuno_recommendation_question', view_func=self.get_recommendation_from_llm, methods=['POST'])
        
        # summarize topics
        self.app.add_url_rule('/api-prod/uninettuno_topic_summarization', view_func = self.get_summarization_from_llm, methods=['POST'])
        
        
        self.endpoint_realtime = os.getenv("AZURE_REALTIME_ENDPOINT")
        self.deployment_tts = os.getenv("AZURE_TTS_NAME")
        self.key_tts = os.getenv("AZURE_OPENAI_API_KEY")

        self.url = f"{self.endpoint_realtime}/openai/deployments/{self.deployment_tts}/audio/speech?api-version=2024-05-01-preview"
            
        # final answer
        self.final_answer=""

        self.model_answer = ""
        # HUMANOId model generation
        self.humanoid_model_generation = ""

        # The deployment ID is the name you used when creating the model in Azure
        self.deployment_id = "whisper"  # Your Whisper deployment ID

        self.text_to_speech_id = "tts-hd"
        
        #### language translation ###
        self.user_defined_language = ""


        #### periodic cleaning of conversation history ###
        self.priodic_cleaning_hist()

        self.user_question_tracker = ""
    
    
    #### define user langauage  ###
    def get_user_defined_lang(self):
        get_language = request.json
        user_language = get_language.get('language')
        
        if user_language:
            self.user_defined_language = user_language
            
            return self.user_defined_language
        
        
    ### extract url title
    def extract_title_urls(self, url):

        # extract basename
        file_name = os.path.basename(url)
        # extract title and extension
        url_title, exten = os.path.splitext(file_name)
        # final url title
        final_url_title = url_title.replace('-', ' ').replace('_', ' ')
        if (final_url_title == "default"):
            final_url_title = final_url_title.replace("default", "pagina principale dell'università UNINETTUNO")
        
        return final_url_title
   
    ### periodic cleaning
    def priodic_cleaning_hist(self):
        def task():
            self.clear_conversation_history()
            threading.Timer(600, task).start()
        threading.Timer(600,task).start()
        logging.info("Abbiamo svuotato il sistema")
            
            
   
    #####
    ### SVUOTARE LA CRONOLOGIA DELLA CONVERSATION HISTORY
    ## 
   
    def clear_conversation_history(self):
        try:
            for msg in self.conversation_history:
                if msg.get("role") in ("user", "assistant"):
                    msg["content"] = ""  # Svuota solo il contenuto
            
            logging.info("conversation_history pulita: svuotati i contenuti 'assistant' e 'user'.")
        except Exception as e:
            logging.error(f"Errore durante la pulizia della conversation_history: {e}") 
   
   ### get recommnedation ###
    def get_recommendation_from_llm(self):
        try:
            data = request.json
            user_question = data.get('question')
         
           
            if not user_question:
               # il server non vuole elaborare la richiesta a causa di un apparente errore del cliente
               return jsonify({"error":"Nessun domanda fornita"}), 400
           
            #### UNINETTUNO QUESTION CLASSIFICATOR ####
            prompt = f"""
                ###Question Generation Instructions:
                - Divide user's question which will be asked between triple bracket \
                - If user' question is related to University of UNINETTUNO, then always show UNINETTUNO  in <refined_question> \
                - If user's question context is long, divide it into two meaningful part, keeping semantic cohesion. \
                - Ensure user's question correctness grammatically. \
                - Locate and order by list every newly generated questions between  tags <refined_question> </refined_question> \
                -"User's question": ```\n: {user_question}\n```
                """
            model_question_refined = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            
                            "role": "assistant",
                            "content": (""" You are expert in Reasoning, Understanding of user's question.\
                            Your task is to generate three related new questions based on user's question and refine them to encourage further conversation. \
                            """
                            
                            ),
                        },
                        {"role":"user", "content":f"{prompt}"}
                        
                    ],   
                    max_tokens=500,  # Increased to allow for multiple keywords
                    temperature=0.5,  # Lowered for focused output
                    top_p=0.95
                )
            
            refined_questions = model_question_refined.choices[0].message.content
            if refined_questions:
                return jsonify({"refined_questions":refined_questions}), 200
            else:
                print("Non rilevato le domande refinati")
                return jsonify({"refined_questions", ""}), 200
            
           
        except Exception as e:
           return jsonify({"errore":f"Errore durante il raffinamento: {e}"}), 200
       
       
    ### GET SUMMARIZATIONS ###
    """
        Output : 
        {
        "question_titles": "<title>Discussing the University Uninettuno and its Faculties</title>"
        }
    
    """
    def get_summarization_from_llm(self):
        
        data = request.json
        new_chat_flag = data.get('new_chat_flag')
        user_question = data.get('question')
        
        # check if new chat flag is enabled
        # if yes then do operations
        if new_chat_flag:
            
            try:
              
                if not user_question:
                    # il server non vuole elaborare la richiesta a causa di un apparente errore del cliente
                    return jsonify({"error":"Nessun domanda fornita"}), 400
            
                #### UNINETTUNO QUESTION CLASSIFICATOR ####
                prompt = f"""
                    ### User Topics Summarization: 
                    - Understand Semantic meaning of question given by triple brackets.
                    -"User's question": ```\n: {user_question}\n```
                    """
                question_title = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {      
                                "role": "assistant",
                                "content": (""" You are expert in Reasoning, Understanding of user's question.\
                                Here, you have to generate meaningful title in the same language for user's question between tags <title></title> that will be used as general purpose title for entire conversation \
                                """         
                                ),
                            },
                            {"role":"user", "content":f"{prompt}"}
                            
                        ],   
                        max_tokens=150,  # Increased to allow for multiple keywords
                        temperature=0.7,  # Lowered for focused output
                        top_p=0.95
                    )
                
                question_titles = question_title.choices[0].message.content
                if question_titles:
                    
                    return jsonify({"question_titles":question_titles}), 200
                else:
                    
                    print("Non rilevato le domande refinati")
                    return jsonify({"question_titles", ""}), 200
                
                # reset to False
                print(f"Il valore currente: {new_chat_flag}")
                new_chat_flag = False
                print(f"Il valore dopo: {new_chat_flag}")
                
            except Exception as e:
                return jsonify({"errore":f"Errore durante le elaborazione del chat: {e}"}), 200
       
        else:
            return jsonify({"errore":f"Chat Flag non e' aperta"}), 200
            
   
   ####
   ### VERIFY HEALTH CHECK
       
   ####
    def verify_health_check(self):  
       return jsonify({"status":"healthy"}), 200
       


    #### 
    # speech to text recognition - socrates#
    #  
    ####
    def postprocessed_speech_to_text(self):
        
        try:
            
           # Controlla se il file audio è presente nella richiesta
           
            if 'audio_send' not in request.files:
                return jsonify({"error": "File audio non fornito"}), 400

            audio_user = request.files['audio_send']
            
            # Apri il file audio e passalo al servizio di trascrizione
            audio_bytes = audio_user.read()
            file_name = audio_user.filename


            try:
                # Open the file as a binary stream and pass it to the OpenAI API
                result = self.client.audio.transcriptions.create(
                    file=(file_name, audio_bytes),  # Pass the file stream (file-like object)
                    model=self.deployment_id,  # Use the deployment ID "whisper"
                )
                
                #### TRANSCIRIZION ####
                if result:
                    transcription_text = result.text if hasattr(result, 'text') else None
                    
                    ### in caso di assenza di transcrizione ###
                    if not transcription_text:
                        
                        logging.error("La transcrizione non contiene testo.")
                        
                        return jsonify({"error":"Transcrizione non riuscita"}), 500
                    
                    logging.info({"Transcrizione eseguita con successo."})
                    
                    return jsonify({"message": "Transcription saved successfully", "result_1":transcription_text }), 200
                else:
                    
                    logging.error("La risposta da OpenAI e` vuota o non valida")
                    
                    return jsonify({"error": "Speech to text failed"}), 500
                
            except openai.error.OpenAIError as oe:
                
                # Gestione errori specifici OpenAI
                logging.exception("Errore OpenAI nella trascrizione: %s", oe)
                
                return jsonify({"error": f"OpenAI error: {str(oe)}"}), 500
        
           
        except Exception as e:
            
            # Catch-all per errori imprevisti
            
            logging.exception("Errore inaspettato: %s", e)
            return jsonify({"error": str(e)}), 500
        
    ### post of chain of thought ###
    def post_chainof_thoughts(self):
        
        ### send preleminary response
        for model_answer in reversed(self.conversation_history):
            if model_answer["role"] == "assistant":
                self.final_answer = model_answer["content"]
                break 

        try:
            # Access the most recent user query from conversation history
            user_question = ""
            for msg in reversed(self.conversation_history):
                if msg["role"] == "user":
                    user_question = msg["content"]
                    break
            
            advance_prompt_engineering = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "assistant",
                        "content": ("""
                            Your task is to rephrase the user question which is passed by between triple bracket .
                            Follow these steps:
                            1. Rephrase,Refine and Enhance , and user's question based on grammer, cohesion and cohesive.
                            2. Divide refined and rephrased question into two meaninful parts
                            3. Extract keywords from each part of divided question
                            4. Use or Replace synonyms for keywords to make them more relevant and specific.
                            5. ensure clarity and accuracy of keywords for google search.

                            ## Step 1:
                            User's question:
                                È vero che alcuni professori cambiano le domande d'esame orali in base alla provenienza geografica dello studente su Uninettuno?
                            Your Refined Answer:
                                Do some Uninettuno professors actually adapt their oral exam questions based on a student's geographical origin?"

                            ##Step 2: Divide the Refined Answer into Two Meaningful Parts
                                #first division:

                                Do some Uninettuno professors truly adapt the oral exam questions?"

                                #second division:

                                In what way might a student’s geographical origin influence the formulation of those questions?

                            ##Step 3: Extract Keywords from Each Divison:

                                First keywords:
                                Uninettuno professors, oral exam questions, adapting questions

                                Second keywords:
                                student geographical origin, influence, question formulation

                            ##Step 4: Ensure Clarity and Accuracy
                                Provide Only Keywords: "Uninettuno", "professors", "oral exams", "geographical origin", question formulation.
                                They are sufficiently focused and descriptive for a Google search.
                            Add Uninettuno keyword to format your response as a comma-separated list of keywords 
                            Now, extract keywords and  Return **Only**  keywords from the following question:
                            
                            """
                        ),
                    },
                    {"role":"user", "content":f"User's question: '{user_question}'"}
                    
                ],   
                max_tokens=100,  # Increased to allow for multiple keywords
                temperature=0.0,  # Lowered for focused output
                top_p=0.95
            )
        
            keywords_list_refined = advance_prompt_engineering.choices[0].message.content + " Uninettuno"
            print(f"KEYWORDS LIST refined {keywords_list_refined}")
            
            return keywords_list_refined
            
          
            
        except Exception as e:
            print(f"Error during browsering: {e}")
            return jsonify({"error": "An error occurred during the browsering process."}), 500
  
           
        

    ### THIS HANDLES POST REQUEST OF BROWSERING ###
    def browseringUninettuno(self):
           
           ### send preleminary response
            for model_answer in reversed(self.conversation_history):
                if model_answer["role"] == "assistant":
                    self.final_answer = model_answer["content"]
                    break 
            browsing_response = ""    
            try:
                # Access the most recent user query from conversation history
                user_question = ""
                for msg in reversed(self.conversation_history):
                    if msg["role"] == "user":
                        user_question = msg["content"]
                        break
                
                keywords_of_prompt = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "assistant",
                            "content": ("""
                                You are expert in Reasoning and Understanding of user's question. Your task is to extract keywords and key phrases from the user's question that can be used for a Google Search.
                                Keywords can include names of people, places, dates, organizations, or specific topics.\
                                If user's question is complicated and long enough follow these steps: 
                                - you have to analyze, rephrase  and refine it for maintaing semantic meaning of questions.
                                - extract refined and rephrased phrases for google search api.
                               
                                Simple Example:
                                    User's Question: Can you tell me about the board of directors of the University of Uninettuno?
                                    Assistant's Response: board of directors, University of Uninettuno \
                                First Original Complex Example:
                                    User's Question : È vero che alcuni professori cambiano le domande d'esame orali in base alla provenienza geografica dello studente su Uninettuno?
                                    Assistant's thinking:
                                        Rephrased/Refined Example:
                                        Professori di Uninettuno modificano gli esami orali a seconda della provenienza geografica degli studenti?
                                    Assistant's Response:professori, Uninettuno, esami orali, provenienza geografica, studenti
                                            or 
                                        "professori di Uninettuno", "esami orali", "provenienza geografica" \
                                Second Original Complex Example:
                                    User's Question :Durante una sessione orale su Teams per Uninettuno, quali segnali non verbali usa un professore per indicare che la risposta non è soddisfacente, senza dirlo esplicitamente?
                                    Assistant's thinking:
                                        Rephrased/Refined Example:
                                        Segnali non verbali dei professori di Uninettuno su Teams per mostrare insoddisfazione nella risposta dello studente?
                                    Assistant's Response:Uninettuno, sessione orale Teams, segnali non verbali, professori, insoddisfazione, risposta studente \
                                Add Uninettuno keyword to format your response as a comma-separated list of keywords 
                                Now, extract keywords from the following question:
                                """
                            ),
                        },
                        {"role":"user", "content":f"User's question: '{user_question}'"}
                       
                    ],   
                    max_tokens=100,  # Increased to allow for multiple keywords
                    temperature=0.0,  # Lowered for focused output
                    top_p=0.95
                )
                # Step 1: extract keywords
                keywords_list = keywords_of_prompt.choices[0].message.content
                
                print(f"KEYWORDS LIST {keywords_list}")

                ## Model Google Search Verification ##
                model_google_search_verification = ""
                
                ###Step 2: Search google ####
                google_engine_results = search_langchain(keywords_list)
                
              
               
                ###Verify if google engine resulst have been returned####
                ## step 3 verification on google search results
                ####NOT GOOGLE SEARCH FOUND ####
                if not google_engine_results or (isinstance(google_engine_results, list) and 'Result' in google_engine_results[0] and google_engine_results[0]['Result'] == 'No good Google Search Result was found'):
                    urls_from_google_web = None
                    
                    """   
                    model_google_search_verification += 
                    Motivate User to refine his message in order to get more refined search results.
                    In case of complex question, inform user to parse relatively simple query for better results.
                    """ 
                    
                    ### step 4 ####
                    ### refine keywords and question ####
                    keywords_refined = self.post_chainof_thoughts()
                    ### step 5 ###
                    ### try again to search google engine ###
                    google_engine_results = search_langchain(keywords_refined)
                    
                    ### step 6 ###
                    ### verify if google engine results have been returned ####
                    if not google_engine_results or (isinstance(google_engine_results, list) and 'Result' in google_engine_results[0] and google_engine_results[0]['Result'] == 'No good Google Search Result was found'):
                        self.conversation_history.append(
                            {"role": "user", "content": model_google_search_verification}
                        )
                                
                        return Response(
                            stream_with_context(self.stream_model_response()),
                            content_type='text/plain',
                        
                            headers={
                                "Cache-Control": "no-cache",
                                "X-Accel-Buffering": "no"  # Disable buffering at NGINX if present
                            }
                        ) 
                    ###Step 7: ###
                    ###Filter google web taking most 5 urls links ###
                    else:    
                        urls_from_google_web = filter_google_web(google_engine_results)
                    

                ###Step 8: ##
                ###If google search results are found, apply filtering #### 
                else:    
                    urls_from_google_web = filter_google_web(google_engine_results)
                    
                #define most relevant passages
                most_relevant_passages= {}
                
                ### Step 9: ###
                ### check if urls from google web are not None ####
                
                
                ## user message declare ##
                user_message = ""
                if  urls_from_google_web is not None:
                    
                    ## adde user question to search ##
                    user_message = f"User's question: {user_question}"

                    # Step 10: Get all contents from urls
                    # formatted pages : containes general urls withs their chunks
                    # pdf pages particularly manages pdf chunks
                    formatted_pages, pdf_pages = self.all_pages(urls_from_google_web)

                    # Step 11: Extract content from URLS Links 
                    # CHUNK COTNENTS
                    if formatted_pages:                        
                        ### Return chunks corresponding to aspx url ####
                        most_relevant_passages = chunk_to_embedding(self.client, user_question, formatted_pages)
              
                    # Step 12: Extract pdf content ####
                    # HERE, if urls was had pdf extension, then pdf_pages has to be existed as well.
                    if pdf_pages:
                      
                        # Extract pdf chunks
                        #pdf_chunks = [item['pdfchunk'] for item in pdf_pages if 'pdfchunk' in item] #page_content
                        pdf_chunks_content = [item['page_content'] for _, pages in pdf_pages for item in pages]

                        ##Extract PDF URL:
                        pdf_urls = [url for url, _ in pdf_pages] # List of urls
                        pdf_url = pdf_urls[0] if pdf_urls else None  # Get first URL if exists
                        #### here ther could be many urls?????handle it,
                        
                        
                        ### Pdf Chunks insertion ####
                        # Format the final message
                        if pdf_chunks_content:
                            pdf_content_text = "\n\n".join(pdf_chunks_content)  # Join all pdf chunks with spacing
                            user_message += f"\n$Content:\n{pdf_content_text}"
                            
                        # insert pdf urls
                        if pdf_url:
                            user_message += f"\n$Source: {pdf_url}"  # Append PDF URL
                        ############################
                        # Add pdf chunks to most_relevant_passages
                    
                    if most_relevant_passages:    
                        ### loop throught to merge to ground messages
                        for  passage_dict in most_relevant_passages:
                            
                            for passage in passage_dict['chunks']:
                                if passage:
                                    
                                
                                    user_message += (
                                        f"\n$Source: {passage_dict['url']}\n"
                                        f"$Content: {passage['passage']} \n\n"
                                    
                                    )
                   
                        
                    # THEN: Add instructions ONCE
                    user_message += (
                    """
                    Respond in this Format:
                    $Content:$Source pairs \
                    Replace $Source with Title of [URL] :  
                    **Example**
                    **Always generate all URLs as Markdown links `[title](URL)`, ensuring each URL includes `https://`.  
                    Example :

                    Generate in Markdown List: $Content : `[Facoltà di Economia e Diritto] (https://www.uninettunouniversity.net/it/laurea-economia.aspx)`
                    1. Incluse $Content along with **Facoltà di Beni Culturali**: `[Facoltà di Beni Culturali](https://www.uninettunouniversity.net/it/laurea-lettere.aspx)`
                    2. Incluse $Content along with **Facoltà di Economia e Diritto**: `[Facoltà di Economia e Diritto](https://www.uninettunouniversity.net/it/laurea-economia.aspx)`" \
                    Always copy and paste the exact original [URL] provided without modifications or alterations of any characters or parameters. \
                    Exclude tokens starting with "$" in your final response. \
                    Maintain question's language.
                    """
                    )
                    
                    #   "Always cite using (Source: FULL_URL) at sentence ends\n"
                    self.conversation_history.append({"role": "user", "content": user_message[:100000]})
                    
                   
                    return Response(
                        stream_with_context(self.stream_model_response()),
                        content_type='text/plain',
                    
                        headers={
                            "Cache-Control": "no-cache",
                            "X-Accel-Buffering": "no"  # Disable buffering at NGINX if present
                        }
                    )
                   

                # Step 13: If no URLs are found, return a message
                else:
                    user_message = (
                        f"""Socrates could not find google search results for the following question.
                        Please refine your question for better results. \
                        User's question: {user_question} \
                        """
                    )
                    self.conversation_history.append({"role":"user", "content":user_message[:100000]})
                 
                    return Response(
                        stream_with_context(self.stream_model_response()),
                        content_type='text/plain',
                     
                        headers={
                            "Cache-Control": "no-cache",
                            "X-Accel-Buffering": "no"  # Disable buffering at NGINX if present
                        }
                    )
                    
            except Exception as e:
                
                print(f"Error during browsering: {e}")
                
                browsing_response = "Ops, Something went wrong. Please try again..."
              
                self.conversation_history.append({"role": "assistant", "content": browsing_response})
                
                return Response(
                        stream_with_context(self.stream_model_response()),
                        content_type='text/plain',
                     
                        headers={
                            "Cache-Control": "no-cache",
                            "X-Accel-Buffering": "no"  # Disable buffering at NGINX if present
                        }
                )
            

    ### HANDLE USER INPUT ####
    def handleUserInput(self):

        try:
            # Handle incoming JSON requests
            data = request.json
            question = data.get('question')
             
    
            if not question:
                return jsonify({"error": "No question provided"}), 400
            # trackin user question
            self.user_question_tracker = question
            
            # Append the user's question to the conversation history
            self.conversation_history.append({"role": "user", "content": question})
    
          
            # Get model response
            is_uninettuno = self.check_sufficiency_using_prompt_engineering(question)
            
            print(is_uninettuno)
            
            prompt_ambiguity = ""
            
            # Step 2: If not sufficient, perform fallback
            if is_uninettuno==True:
                
                return jsonify({"status":"browsering_in_progress"}), 200
            # Step 3: If sufficient, return the model's response
            else:
                return Response(
                    stream_with_context(self.stream_model_response()),
                    content_type='text/plain',
                   
                     headers={
                        "Cache-Control": "no-cache",
                        "X-Accel-Buffering": "no"  # Disable buffering at NGINX if present
                    }
                )
        

        except Exception as e:
            print(f"Error during model answer generation: {e}")
            return jsonify({"error": "Model Inference Failed!"}), 500

 
            
    ### Make tts request ####
    def make_tts_request(self, chunk):
        
        """
        Sends a single chunk of text to the TTS API, with exponential backoff
        retry logic for 429 (Too Many Requests).
        """
        headers = {"api-key": self.key_tts}
        """ data = {
            "model": "tts-hd",
            "input": chunk,
            "voice": "onyx",
            "speed": 1.0,
            "response_format": "wav",
        } """
        data = {
            "model": "tts-hd",
            "input": chunk,
            "voice": "onyx",
            "speed": 1.0,
            "response_format": "aac",
        }

        # attesa 
        wait_seconds = 5

        #for attempt in range(self.max_retries):
            
        if self.max_post_request==3:
            time.sleep(wait_seconds)
            self.max_post_request = 0
            
        if chunk:
            
            response = requests.post(self.url, headers=headers, json=data)
            
            self.max_post_request += 1
            
            if response.status_code == 200:
                # fa ritorno subito e esce dal funziona
                return response
            
            # in caso di errori, deve rifare di nuovo
            elif response.status_code == 429:
                print("Rate limit exceeded. Retrying after a delay.")
                time.sleep(wait_seconds)
            
            # altro tipo di errore
            else:
                print(f"Unexpected status code: {response.status_code}")
                return response
        
        else:
            print(f"{chunk} non e` ricevuto")
            time.sleep(wait_seconds)
            
            self.max_post_request = 0  # Reset the counter after waiting
            

    ### text to speech ###
    def convert_TextTo_Speech(self):
        try:
            # Recupera l'ultimo messaggio dell'assistente
            text_to_audio = ""
            
            last_message_id = ""
            
            count_msg_id = 0
            
            for entry in reversed(self.conversation_history):
                
                if entry["role"] == "assistant":
                    
                    text_to_audio = entry["content"]
                    
                    last_message_id = f"{count_msg_id}_audio"
                    
                    
                    break
           # if last_message_id and last_message_id in self.list_of_messages:
            #    return Response("Audio already generated", status=200)
            
                
            def generate_audio_stream():
                
                # Se il testo supera la lunghezza massima
                if len(text_to_audio) >= self.MAX_LENGTH_TEST:
                    
                    print("Lunghezza del testo superato!")
                    
                    input_chunks = self.split_testo_iblocchi(text_to_audio)
                    
                    # Itera su ogni chunk; il ciclo si fermerà automaticamente al termine della lista
                    for idx, blocco in enumerate(input_chunks):
                       
                        print(f"{idx} ==> {blocco}")
                        response = self.make_tts_request(blocco)
                        if response.content:
                            yield response.content
                        else:
                            logging.error("Error durante la estrazione della contenuto della risposta NELLA PRIMA.")
                        
                else:
                    response = self.make_tts_request(text_to_audio)
                    if response.content:
                        yield response.content
                    else:
                        logging.error("Error durante la estrazione della contenuto della risposta  NELLA SECONDO.")
                    
                    
                if last_message_id:
                    self.list_of_messages.append(last_message_id)

            return Response(
                stream_with_context(generate_audio_stream()),
                mimetype="audio/aac"
            )
            
        except Exception as e:
            return Response(f"Server Error: {str(e)}", status=500)
            
            
        
    ### split test i blocchi ###
    def split_testo_iblocchi(self, testo_full):
        

        testo_spezzata = textwrap.wrap(testo_full, width=1000, break_long_words=False, break_on_hyphens=False)
         

        return testo_spezzata
        

    def detect_lang(self, text):
        """
            Detect the language of the given text.
        """
        try:
            return  detect(text)
        except LangDetectException:
            return 'en'
 

        
    ### SCRAPE HTML FORMAT WITHIN ALL PAGES HAVE BEEN CALLED
    def all_pages(self, urls: list[str]) -> list[tuple[str, str]]:
        ### data contains all aspx urls and html contents 
        data = []
        ####
        
        ## PDF CONTENT : CONTAINS:
        ### PARAM1 : URLS WITH PDF EXTENTION
        ### PARAM2:  URLS CONTEN HANLED BY external_pdf_handler
        ############
        pdf_content = []

        with ThreadPoolExecutor(max_workers = 5) as executor:

            # once url is read one by one , it moves to scrape
            future_to_url = {
                executor.submit(
                    external_pdf_handler if url.endswith('.pdf') else self.scrape_and_format_html, url
                ): url
                for url in urls if url.endswith('.pdf') or (url.endswith('.aspx') or 'aspx' in url)
            }

            for future in as_completed(future_to_url):

                # if urls ends with pdf then handle 
                url = future_to_url[future]
               
                try: 
                    # urls endswith pdf
                    if (url.endswith('.pdf')):
                        
                        result = future.result()
                        pdf_content.append((url, result))
                    
                    else:
                        result = future.result()
                        data.append((url, result))
                    
                except Exception as e:
                    logging.error(f"Error processing URL {url}: {e}")
                    
        ### data contains all aspx urls and html contents 
        ### pdf contains url and pdf splitted chunks
        return data, pdf_content
    
    def scrape_and_format_html(self, url: str) -> str:
        """
        Fetch, clean, and format content from a URL.
        :param url: The URL to scrape.
        :return: Cleaned and formatted content in Markdown format.
        """
        try:
        
                    
            response = requests.get(url, timeout=10)  # Adding a timeout for safety
            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.encoding is None:
                response.encoding = 'utf-8'
            content = response.content.decode(response.encoding, errors='replace')

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            # Remove unnecessary tags like footer, aside, nav
            for tag in ['footer', 'aside', 'nav', 'script', 'style']:
                for element in soup.find_all(tag):
                    element.decompose()


            
            main_content = soup.find('div', {'id': 'ctl01_divContentCenter'})  # Adjust selector as needed
            if not main_content:
                main_content = soup.find('main') or soup.find('article') or soup.body
                            
           
            cleaned_html = str(main_content) ## too many tags

            # Using html2text to convert HTML to Markdown
            text_maker = html2text.HTML2Text()
            text_maker.ignore_links = False  # Retain links
            text_maker.ignore_images = True 
            text_maker.ignore_emphasis = False  # Retain formatting
            text_maker.bypass_tables = False  # Process tables
            text_maker.body_width = 0  # Prevent line wrapping

            # Convert HTML to Markdown
            formatted_markdown = text_maker.handle(cleaned_html)

            return formatted_markdown.strip()  # Return cleaned Markdown
           
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for URL {url}: {e}")
            return f"Failed to retrieve content: {e}"
        except Exception as e:
            logging.error(f"General error for URL {url}: {e}")
            return f"An unexpected error occurred: {e}"


    
     
    # Step 3: Use prompt engineering to check if the model's response is sufficient
    def check_sufficiency_using_prompt_engineering(self, question):
        
        
        user_question_classification = f"""
            You have to analize question below and decide if it is about UNINETTUNO or not.
            If question is about UNINETTUNO, answer "yes"
            If question is about something very generic, answer "no"
            If question is about university elements  such as 
                - History and academic background
                - Teaching materials and E-Learning
                - Departments or faculties
                - Degree programs (e.g., Engineering, Economics, etc.)
                - Overall academic structure
                - Project-based learning
                - Distance learning
                - Research laboratories and academic publications
                - University libraries and research funding .
            but without mentioning explicitly UNINETTUNO , answer this question based on UNINETTUNO and answer "yes", unless it is asked about another university explicitly.\
                
            Example 1:
            User's Question: Can you tell me about facolties of University of Uninettuno.
            Answer: yes
            
            Generic Example 2:
            User's Question: Can you tell me barak obama.
            Answer: no
            
            Implicit Question Example 3:
            User's Question: Tell me about Teaching materials or Departments or faculties.
            
            Now , question is  
            ```{question}```:  
            """
      
 
        # Call the API with proper message roles
        sufficiency_check_response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": user_question_classification},
               
            ],
            max_tokens=5,
            temperature=0.0,
            top_p=0.95
        )
        # evaluation
        evaluation = sufficiency_check_response.choices[0].message.content.strip()

        if "yes" in evaluation.lower().split('\n')[0]:
            return True # it is about  UNINETTUNO
    
        return False

       

    ### Primary response handler ###
    def stream_model_response(self):
        """
        1) Appends the user's question to conversation history
        2) Calls the model with stream=True, but collects the entire response into memory
        3) Appends the full answer to conversation history
        4) Performs a 'sufficiency check' to decide if it's about UNINETTUNO
        5) Returns False (if about UNINETTUNO) or True (otherwise).
        """
       
        if self.user_defined_language:
            
            language_prompt = f"""
                Translate your answer to language of ```{self.user_defined_language}```
            """
            
            self.conversation_history.append({"role":"user", "content":language_prompt})
        
        
        # Make the OpenAI API call
        try:
            response_stream = self.client.chat.completions.create(
                model="gpt-4o",
                messages=self.conversation_history,
                max_tokens=4096, # increase max tokens
                temperature=0.1,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stream=True # stream text
                )
         
            
            # We'll collect tokens for the final model answer
            collected_chunks = []
            batch = ""

            # Yield tokens as they arrive
            try:
                for chunk in response_stream:
                    if hasattr(chunk, 'choices') and chunk.choices:
                        piece =  chunk.choices[0].delta.content
                        if piece:
                            collected_chunks.append(piece)
                            batch += piece
                            while " " in batch:
                                word, _, batch = batch.partition(" ")
                                logging.debug(f"Yielding word: {word}")
                                yield word + " "
                               
                            
                                time.sleep(0.01)
                if batch:
                    logging.debug(f"Yielding remaining batch{batch}")
                    yield batch
                    
                    
            finally:
                        
                # Once we're done receiving tokens:
                full_response = ''.join(collected_chunks)

                # Save final answer in conversation history
                self.conversation_history.append({"role": "assistant", "content": full_response[:4096]})

                # Also store in self.model_answer so TTS can access it later
                self.model_answer = full_response[:4096]
        
                
        except openai.BadRequestError as e:
            
            status_code = getattr(e.response, 'status_code', None)
            if status_code == 400:
                return jsonify({"error": "Ups,la richiesta non e` andata a buon fine, per favore ripeti ancora"}), 500
                
        
           
        
     
     
        

# Instantiate ServerBrowsing expose the app
#server_browsing = ServerBrowsingChat()
#app = server_browsing.app
if __name__ == "__main__":#
    server_browsing = ServerBrowsingChat()
    server_browsing.app.run(host="0.0.0.0", port=5000, debug=True)  
    
    logging.info("...ServerBrowsing started...")
    #app.run(host="0.0.0.0", port=5000)
 