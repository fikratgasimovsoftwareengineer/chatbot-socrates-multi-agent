from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
import json
### For now, we do not split text ###
#from langchain_text_splitters import CharacterTextSplitter
from azure.search.documents.models import QueryType , QueryAnswerType, QueryCaptionType
import os
from pathlib import Path
import sys

path_dir = Path(__file__).resolve().parent
sys.path.append(str(path_dir))

class AzureSearchService:
    
    def __init__(self):
        
          # Get Azure OpenAI credentials from environment variables
        self.azure_search_endpoint = os.environ.get('AZURE_SEARCH_ENDPOINT')
        self.search_api_key = os.environ.get('AZURE_SEARCH_KEY')
        self.search_index_name = os.environ.get('AZURE_SEARCH_INDEX_NAME')
      
      
            
        # SEARCH ADA
        self.search_ada_key = os.environ.get('AZURE_SEARCH_ADA_KEY')
        self.search_ada_endpoint = os.environ.get('AZURE_SEARCH_ADA_ENDPOINT')
        self.search_ada_version = os.environ.get('AZURE_API_VERSION_ADA')
        
        
        """ self.text_split = CharacterTextSplitter(
            separator="\n\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        ) """
        
        self.client = SearchClient(
            endpoint=self.azure_search_endpoint,
            index_name=self.search_index_name,
            credential=AzureKeyCredential(self.search_api_key)
        )
      
    

    def get_embeddings(self, text: str):
  
        client = AzureOpenAI(
            azure_endpoint=self.search_ada_endpoint,
            api_key=self.search_ada_key,
            api_version=self.search_ada_version,
        )
        embedding = client.embeddings.create(input=[text], model="text-embedding-ada-002")
        return embedding.data[0].embedding


    def query_documents(
        self,
        question:str, 
        top:int=3,
        use_semantic_search:bool=True,
        semantic_config_name: str="default"
        ):
     
        try:
            # Create a vectorized query
            vector_query = VectorizedQuery(
                vector=self.get_embeddings(question),
                #fields=["id", "content", "title","metadata", "sourcepage", "sourcepagebucket", "sourcefile", "sourcefilebucket", "embedding"],
                fields="embedding",
                exhaustive=True,
                k_nearest_neighbors=50
                # Field in the index used for vector search
            
            ) 
            

            """
            Query documents using either vector search or semantic search, 
            optionally combining them if needed. 
            Returns a list of results or None if nothing found.
            
            :param question: The query text.
            :param top: Max number of docs to retrieve.
            :param score_threshold: Min @search.score required to keep a doc.
            :param use_semantic_search: Whether to use Azure Cognitive Search's semantic pipeline.
            :param semantic_config_name: Name of your semantic config in the index (default is 'default').
            :param query_language: Language code for semantic search or speller, e.g., 'en', 'it', etc.
            """
            
            if use_semantic_search:
                results = self.client.search(
                    search_text=question,
                    vector_queries=[vector_query],
                    top=top*2, # = pagesize * 2 behavior 
                    query_type=QueryType.SEMANTIC,
                    semantic_configuration_name=semantic_config_name,
                    query_caption=QueryCaptionType.EXTRACTIVE,
                    query_answer=QueryAnswerType.EXTRACTIVE,   
                    select=["id", "content", "title", "sourcepage", "sourcepagebucket", 
                        "sourcefile", "sourcefilebucket", "embedding", "metadata"]
                )
    
                return self._map_fields(results)
        except Exception as e:
            print(f"Search Error {e}" )
            return None
        #print(total_docs)
        #return total_docs
       
    
   
    def _map_fields(self, results, score_threshold_semantic:float=2.2):#score_threshold_semantic=2.2
        """
        Map the fields from Azure Search results to a structured dictionary.
        """
        collector_content = []
      
        for index, result in enumerate(results):
            full_url_aws_s3 = ""
            full_url_aws_s3_source_page = ""
            
                
            #embedding_score = result.get('@search.score', "")
            # 2) The semantic re-ranker score if available
            #    (only present if query_type=semantic and re-ranker is applied)
            
            #===============================================
            ###The @search.rerankerScore range is 1 to 4.00, 
            
            # #where a higher score indicates a stronger semantic match.
            ## The Smaller Vector search is, The better results are! 
            #  @search.score
            ### 
            embed_semantic_score = result.get('@search.reranker_score')
            #embed_vector_score = result.get('@search.score')
        
            ### EMBEDDING SEMANTIC SCORE ###
            if embed_semantic_score  >= score_threshold_semantic:
                ### EMBED VECTOR STORE- DOUBLE CHECK ###
                #if embed_vector_score >= 0.6:
                
                """
                ### Meta data ###
                        {
                        "academicyear": "2012/2013",
                        "degreecourse": "Psicotecnologie e processi formativi (nuova edizione)",
                        "discipline": "Discipline psicosociali ",
                        "studypath": null,
                        "faculty": "Facoltà di Psicologia",
                        "scotitle": "Psicotecnologie e processi formativi (nuova edizione)",
                        "language": null,
                        "other": []
                        ###return : discipline+academicyear+degreecourse
                """
            
                source_file = result.get("sourcefile", "")
                citation_data = {}
                if source_file.lower().endswith('.pdf'):
                    
                    
                    
                    title = result.get("title")
                    
                    #### HERE WE NEED TO EXTRACT METADATA ####
                    
                    metadata_list = result.get("metadata", [])  
                    
                    full_title_docs = ""
                   
                    
                    if isinstance(metadata_list, list) and len(metadata_list) > 0:
                        
                        # Possibly take the first dictionary in that list
                        first_meta = metadata_list[0]
                        discipline = first_meta.get("discipline") or ""
                        academicyear = first_meta.get("academicyear") or ""
                        degreecourse = first_meta.get("degreecourse") or ""
                        full_title_docs = f"{discipline} {academicyear} {degreecourse}".strip()
                    else:
                        full_title_docs = " "

                                            
                    #id = result.get("id")
                    content = result.get("content")
                    sourcepage = result.get("sourcepage","")
                    # sourcepagebucket = result.get("sourcepagebucket")
                    sourcefile = result.get("sourcefile")
                    sourcefilebucket = result.get("sourcefilebucket") 
                
                    if sourcefilebucket == 'uninettunomateriale':
                     
                        full_url_aws_s3 = f'https://{sourcefilebucket}.s3.eu-west-1.amazonaws.com/{sourcefile}'
                        full_url_aws_s3_source_page = f'https://{sourcefilebucket}.s3.eu-west-1.amazonaws.com/{sourcepage}'
                        
                    elif sourcefilebucket == 'videoroot':
                     
                        full_url_aws_s3 = f'https://{sourcefilebucket}.s3.eu-west-1.amazonaws.com/{sourcefile}'
                        full_url_aws_s3_source_page = f'https://{sourcefilebucket}.s3.eu-west-1.amazonaws.com/{sourcepage}'
                                
                    citation_data = {
                        "title":title,
                        "content":content.replace('Facoltà di Giurisprudenza', '').strip(),
                        "source_page":full_url_aws_s3_source_page,
                        "url_docs":full_url_aws_s3,
                        "full_title":full_title_docs
                        
                    }
                    
                    if citation_data:   
                        collector_content.append(citation_data)
    
        
                   
        # collector content
        if collector_content:     
            return json.dumps(collector_content, indent=2)
        else:
            return None
            


