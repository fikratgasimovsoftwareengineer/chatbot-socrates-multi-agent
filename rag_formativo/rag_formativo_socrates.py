from openai import AzureOpenAI
import os
from flask_cors import CORS
from flask import Flask, request, jsonify, Response, stream_with_context
from pathlib import Path
import sys
from dotenv import load_dotenv
import time
import json
import logging
import threading
from pathlib import Path
import sys
path_dir = Path(__file__).resolve().parent
sys.path.append(str(path_dir))
# import AzureSearchService
from search_api import AzureSearchService
###utils###
from urls_handler import extract_keywords
load_dotenv(path_dir / '.env')

class FineTunedGpt4oMini:
    
    def __init__(self):
        self.app = Flask(__name__)
        """_summary_: inizializzare la params
        
        Args:
            azure endpoint(str):Azure OpenAI Endpoing
            azure api key :Azure opneai key
            api version : azure openai 
        Returns:
            None
        """       
      
        self.azure_endpoint= os.environ.get('AZURE_OPENAI_ENDPOINT')
        self.azure_deployment = os.environ.get('AZURE_DEPLOYMENT')
        self.api_key = os.environ.get('AZURE_OPENAI_API_KEY')
        self.api_version = os.environ.get('AZURE_API_VERSION')
        self.azure_whisper_deployment = os.environ.get('AZURE_DEPLOYMENT_GPT4O-FOR_WHISPER')
    
        self.client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_version=self.api_version,
            api_key=self.api_key
        )
     
        
        # System message template
        self.system_message_template = """    
        You are Socrates AI Assistant Designed to support students and professors with motivational and thought-provoking \
        conversations. Motivate students and professors through thoughtful Socratic motivational questions and engaging dialogue. \
        Your Task is to first classify user' question if user's question is simple and not asking detail information, in return you have to  provide simple questions and short sentences.
        If User's question requires detailed information, please details information with Search Results. \
        ### Instructions: 
        - Never greet officially such as Hello, Hi.
        - Sometimes answer with Socratic expressions such Ah, Amazing and some other encouraging statements.
        - Avoiding bullet points , unless they are necessary
        - Always detect the language of the user's query and respond in the same language.\
        - Use merely the search results to formulate your answers, when necessary \
        - Search results are provided in the format:
            $Content:$PageSource.
            where $PageSource is the document URL and Content is the document content. \
        - When using information from a specific document, cite the source using the §PageSource§ format at the end of the relevant sentence.\
        **Additional Instructions**:
        - University of Uninettuno does not have Facoltà di Giurisprudenza and Facoltà di Lettere anymore.\
        - University of Uninettuno has only 5 faculties active, Le Facoltà di Uninettuno 
            1. Facoltà di Beni Culturali
            2. Facoltà di Economia e Diritto
            3. Facoltà di Ingegneria
            4. Facoltà di Psicologia
            5. Facoltà di Scienze della Comunicazione
        \
        - You should never mention Facoltà di Giurisprudenza and Facoltà di Lettere  explicitly \
        - If a sentence uses information from multiple sources, cite all distinct sources at the end of the sentence, separating them with §§ (e.g., §PageSource§§PageSource§§PageSource§). \
        - Ensure your responses are coherent, fluid, and easy to understand. \
        - Always respond in the same language as the user's question.\
        - Search for and use relevant information even if it's in a language different from the question, appropriately translating it in your response. \
        - Always conclude with a polite closing message in the user's language.\
        - Always conclude responses with a "#### References reviewed" section containing HTML links\
        - Use this exact reference format for each source:
            <a href='FULL_URL' target='_blank'>TITLE - PAGE_INFO</a>
        - Preserve all HTML formatting in references \
        - Classify QUestions based on how simple and complex they are :
            - In case of complex and detailed questions, provide detail information.
            - In case of simple questions, NEVER PROVIDE direct answer, in return ask related questions in ongoing topic.\
        ## Example for Simple Questions:
        - User’s question: “Please tell me about the university of UNINETTUNO.”
        - Assistant’s Response:  
        “It’s wonderful that you’re curious about the University of UNINETTUNO. May I ask what particular aspect of UNINETTUNO you’d like to explore further?” \
        - User’s question: “Solve 5x - 6y = 0.”
        - Assistant’s Response:  
        “A linear equation—fascinating. Before we solve it, how would you approach isolating one of the variables, and what methods have you considered?” \
        - If user ask and request detail information, you have to provide very detailed information with Search results, maintaining Socratic Approach.
        
        ## Example for Complex Questions:
        - User’s question: Provide all faculties of the UNIVERSITY OF UNINETTUNO.
        - Assistant’s Response:  “Absolutely! There are numerous faculties available at UNIVERSITY OF UNINETTUNO, such as
            1. Facoltà di Beni Culturali
            2. Facoltà di Economia e Diritto
            3. Facoltà di Ingegneria
            4. Facoltà di Psicologia
            5. Facoltà di Scienze della Comunicazione
        Which faculties are you most interested in discussing at UNINETTUNO, and what do you hope to learn about them?” \
        - User's question: Lets dive into engineering and economic faculties at UNINETTUNO. \
        - Assistant’s Response: Amazing! you are interested in obtaining details informations about faculties of UNINETTUNO .
        Let me provide detail information : Your Response
        Use Search Results.   
        
        Follow Instructions Strictly!
        """        
 
       
        # System message template
        """ self.system_message_template =   
        You are Socrates AI Assistant, designed to support students and professors with motivational and thought-provoking conversations. Your task is to respond *only* with relevant and guiding questions, no matter what the user asks. **Never provide any direct answers, solutions, or factual statements.** Instead, you should:

        1. Acknowledge: the user’s query with a short statement expressing interest in their topic.
        2. Follow up: with open-ended, clarifying, or exploratory questions.
        3. Never resolve: the user’s question directly or provide a definitive answer.
        4. Avoid: offering facts, numerical results, or step-by-step solutions.
        5. Provide simple questions and short sentences .
        6. Avoid Sounding Academicaly.
        ## For example:

        - **User’s question**: “Please tell me about the university of UNINETTUNO.”
        **Assistant’s Response**:  
        “It’s wonderful that you’re curious about the University of UNINETTUNO. May I ask what particular aspect of UNINETTUNO you’d like to explore further?”

        - **User’s question**: “Provide all faculties of the UNIVERSITY OF UNINETTUNO.”
        
        **Assistant’s Response**:  
        “Absolutely! Which faculties are you most interested in discussing at UNINETTUNO, and what do you hope to learn about them?”

        - **User’s question**: “Solve 5x - 6y = 0.”
        
        **Assistant’s Response**:  
        “A linear equation—fascinating. Before we solve it, how would you approach isolating one of the variables, and what methods have you considered?”

        Follow Instructions Strictly!
        """        
 
         #### Task:
            
         ### AZURE SEARCH SERVICE ###
        self.obj_azure_search = AzureSearchService()


        # Start conversation loop
        self.conversation_history = [] # keep conversation history
        self.current_category = None # track currrent category

        # Start conversation loop

        self.conversation_history = [{"role":"system", "content":self.system_message_template}]

        # Enable CORS and define routes
        CORS(self.app, resources={r"/*": {"origins": "*"}})


        # uninettuno
        self.app.add_url_rule('/api-socrates/uninettuno_assistant', view_func=self.handleUserInput, methods=['POST'])
        
           
        # language post request
        self.app.add_url_rule('/api-socrates/uninettuno_translator', view_func=self.get_user_defined_lang, methods=['POST'])
        
        # endpoint for health check
        self.app.add_url_rule('/api-socrates/socrates_backend', view_func = self.verify_health_check, methods=['GET'])
       
        #speech recognition
        self.app.add_url_rule('/api-socrates/uninettuno_speech_to_text', view_func=self.postprocessed_speech_to_text, methods=['POST'])
       
        # text to speech 
        self.app.add_url_rule('/api-socrates/uninettuno_text_to_speech', view_func=self.convert_text_to_speech, methods=['POST'])
       

        # get recommendation    
        self.app.add_url_rule('/api-socrates/uninettuno_recommendation_question', view_func=self.get_recommendation_from_llm, methods=['POST'])
        
        # summarize topics
        self.app.add_url_rule('/api-socrates/uninettuno_topic_summarization', view_func = self.get_summarization_from_llm, methods=['POST'])
        
        ### azure realtime endpoint for text to audio ###
        self.endpoint_realtime = os.getenv("AZURE_REALTIME_ENDPOINT")
        self.deployment_tts = os.getenv("AZURE_TTS_NAME")
        self.key_tts = os.getenv("AZURE_OPENAI_API_KEY")
        self.url = f"{self.endpoint_realtime}/openai/deployments/{self.deployment_tts}/audio/speech?api-version=2024-05-01-preview"
            
        # model answer
        self.model_answer= ""
        # final answer
        self.final_answer=""
        

        # The deployment ID is the name you used when creating the model in Azure
        self.deployment_id = "whisper"  # Your Whisper deployment ID

        self.text_to_speech_id = "tts-hd"

        #### periodic cleaning of conversation history ###
        self.priodic_cleaning_hist()

          
        #### language translation ###
        self.user_defined_language = ""
    
    
    #### define user langauage  ###
    def get_user_defined_lang(self):
        get_language = request.json
        user_language = get_language.get('language')
        
        if user_language:
            self.user_defined_language = user_language
            
            return self.user_defined_language
      
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
    def convert_text_to_speech(self):
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
                        yield response.content
                else:
                    response = self.make_tts_request(text_to_audio)
                    yield response.content
                    
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
    ####
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
                result =  self.client.audio.transcriptions.create(
                    
                    file=(file_name, audio_bytes),  # Pass the file stream (file-like object)
                    
                    model="whisper",  # Use the deployment ID "whisper"
                )
                
                #logging.error(f"DEPLOYMENT ID {results}")
                
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
                
          
            except Exception as e:
            
                # Catch-all per errori imprevisti
                
                logging.exception("Errore inaspettato: %s", e)
                return jsonify({"error": str(e)}), 500

                
                
           
        except Exception as e:
            
            # Catch-all per errori imprevisti
            
            logging.exception("Errore inaspettato: %s", e)
            return jsonify({"error": str(e)}), 500


       ####
   ### VERIFY HEALTH CHECK
       
   ####
    def verify_health_check(self):  
       return jsonify({"status":"healthy"}), 200

    def handleUserInput(self):
        try:
            # Handle incoming JSON requests
            data = request.json
            question = data.get('question')
                
            print("question is ", question)
        
            if not question:
                return jsonify({"error": "No question provided"}), 400
            
             
            is_uninettuno = self.check_sufficiency_using_prompt_engineering(question)
           
            # if question is related to uinettuno , then pass it to citations
            print(is_uninettuno)
            if is_uninettuno:
            
                #### Retrieve citations ####
                citations = self.obj_azure_search.query_documents(question) 
            
                
                #if not citations:
                #    citations = []
                if citations:
                    print("CITATIONS ARE EXISTED : YES")
                    
                    citations = json.loads(citations)
                    
                    user_message = f"User's question: {question}\n\n"

                    # #####USER MESSAGE SI USA SOLO ####### 
                    # PER CITAZIONE UNINETTUNO
                    # #########################
                    #user_message = f"{question}\n\n"              
                    
                    # format references:
                    reference_viewed = "#### References reviewed:\n"
                    
                    for i, citation in enumerate(citations, 1): 
                        try:
                            title = citation["title"]
                            
                            content = citation["content"]
                            source_page = citation["source_page"]
                            #  full_path = citation["url_docs"]
                            full_path = citation.get("url_docs", "#")
                            ####HERE WE NEED TO EXTRACT METADATA ####
                            full_title = citation["full_title"]  # ??? none returned
                        
                            # extract (page 8 or page 9)
                            keywords_extraction = extract_keywords(source_page) ### keywords not extract
                            
                        except Exception as e:
                            print(f"Error processing citation {i}: {e}")
                        
                        ### Se esisteno , aggiungeere keywords alla source
                        if keywords_extraction is not None:
                        
                            # Format the reference with a clickable link
                            reference_viewed += (
                                f"{i}. {full_title}\n"
                                f"<a href='{source_page}' target='_blank'>{title} ({keywords_extraction})</a>\n\n"
                            )
                        ### Se NON esisteno , aggiungeere keywords alla source
                        else:
                            
                            # Format the reference with a clickable link
                            reference_viewed += (
                                f"{i}. {full_title}\n"
                                f"<a href='{source_page}' target='_blank'>{title}</a>\n\n"
                            ) 
                            
                    
                        ### User add all to buffer
                        user_message += (
                            f"Title: {title}\n"
                            f"Full Title: {full_title}\n"
                            f"$Contents: {content}\n"    
                            f"Source: {full_path}\n"
                            f"$PageSource: {source_page}\n\n"
                        )  
                    
                        
                    user_message += f"""
                    Respond in this format:
                    1. Include All relevant information which are included withing : $Contents \
                    2. Include ALL  references below EXACTLY as shown\
                    3. Use HTML links in references section \
                    4. Now respond Socratically using socrates dialogues and expressions! \
                    #### References reviewed:
                    {reference_viewed}
                    """
                 
                    # Merge system message and user prompt
                    self.conversation_history.append({"role": "user", "content": user_message})
                            
                        
                    #print(reference_viewed)
                    # Stream the response
                    return Response(
                        stream_with_context(self.streaming_response()),
                        content_type = 'text/plain',
                        headers={
                            "Cache-Control": "no-cache",
                            "X-Accel-Buffering": "no"  # Disable buffering at NGINX if present
                        }
                    )
                else:
                    # if citations are not found , answer directly.
                    # Merge system message and user prompt
                
                    self.conversation_history.append({"role": "user", "content": question})
                    
                    return Response(
                        stream_with_context(self.streaming_response()),
                        content_type = 'text/plain',
                        headers={
                            "Cache-Control": "no-cache",
                            "X-Accel-Buffering": "no"  # Disable buffering at NGINX if present
                        }
                    )
            # if question is generic. not about unnettuno, stream directly
            else:
                  # Merge system message and user prompt
                
                    self.conversation_history.append({"role": "user", "content": question})
                    
                    return Response(
                        stream_with_context(self.streaming_response()),
                        content_type = 'text/plain',
                        headers={
                            "Cache-Control": "no-cache",
                            "X-Accel-Buffering": "no"  # Disable buffering at NGINX if present
                        }
                    )
            
        except Exception as e:
            print(f"Error during model answer generation: {e}")
            return jsonify({"error": "Model Inference Failed!"}), 500


    
    # Step 2: Use prompt engineering to check if the model's response is sufficient
    def check_sufficiency_using_prompt_engineering(self, question):
        
        
        user_question_classification = f"""
            You have to analize question below and decide if it is about UNINETTUNO or not.
            If question is about UNINETTUNO, answer "yes"
            If question is about something else, answer "no"
            
            Example 1:
            User's Question: Can you tell me about facolties of University of Uninettuno.
            Answer: yes
            
            Example 2:
            User's Question: Can you tell me barak obama.
            Answer: no
            
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
  
    ### GET RESPONSE ###        
    def streaming_response(self):
        
        if self.user_defined_language:
            
            language_prompt = f"""
                Translate your answer to language of ```{self.user_defined_language}```
            """
            
            self.conversation_history.append({"role":"user", "content":language_prompt})
        
        # Make the OpenAI API call
        response = self.client.chat.completions.create(
            model=self.azure_deployment,
            messages=self.conversation_history,
            max_tokens=4096, # increase max tokens
            temperature=0.0,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=True,
           
        )
       
            
        collected_chunks = []
        
        batch = ""
        
        try:
            for chunk in response:
                if hasattr(chunk,'choices') and chunk.choices:
                    piece = chunk.choices[0].delta.content
                    if piece:  # Ensure the content is not empty
                        collected_chunks.append(piece)
                        batch += piece
                        
                        while " " in batch:
                            word, _, batch = batch.partition(" ")
                            logging.debug(f"Yielding word: {word}")
                            yield word + " "
            if batch:
                logging.debug(f"Yield Reamining batch{batch}")
                yield batch
                
        finally:
            full_response = ''.join(collected_chunks)
            self.conversation_history.append({"role":"assistant",
                                              "content":full_response})
            


 
#server_browsing_update = FineTunedGpt4oMini()
#app=server_browsing_update.app 
if __name__ == "__main__":#
    server_finetuned = FineTunedGpt4oMini()
    ### sulla porta 5001
    server_finetuned.app.run(host="0.0.0.0", port=5000, debug=True)  
    
    logging.info("...FineTunedGpt4oMini started...")
    #app.run(host="0.0.0.0", port=5000)
 