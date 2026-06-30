from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
import os

def search_langchain(query):

    try:
            # 2) Istanzia il wrapper (non serve ripassare le chiavi se sono già in env)
        search = GoogleSearchAPIWrapper(
            google_api_key=os.environ["GOOGLE_API_KEY"],
            google_cse_id=os.environ["GOOGLE_CSE_ID"],
            k=7  # numero di risultati di default
        )
        print("Avvio della ricerca...")    
        # Esegui la ricerca
        raw_results = search.results(query, 7 )  # Ottieni i risultati come JSON
        return raw_results
    
    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")


# return page and urls of page
def filter_google_web(google_webengine_json):
        
    urls=[]

    if not google_webengine_json:
        print("Nessun risultato trovato.")
        return None
    
    
    for i,_ in enumerate(google_webengine_json):
        
        if i <= 7:
            site_url = google_webengine_json[i]['link']
            urls.append(site_url)
    if urls:
        
        return urls
    
    else:
        return None
