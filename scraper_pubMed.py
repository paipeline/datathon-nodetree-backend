import requests
from bs4 import BeautifulSoup
import smtplib # mail protocol
import time
import json

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
        print(URL)
        pmid_list = pmc_scrapy(URL)
        pmid_total +=  pmid_list
        print(len(pmid_total))
    
            
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
                pid = element.find('span', class_='docsum-pmid').get_text().strip()
                pmid_array.append(pid)
    
    print(pmid_array, "pmid_array")
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
    results = {}

    for pmid in pmids:
        url = f"{base_url}/{pmid}/unicode"
        response = requests.get(url)

        if response.status_code == 200:
            try:
                data = response.json()[0]  # Parse JSON response
                text_content = []
                print(type(data), "data")
                
                # Extract text from BioC JSON structure
                for passage in data.get("documents", [])[0].get("passages", []):
                    text_content.append(passage.get("text", ""))

                # Store concatenated full text
                results[pmid] = "\n".join(text_content)
            except json.JSONDecodeError:
                print(f"Failed to decode JSON for PMID {pmid}")
        else:
            print(f"Error fetching data for PMID {pmid} (Status Code: {response.status_code})")

    return results




results = scrape("covid", 50)
print(results)