from time import sleep
import requests
from bs4 import BeautifulSoup
import json
import os
import indexer as indx


def load_data():
    """
    load first document.
    updating documents publications, check if the first doc is already there 

    """
    try:
        print("Loading stored data...")
        # sorting files in the directory
        # filtering following the [0] of the file name
        # [-1] to target the last article uploaded
        last_added_file = sorted(os.listdir(
            "data/"), key=lambda x: int(x.split(".")[0]))[-1]
        with open(f"data/{last_added_file}", "r") as f:
            print("Updating...")
            return json.loads(f.read())
    except:
        print("No stored data found, inserting...")
        # when running the code for the first time



def save_data(documents):

    """
    Saving data in the directory

    """
    # checking the total nbr of files
    # appending the new downloaded files in the total number of files
    # naming the new files by adding the length of of the total number of files and the index of the file itself
    nbr_of_files = len(os.listdir("data/"))
    new_files = []  # names of new files
    for doc in documents:
        file_name = f"{nbr_of_files + documents.index(doc)}.txt"
        new_files.append(file_name)
        with open("data/"+file_name, "w") as f:
            f.write(json.dumps(doc))
    print("Data saved!")
    print("Indexing...")
    print("This may take some time...")
    # indx is a library created from the indexer file which runs in parallel to the crawler
    indexed_data = indx.index_data(indx.extract_data(new_files))
    # updating index instead of reindexing all the data from scratch
    indx.update_index(indexed_data)
    print(f"Done!, scrapped {len(documents)} documents successfully")


def scrape_document(li):
    
    """
    Scraping webpages and extracting the information needed

    """
    container = li.find("div", {"class": "result-container"})
    data_div = container.find("div")

    # children is a list of all elements in the div, it contains the title, link, authors , date and many others
    # we need to stop when we reach "date" (that's why we use break)
    children = []
    # contains all the elements in the div (html)
    for ch in data_div.children:  
        try:
            children.append(ch)
            if "date" in ch.get("class"):
                break
        except:
            pass

    # "a" is always the first child, it contains the title and link, the date is always the last child
    # all the other children are the authors separated by commas
    # some of them have links, for the rest we put None as the link
    a = children[0].find("a")
    a_href = a.get("href")
    title = a.find("span").text
    date = children[-1].text
    authors = []
    for ch in children[1:-1]:
        try:
            authors.append(
                {"name": ch.find("span").text.strip(), "link": ch.get("href")})
        except:
            if ch.text.strip() in [",", "&"]:
                continue
            authors.append({"name": ch.text, "link": None})

    document = {
        "title": title,
        "link": a_href,
        "authors": authors,
        "date": date
    }
    return document



def document_exists(li, doc):
    "Comapring scraped html to exisiting documents"
    return scrape_document(li) == doc


baseurl = "https://pureportal.coventry.ac.uk/en/organisations/school-of-computing-electronics-and-maths/publications/"
documents = []
loaded_doc = load_data()  # retrieve last added doc
exit = False
soup = BeautifulSoup(requests.get(baseurl).text, "html.parser")
nbr_of_pages = int(soup.find("nav", {"class": "pages"}).find(
    "ul").find_all("li")[-2].find("a").text)

#browse all urls
for page in range(nbr_of_pages):
    print(f"Scraping page {page+1}...")
    if page != 0:
        soup = BeautifulSoup(requests.get(
            baseurl + "?page=" + str(page)).text, "html.parser")
    # ul contains all the publications
    ul = soup.find("ul", {"class": "list-results"})
    
    # lis contains all li(information about each publication)
    lis = []
    # we only extract li that have a class "list-result-item" as this class contains all the information
    for l in ul.find_all("li"):
        if "list-result-item" in l.get("class"):
            lis.append(l)
    
    for li in lis:
        if document_exists(li, loaded_doc):
            exit = True
            break
        else:
            documents.insert(0, scrape_document(li))
    if exit:
        break
    sleep(5)
save_data(documents)
