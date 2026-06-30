import numpy as np

from sklearn.metrics.pairwise import cosine_similarity


def split_markdown_to_chunks(markdown_content_html):


    """
    Split the markdown content into chunks based on paragraph breaks.
    
    Args:
    - markdown_content: The cleaned Markdown text.

    Returns:
    - List of paragraph chunks.
    """

    chunks = markdown_content_html.split("\n\n")

    chunk = [ chunk.strip() for chunk in chunks if chunk.strip()]

    return chunk



embedding_html_indices = []

### EMBED QUERRY WITH TEXT LARGE
def embedd_querry(client, content):
    embedding_response = client.embeddings.create(
        input=content,
        model = "text-embedding-3-large"
    )
    embedding_response.data[0].embedding   
    return np.array(embedding_response.data[0].embedding)  
    
    
# Calculate cosine similarity between two vectors
def get_cosine_similarity(vector1, vector2):

    # Reshape the vectors to 2D arrays before passing to cosine_similarity
    vector1 = np.reshape(vector1, (1, -1))
    
    vector2 = np.reshape(vector2, (1, -1))
    return cosine_similarity(vector1, vector2)[0][0]

'''
def tokenize_sentence(sentence):
    
    return re.findall(r'\b\w+\b', sentence)
'''


# Extract key tokens based on similarity to the entire sentence
def search_doc(client,  user_question,  scrapped_content):


    # step 1 : extract chunk from html

    chunk_html = split_markdown_to_chunks(scrapped_content)

    # step 2: embed chunk
    browsering_chunk_html = {}

    for ids, chunks in enumerate(chunk_html):
        browsering_chunk_html[chunks] = embedd_querry(client, chunks)

    # step 3 : embed query

    query_vector = embedd_querry(client, user_question)

    # Step 4: Calculate cosine similarity for each token with the entire sentence embedding
    
    embedding_similarity = {chunk: get_cosine_similarity(chunk_vector, query_vector) for chunk, chunk_vector in browsering_chunk_html.items()}

    sorted_chunks = sorted(embedding_similarity.items(), key=lambda x: x[1], reverse=True)

    most_relevant_chunk = [ chunk for chunk, _ in  sorted_chunks[:4]]

    return most_relevant_chunk