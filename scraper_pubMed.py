import requests
from bs4 import BeautifulSoup
import smtplib # mail protocol
import time
import json
from langchain.schema import Document

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://pubmed.ncbi.nlm.nih.gov/",
    "Connection": "keep-alive",
}



def scrape(keywords, limit):
    limit *= 1.2
    limit = int(limit)
    page = 0
    pmid_total = []
    
    while len(pmid_total) < limit:
        page += 1
        URL = f"https://pubmed.ncbi.nlm.nih.gov/?term={keywords}&size=50&page={page}"
        # print(URL)
        pmid_list = pmc_scrapy(URL)
        pmid_total +=  pmid_list
        # print(len(pmid_total))
    
            
    pmid_total = pmid_total[:limit]
            
        
    full_texts = fetch_full_text_bioc(pmid_total)

    
    return full_texts



def pmc_scrapy(URL):
    pmid_array = []
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    # print(soup.prettify()) 
    citation = soup.find_all('div', class_='docsum-citation full-citation')
    for cit in citation:
        free_article = cit.find('span', class_='free-resources spaced-citation-item citation-part')
        if free_article:
            if free_article.get_text() == "Free PMC article." :
                element = cit.find('span', class_='citation-part')
                pid = element.find('span', class_='docsum-pmid')
                if pid:
                    pid = pid.get_text().strip()
                    pmid_array.append(pid)
    
    return pmid_array





def fetch_full_text_bioc(pmids):
    """
    Fetches full text for a list of PubMed IDs (PMIDs) using the BioC API.

    Args:
        pmids (list): A list of PubMed IDs.

    Returns:
        dict: A dictionary mapping PMID to extracted text.
    """
    base_url = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json"
    documents = []
    for pmid in pmids:
        url = f"{base_url}/{pmid}/unicode"
        response = requests.get(url)

        if response.status_code == 200:
            try:
                data = response.json()[0] #Parse JSON response
                text_content = []
                
                for document in data.get("documents", []):
                    title = document['passages'][0]['text']
                    authors = []
                    for key, value in document['passages'][0].get("infons", {}).items():
                        if key.startswith("name_"):
                            # Extract author names
                            author_info = value.split(";")
                            surname = author_info[0].split(":")[1]
                            given_name = author_info[1].split(":")[1]
                            authors.append(f"{given_name} {surname}")


                    for passage in document.get("passages", []):
                        text = passage['text']
                        if text:
                            text_content.append(text)
                        
                        

                documents.append(
                        Document(
                            page_content="\n".join(text_content),  # Store full-text from PDF
                            metadata={
                                "title": title,
                                "authors": ', '.join(authors) if authors else 'Unknown Authors',
                                "published": "published",
                                "pdf_url": "None"
                            }
                    )
                )

            except json.JSONDecodeError:
                # print(f"Failed to decode JSON for PMID {pmid}")
                pass
        else:
            print(f"Error fetching data for PMID {pmid} (Status Code: {response.status_code})")

    return documents
