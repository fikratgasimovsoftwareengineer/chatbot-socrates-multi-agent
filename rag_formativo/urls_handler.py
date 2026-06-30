###extract page number from urls###

def extract_keywords(url):
    keyword = ""
    # split urls
    fragment= url.split("#")[-1]
    # Replace '=' with a space to form "page 8"
    
    # # Check if the fragment contains a page number (e.g., "page=18" or "pagina=18")
    if "page=" in fragment.lower() or "pagina=" in fragment.lower():
        keyword = fragment.replace("="," ")
        return keyword.strip()
    return " "
    