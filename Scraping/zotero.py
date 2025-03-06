from pyzotero import zotero
import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv

'''
Plugs into your Zotero account and downloads papers from a specified collection.
'''

# Load environment variables
load_dotenv()

def process_zotero_metadata(item: Dict) -> Dict:
    """
    Process Zotero item metadata into clean format matching NBER structure.
    
    Args:
        item (dict): Raw Zotero item metadata
        
    Returns:
        dict: Cleaned paper metadata
    """
    # Extract creators and format as list of names
    creators = item['data'].get('creators', [])
    authors = [
        f"{creator.get('firstName', '')} {creator.get('lastName', '')}".strip()
        for creator in creators
    ]
    
    # Create metadata matching NBER format
    metadata = {
        'unique_id': f"zotero_{item['key']}",
        'title': item['data'].get('title', ''),
        'authors': authors,
        'abstract': item['data'].get('abstractNote', ''),
        'date': item['data'].get('date', ''),
        'paper_id': item['key'],
        'url': item['data'].get('url', ''),
        'journal': item['data'].get('publicationTitle', '')
    }
    
    return metadata

def copy_zotero_paper(zotero_storage_path: Path, item_metadata: Dict, attachment: Dict) -> bool:
    """
    Copies PDF from Zotero storage to our paper directory.
    
    Args:
        zotero_storage_path: Path to Zotero storage directory
        item_metadata: Paper metadata
        attachment: Attachment information from Zotero
    """
    # Create save directory structure: data/papers/zotero/item_key/
    paper_dir = Path("../Data/papers/zotero") / item_metadata['paper_id']
    paper_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_path = paper_dir / "paper.pdf"
    metadata_path = paper_dir / "metadata.json"
    
    # Check if files already exist
    if pdf_path.exists() and metadata_path.exists():
        print(f"Paper {item_metadata['paper_id']} already exists at {paper_dir}")
        return True
    
    try:
        # Construct path to PDF in Zotero storage
        storage_key = attachment['key']
        pdf_filename = attachment['data'].get('filename', 'paper.pdf')
        source_path = zotero_storage_path / storage_key / pdf_filename
        
        if not source_path.exists():
            print(f"Source PDF not found at {source_path}")
            return False
            
        # Copy PDF
        shutil.copy2(source_path, pdf_path)
            
        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(item_metadata, f, indent=2)
            
        print(f"Paper and metadata saved to {paper_dir}")
        return True
        
    except Exception as e:
        print(f"Failed to copy paper {item_metadata['paper_id']}: {str(e)}")
        return False

def download_podcast_library():
    """
    Downloads all papers from the Zotero podcast library collection.
    """
    # Get credentials from environment variables
    LIBRARY_ID = os.getenv("ZOTERO_LIBRARY_ID")
    API_KEY = os.getenv("ZOTERO_API_KEY")
    COLLECTION_NAME = os.getenv("ZOTERO_COLLECTION_NAME")
    
    # Path to Zotero storage (adjust this to match your system)
    ZOTERO_STORAGE = Path.home() / "Zotero/storage"
    
    # Initialize Zotero client
    zot = zotero.Zotero(LIBRARY_ID, 'user', API_KEY)
    
    # Get collection key
    collections = zot.collections()
    collection_key = None
    
    for collection in collections:
        if collection['data']['name'].lower() == COLLECTION_NAME.lower():
            collection_key = collection['key']
            break
    
    if not collection_key:
        raise ValueError(f"Collection '{COLLECTION_NAME}' not found")
    
    # Get items from collection
    items = zot.collection_items(collection_key)
    
    for item in items:
        # Skip attachments and notes
        if item['data']['itemType'] in ['attachment', 'note']:
            continue
            
        # Process metadata
        metadata = process_zotero_metadata(item)
        
        # Get attachments
        attachments = zot.children(item['key'], itemType='attachment')
        
        for attachment in attachments:
            if attachment['data'].get('contentType') == 'application/pdf':
                print(f"Processing {metadata['title']}...")
                copy_zotero_paper(ZOTERO_STORAGE, metadata, attachment)
                break  # Only process the first PDF attachment

if __name__ == "__main__":
    download_podcast_library()