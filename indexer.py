import re
import os
import string
import json
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
ps = PorterStemmer()


def ordered_documents(path):
    """
    Extract the documents' names from the given path and return 
    them in a sorted list (0.txt, 1.txt, 2.txt, ...).
    """
    return sorted(os.listdir(path), key=lambda x: int(x.split(".")[0]))


def extract_data(names_of_documents):
    """
    Extract the data from the given path.

    """
    documents = []
    for doc_name in names_of_documents:
        with open(f"data/{doc_name}", "r") as f:
            document = json.loads(f.read())
            document["id"] = int(doc_name.split(".")[0])
            documents.append(document)
    return documents


def transform_document(doc):
    """
    Transform the document to a format {'id': 1, 'text': 'this is a text'}.
    """
    auths = []
    try:
        for author in doc["authors"]:
            auths.append(author["name"].split(".")[0])
    except:
        pass
    d = doc["title"] + " " + " ".join(auths)
    id = doc["id"]
    return {"id": id, "text": d}

def deep_clean(words):
    """
    used to normalise words before indexing.
    """    
    cleaned, non_cleaned = [], []
    for w in words:
        try:
            splited = re.split(r'[-—’/]', w)
            assert len(splited) > 1 # raise an error 
            cleaned.extend(splited)
        except:
            non_cleaned.append(w)

    for w in non_cleaned:
        for c in w:
            if not c.isalpha():
                a = w.replace(c, " ")
                if len(a.strip()) > 4:
                    cleaned.append(a.strip())
    return cleaned


def extract_words(data):
    """
    Extract the words from the given data.
    Clean the word using text mining techniques like stemming and stop words...
    """
    words = []
    for doc in data:
        word_tok = word_tokenize(doc["text"])
        words_without_pct = [w.lower()
                             for w in word_tok if w not in string.punctuation]
        non_alphanumeric_words = [
            w for w in words_without_pct if not w.isalnum()]
        cleaned = words_without_pct + deep_clean(non_alphanumeric_words)
        stemmed = [ps.stem(w) for w in cleaned]
        without_stop_words = [
            w for w in stemmed if w not in stopwords.words("english")]
        for w in without_stop_words:
            words.append((w, doc["id"]))
    return sorted(words)


def creat_dictionary(words):
    """
    Creating the dictionary (terms and postings list) from the given words.
    """
    indexer = {}
    for word in words: 
        w = word[0]
        nbr = word[1]
        if w not in indexer:
            # append key and value
            indexer[w] = [nbr] 
        else:
            # update only the value, key already exists
            if nbr not in indexer[w]:
                indexer[w].append(nbr) 
    # add all items alphanum (leave out special charac )
    return sorted([item for item in indexer.items() if item[0].isalnum()]) 



def update_index(dictionary):
    """
    Update the index
    """
    for d in dictionary:
        file_name = f"{d[0]}.txt"
        if file_name not in os.listdir(f"dictionary/"):
            with open(f"dictionary/{file_name}", "w") as f:
                f.write(json.dumps(d[1]))
        else:
            with open(f"dictionary/{file_name}", "r") as f:
                old_postings = json.loads(f.read())
            with open(f"dictionary/{file_name}", "w") as f:
                f.write(json.dumps(old_postings.extend(d[1])))



def index_data(non_indexed_docs):
    """
    Index the given data.
    """
    # 1. transform the documents
    transformed_docs = []
    for doc in non_indexed_docs:
        transformed_docs.append(transform_document(doc))
    # 2. extract the words from each the documents and create an indexer
    words = extract_words(transformed_docs)
    return creat_dictionary(words)


def get_postings(word):
    
    """
    getting the file containing the matching query
    """   
    try:
        file = [w for w in os.listdir(f"dictionary/") if word in w][0] 
        return json.loads(open(f"dictionary/{file}", "r").read())
    except:
        return []


def intersect(pst1, pst2):
    """
    Intersect two postings list.
    """
    ans = []
    p1, p2 = 0, 0
    while p1 < len(pst1) and p2 < len(pst2):
        if pst1[p1] == pst2[p2]:
            ans.append(pst1[p1])
            p1 += 1
            p2 += 1
        elif pst1[p1] < pst2[p2]:
            p1 += 1
        else:
            p2 += 1
    return ans


def intersect_all(words):
    """
    find the intersect of the postings list of the words
    """
    postings = get_postings(words[0]) 
    for word in words[1:]:
        new_postings = get_postings(word) 
        if not new_postings:
        #if the word is not in the dictionary skip it, meaning that 
        #if someone inserts a wrong word it will skip it instead of returning an empty list
            continue
        postings = intersect(postings, new_postings)
    return postings


def search(query):
    words = word_tokenize(query)
    words = [w.lower() for w in words if w not in string.punctuation]
    words = [ps.stem(w) for w in words]
    words = [w for w in words if w not in stopwords.words("english")]
    return intersect_all(words)

