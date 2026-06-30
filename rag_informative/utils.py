from google_labs_html_chunker.html_chunker import HtmlChunker
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from langchain_community.document_loaders import PyPDFLoader


def chunk_to_embedding(client,  user_question, html_content:list[str, str])->list[tuple[str, list[str]]]:

    results = {}

    querry_vector =  embedd_text(client, user_question) 


    with ThreadPoolExecutor(max_workers=5) as executor:

        html_content_filtering = {
            # if html body exits , return url!
            ### here it retuyrns all urls from html content, even nested urls.
            ### html body is considered as entire concept of html content
            executor.submit(postprocess_html, client, url, html_body, querry_vector): url for url, html_body in html_content if html_body
        }
        for chunk in  as_completed(html_content_filtering):
            get_url = html_content_filtering[chunk]
            if (get_url.endswith('.pdf')):
                print(f"url is PDF...{get_url}")
                
                continue

            try:
                relevant_chunk = chunk.result()
                if relevant_chunk and isinstance(relevant_chunk, list): # if there are relevant chunks
                    # extract passagtes
                    #extracted_passages = [chunk_dict["passage"] for chunk_dict in relevant_chunk]
                    results[get_url] = relevant_chunk
                    #print(results)
                   
         
            except requests.exceptions.HTTPError as e:       
                print(f"Error processing URL {get_url}: {e}")
    
    # Rerank URLs based on passage relevance
    ranked_results = reranked_results(results)

    return ranked_results

    
def postprocess_html(client, url, html_body, query_vector, threshold=0.38):
    
    chunker = HtmlChunker(
        max_words_per_aggregate_passage=500, # solo cinque.
        greedily_aggregate_sibling_nodes=True,
    )
    
    passages = chunker.chunk(html_body)
    
    relevant_chunks = [] # will contain passages with similariy score
    
    # passage returns all content from passages
    for passage in passages:
        
        ### qua dobbiamo spingere passage da passage , no come 8191###
        passage_vector = embedd_text(client, passage[:6000])

        similarity_score = get_cosine_similarity(query_vector, passage_vector)
     
        if similarity_score > threshold:
            relevant_chunks.append({
                "passage":passage,
                "similarity_score":similarity_score
            })
            
       
            #relevant_chmost_relevant_passagesunks.append((passage, similarity_score))

    relevant_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    if not relevant_chunks:
        print("No relevant chunks found!")
 
    return relevant_chunks


### embedded 
def embed_pdf_contents(client,  user_question, pdf_contents):
    
    if not pdf_contents:
        print("No pdf contents")
        return []
    
    
    # query vector embedding
    query_vector =  embedd_text(client, user_question)
    relevant_embedding_store = []

    ###
    # pdf_contents[0][0]
    ###
    for page_url, pages in pdf_contents:
        for page in pages:
            
            page_cont = page.get('page_content', '')
            
            
            
            page_vector = embedd_text(client, page_cont)
            
            similarity_score = get_cosine_similarity(query_vector, page_vector)
            

            if similarity_score > 0.45:
                
                #print(f"Passage: {page_cont}, Similarity : {similarity_score}")
                
                relevant_embedding_store.append({"pdfchunk":page_cont})
    
    relevant_embedding_store.append({"pdfurl":page_url})
    
    if not relevant_embedding_store:
        print("No relevant embedding score fouund!")
    return relevant_embedding_store

### EMBED QUERRY WITH TEXT LARGE
def embedd_text(client, content):
    
    try:
        content = content[:4096]
        embedding_response = client.embeddings.create(
            input=content,
            model="text-embedding-3-large"
        )
    
        return np.array(embedding_response.data[0].embedding)  
    except Exception as e:
        print(f"Embedding failed : {e}")
        
    
    
# Calculate cosine similarity between two vectors
def get_cosine_similarity(vector1, vector2):

    # Reshape the vectors to 2D arrays before passing to cosine_similarity
    vector1 = np.reshape(vector1, (1, -1))
    
    vector2 = np.reshape(vector2, (1, -1))
    return cosine_similarity(vector1, vector2)[0][0]


""" 
# rank results due to cosine similarity results
def reranked_results(results):
    
    Rerank urls based on most relevant passage.. 
    
    if not results:
        print("NO RESULTS to rerank")
        return []
    ranked_results = sorted(
        results,
        key=lambda x: max(chunk[1] for chunk in x[1]),  # Max similarity score per URL
        reverse=True
    
    )

    return ranked_result
"""
def reranked_results(results: dict) -> list:
    """
    Reranks the URLs based on the highest similarity score of their chunks.
    Returns a list of dictionaries sorted by relevance.
    """
    all_ranked = []
    for url, chunk_dicts in results.items():
        #print(f"Processing URL for reranking: {url} with chunks: {chunk_dicts}")
        if not chunk_dicts:
            max_score = 0
        else:
            max_score = max(d["similarity_score"] for d in chunk_dicts)

        all_ranked.append({
            "url": url,
            "chunks": chunk_dicts,
            "max_similarity": max_score
        })

    # Sort descending by max_similarity
    all_ranked.sort(key=lambda x: x["max_similarity"], reverse=True)
    #print("Final Ranked Results:", all_ranked)
    return all_ranked

# EXTERNAL PDF HANDLER
def external_pdf_handler(file_path): #url_endpoint_to_file
    
    # pages with number
    pages_contents = []
    
    # loader pdf 
    loader =  PyPDFLoader(file_path, extract_images = False)
    
    # loader and split docs
    pages = loader.load_and_split() 
    
    if len(pages)>0:

        #for page_num, page in enumerate(pages, start=1):
        for page in pages:    
            #pages_with_num.append({"page_number":page_num, "page_content":page.page_content})    #page.page_content[:1000]
            pages_contents.append({"page_content":page.page_content[:1000]})    #page.page_content[:1000]
        
        
    return pages_contents