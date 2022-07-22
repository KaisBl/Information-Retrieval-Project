import time
import json
import pandas as pd
import numpy as np
import indexer as ind
from sklearn.feature_extraction.text import TfidfVectorizer



def get_corpus(postings):
    """
    Extracts the data from the postings list
    """
    filenames = [f"{w}.txt" for w in postings]
    return [ind.transform_document(doc) for doc in ind.extract_data(filenames)]

def get_idf(corpus):
    """
    Transform a corpus [{'id': 1,'text': 'This is a text'}] to TFIDF to estimate ranking
    """
    vectorizer = TfidfVectorizer(stop_words='english', analyzer='word')
    x = vectorizer.fit_transform([d["text"] for d in corpus]).T.toarray()
    idf = pd.DataFrame(x, index=vectorizer.get_feature_names())
    return idf, vectorizer

def get_similar_documents(q):
    """ 
    Get cosine similarity of query
    """
    print("query:", q)
    print("The following is the article with the highest cosine similarity value: ")

    corpus = get_corpus(ind.search(q))
    idf, vectorizer = get_idf(corpus)
    # Convert the query become a vector
    q = [q]
    q_vec = vectorizer.transform(q).toarray().reshape(idf.shape[0],)
    sim = {}
    # Calculate the similarity
    for i in range(len(idf.columns)):
        sim[i] = np.dot(idf.loc[:, i].values, q_vec) / np.linalg.norm(idf.loc[:, i]) * np.linalg.norm(q_vec)
    # Sort the values
    sim_sorted = sorted(sim.items(), key=lambda x: x[1], reverse=True)
    # Print the articles and their similarity values
    for k, v in sim_sorted:
        if v != 0.0:
            id = corpus[k]['id']
            rate = f'{v:.4f}'
            print(f'Similarity: {rate}')
            with open(f"data/{id}.txt") as f:
                content = json.loads(f.read())
                print(json.dumps(content, indent=4, sort_keys=True))
                print()
            


def search_query(query):
    """
    get the execution time of a query
    """
    start = time.time()
    get_similar_documents(query)
    end = time.time()
    print(f"Execution time: {end - start}")
