import requests
import os
import json

def process_paper_metadata(paper):
    """
    Process raw paper metadata into clean format.
    
    Args:
        paper (dict): Raw paper metadata from API
    
    Returns:
        dict: Cleaned paper metadata
    """
    # Extract paper ID from URL (e.g. w33433 from /papers/w33433)
    paper_id = paper['url'].split('/')[-1]
    
    # Clean author names by removing HTML tags
    authors = [
        author.replace('<a href="/people/', '').split('">')[1].replace('</a>', '')
        for author in paper['authors']
    ]
    
    # Create cleaned metadata dict
    metadata = {
        'unique_id': f"nber_{paper_id}",
        'title': paper['title'],
        'authors': authors,
        'abstract': paper['abstract'],
        'date': paper['displaydate'],
        'paper_id': paper_id,
        'url': f"https://www.nber.org{paper['url']}",
        'journal': 'NBER Working Paper'
    }
    
    return metadata

def download_nber_paper(paper_metadata: dict) -> bool:
    """
    Downloads NBER working paper given its metadata and saves it to specified directory.
    
    Args:
        paper_metadata (dict): Paper metadata including unique_id, paper_id, etc.
    
    Returns:
        bool: True if download successful, False otherwise
    """
    # Create save directory structure: data/papers/nber/w12345/
    paper_dir = f"../Data/papers/nber/{paper_metadata['paper_id']}"
    os.makedirs(paper_dir, exist_ok=True)
    
    # Define paths for paper and metadata
    pdf_path = os.path.join(paper_dir, "paper.pdf")
    metadata_path = os.path.join(paper_dir, "metadata.json")
    
    # Check if files already exist
    if os.path.exists(pdf_path) and os.path.exists(metadata_path):
        print(f"Paper {paper_metadata['paper_id']} already exists at {paper_dir}")
        return True
        
    # Construct PDF URL
    pdf_url = f"https://www.nber.org/system/files/working_papers/{paper_metadata['paper_id']}/{paper_metadata['paper_id']}.pdf"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': paper_metadata['url'],
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-ch-ua-mobile': '?0',
        'if-modified-since': 'Tue, 04 Feb 2025 03:01:10 GMT',
        'Cookie': 'STYXKEY_wp_claim=JV1A93ePauAe; SSESS434783100c680fee468371c19ab1c999=jpN7%2CwbBGvqvuRLLJXlrr-kYSPHcaA%2CH9R8wp9e-L3mHT0hY; STYXKEY_nber_user_info=Daniel|0|0; STYXKEY_nber_attributes=|1||yes|; STYXKEY_username_ticket_cookie=1849127750-daniel_milo; STYXKEY_security_tickets=2120753342'
    }

    # Download PDF
    response = requests.get(pdf_url, headers=headers)
    
    if response.status_code == 200:
        # Save PDF
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
            
        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(paper_metadata, f, indent=2)
            
        print(f"Paper and metadata saved to {paper_dir}")
        return True
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")
        return False

def fetch_nber_papers(page: int = 1, per_page: int = 50) -> list:
    """
    Fetches NBER working papers from the API.
    
    Args:
        page (int): Page number to fetch
        per_page (int): Number of papers per page
        
    Returns:
        list: List of paper metadata dictionaries
    """
    base_url = "https://www.nber.org/api/v1/working_page_listing/contentType/working_paper/_/_/search"
    params = {
        'page': page,
        'perPage': per_page,
        'sortBy': 'public_date'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Process each paper's metadata
        papers = []
        for paper in data['results']:
            metadata = process_paper_metadata(paper)
            papers.append(metadata)
            
        return papers
    except Exception as e:
        print(f"Error fetching papers: {e}")
        return []

def download_latest_papers(num_pages: int = 1):
    """
    Downloads the latest NBER papers.
    
    Args:
        num_pages (int): Number of pages to fetch and download
    """
    for page in range(1, num_pages + 1):
        papers = fetch_nber_papers(page=page)
        for paper_metadata in papers:
            print(f"Downloading paper {paper_metadata['paper_id']}...")
            download_nber_paper(paper_metadata)


if __name__ == "__main__":
    download_latest_papers(num_pages=1)