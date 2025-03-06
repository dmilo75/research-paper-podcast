import os
from pathlib import Path
from Podcast_Code.make_podcast import process_paper
import logging
import dropbox
from dropbox.exceptions import ApiError
from pydub import AudioSegment  # for WAV to MP3 conversion
from feedgen.feed import FeedGenerator
from datetime import datetime
import json
import feedparser  # Add this import at the top
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_directories():
    """Create necessary directories if they don't exist."""
    # Create main output directory
    output_base = Path("output")
    output_base.mkdir(exist_ok=True)
    
    # Create NBER papers output subdirectory
    nber_output = output_base / "NBER_Papers"
    nber_output.mkdir(exist_ok=True)
    
    return output_base

def get_output_path(input_path: Path, output_base: Path) -> Path:
    """
    Generate output path based on paper source and ID.
    
    Args:
        input_path: Path to input PDF file (e.g., data/papers/nber/w12345/paper.pdf)
        output_base: Base output directory
    
    Returns:
        Path: Output path for audio file (e.g., output/NBER_Papers/nber_w12345.wav)
    """
    # Extract source and paper_id from path
    # Example path: data/papers/nber/w12345/paper.pdf
    parts = input_path.parts
    source = parts[-3]  # e.g., 'nber'
    paper_id = parts[-2]  # e.g., 'w12345'
    
    # Create unique ID (e.g., nber_w12345)
    unique_id = f"{source}_{paper_id}"
    
    # Create output path with source directory
    output_path = output_base / f"NBER_Papers" / f"{unique_id}.wav"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    return output_path

def initialize_rss_feed() -> FeedGenerator:
    """Create a new RSS feed with basic channel information."""
    fg = FeedGenerator()
    
    # Set required channel elements
    fg.title(os.getenv('RSS_FEED_TITLE', 'Research Paper Podcasts'))
    fg.description(os.getenv('RSS_FEED_DESCRIPTION', 'Audio versions of research papers'))
    fg.author({'name': os.getenv('RSS_FEED_AUTHOR', 'Research Paper Podcasts')})
    fg.language(os.getenv('RSS_FEED_LANGUAGE', 'en'))
    fg.link(href=os.getenv('DROPBOX_BASE_URL', 'https://www.dropbox.com/home/Apps/podcast_folder'), rel='alternate')
    
    # Add timezone information
    current_time = datetime.now().astimezone()
    fg.pubDate(current_time)
    fg.lastBuildDate(current_time)
    
    return fg

def load_existing_feed(output_base: Path) -> tuple[FeedGenerator, set]:
    """
    Load existing RSS feed or create new one.
    
    Returns:
        tuple: (FeedGenerator, set of existing unique_ids)
    """
    feed_path = output_base / 'feed.xml'
    existing_ids = set()
    
    if feed_path.exists():
        try:
            # Parse existing feed
            parsed_feed = feedparser.parse(str(feed_path))
            
            # Print feed contents
            logging.info("Current feed contents:")
            for entry in parsed_feed.entries:
                logging.info(f"Title: {entry.title}")
                logging.info(f"ID: {entry.id}")
                logging.info(f"Link: {entry.link}")
                logging.info("---")
            
            # Create new FeedGenerator with existing channel info
            fg = FeedGenerator()
            fg.title(parsed_feed.feed.title)
            fg.description(parsed_feed.feed.description)
            fg.author({'name': os.getenv('RSS_FEED_AUTHOR', 'Research Paper Podcasts')})
            fg.language(os.getenv('RSS_FEED_LANGUAGE', 'en'))
            fg.link(href=os.getenv('DROPBOX_BASE_URL', 'https://www.dropbox.com/home/Apps/podcast_folder'), rel='alternate')
            
            # Add existing entries
            for entry in parsed_feed.entries:
                # Extract unique_id from entry id (e.g., "pushpod-nber_w12345")
                unique_id = entry.id.split('-')[1]
                existing_ids.add(unique_id)
                
                # Recreate entry in new feed
                fe = fg.add_entry()
                fe.id(entry.id)
                fe.title(entry.title)
                fe.description(entry.description)
                fe.link(href=entry.link)
                fe.published(entry.published)
                
                # Add enclosure if it exists
                if hasattr(entry, 'enclosures') and entry.enclosures:
                    enclosure = entry.enclosures[0]
                    fe.enclosure(url=enclosure.href, length=enclosure.length, type=enclosure.type)
            
            logging.info(f"Loaded existing feed with {len(existing_ids)} entries")
            return fg, existing_ids
            
        except Exception as e:
            logging.error(f"Error loading existing feed: {e}")
            logging.info("Creating new feed")
            return initialize_rss_feed(), existing_ids
    else:
        logging.info("No existing feed found. Creating new feed")
        return initialize_rss_feed(), existing_ids

def add_podcast_to_feed(fg: FeedGenerator, audio_path: Path, metadata: dict, url: str) -> FeedGenerator:
    """
    Add a single podcast entry to the feed.
    
    Args:
        fg: FeedGenerator object
        audio_path: Path to audio file
        metadata: Paper metadata
        url: Dropbox URL for audio file
    """
    logging.info(f"Adding {metadata['unique_id']} to feed...")
    
    fe = fg.add_entry()
    fe.id(f"pushpod-{metadata['unique_id']}")
    fe.title(metadata['title'])
    
    # Create description with authors and abstract
    authors_str = ', '.join(metadata['authors'])
    description = f"Authors: {authors_str}\n\n{metadata['abstract']}"
    fe.description(description)
    
    # Convert URL to direct download format
    direct_url = url.replace('www.dropbox.com', 'dl.dropboxusercontent.com')
    direct_url = direct_url.replace('?dl=0', '?raw=1')
    
    fe.link(href=direct_url)
    
    # Add timezone information to publication date
    pub_date = datetime.fromtimestamp(audio_path.stat().st_mtime).astimezone()
    fe.published(pub_date)
    
    # Add enclosure with correct MIME type and file size
    file_size = str(audio_path.stat().st_size)
    fe.enclosure(url=direct_url, length=file_size, type='audio/wav')
    
    logging.info(f"Successfully added {metadata['unique_id']} to feed")
    
    return fg

def verify_feed_content(dbx, feed_path: Path):
    """Verify feed content in Dropbox matches local file."""
    logging.info("Verifying feed content...")
    
    # Read local feed
    with open(feed_path) as f:
        local_feed = feedparser.parse(f.read())
    logging.info(f"Local feed has {len(local_feed.entries)} entries")
    for entry in local_feed.entries:
        logging.info(f"Local feed entry: {entry.title}")
    
    # Get Dropbox feed
    dropbox_folder = os.getenv('DROPBOX_FOLDER_PATH', '/Apps/podcast_folder')
    dropbox_path = f"{dropbox_folder}/{feed_path.name}"
    try:
        response = dbx.files_download(dropbox_path)[1]
        dropbox_feed = feedparser.parse(response.content)
        logging.info(f"Dropbox feed has {len(dropbox_feed.entries)} entries")
        for entry in dropbox_feed.entries:
            logging.info(f"Dropbox feed entry: {entry.title}")
    except Exception as e:
        logging.error(f"Error reading Dropbox feed: {e}")
    
    return local_feed, dropbox_feed

def process_all_papers(test_mode=False):
    """Process all papers in the data/papers directory that haven't been processed yet."""
    # Setup directories and Dropbox
    output_base = setup_directories()
    dbx = setup_dropbox()
    
    # Load or initialize RSS feed
    fg, existing_ids = load_existing_feed(output_base)
    feed_path = output_base / 'feed.xml'
    
    # Save and upload initial feed
    fg.rss_file(str(feed_path))
    feed_url = upload_to_dropbox(dbx, feed_path)
    logging.info(f"Initial RSS Feed available at: {feed_url}")
    
    # Update base paths
    papers_dir = Path("Data/papers")
    
    # Get all PDF files in papers directory
    pdf_files = list(papers_dir.rglob("paper.pdf"))
    
    if not pdf_files:
        logging.warning("No PDF files found in data/papers directory!")
        return
    
    logging.info(f"Found {len(pdf_files)} PDF files")
    
    # In test mode, only process the first file
    if test_mode:
        pdf_files = pdf_files[:1]
        logging.info("TEST MODE: Processing only first PDF file")
    
    # Process each PDF file
    for pdf_path in pdf_files:
        # Load metadata
        metadata_path = pdf_path.parent / "metadata.json"
        try:
            with open(metadata_path) as f:
                metadata = json.load(f)
        except Exception as e:
            logging.error(f"Error loading metadata for {pdf_path}: {e}")
            continue
        
        # Skip if already in feed
        if metadata['unique_id'] in existing_ids:
            logging.info(f"Skipping {metadata['unique_id']}, already in feed")
            continue
            
        # Generate output path using unique ID
        output_path = get_output_path(pdf_path, output_base)
        
        logging.info(f"Processing {metadata['unique_id']}: {metadata['title']}")
        try:
            # Create WAV file
            process_paper(str(pdf_path), str(output_path), metadata)
            
            # Upload WAV directly to Dropbox and get URL
            url = upload_to_dropbox(dbx, output_path)
            
            # Add to feed and verify
            fg = add_podcast_to_feed(fg, output_path, metadata, url)
            
            # Save feed after each addition
            feed_path = output_base / 'feed.xml'
            fg.rss_file(str(feed_path))
            
            # Upload updated feed to Dropbox
            feed_url = upload_to_dropbox(dbx, feed_path)
            
            # Verify feed content
            local_feed, dropbox_feed = verify_feed_content(dbx, feed_path)
            
            # Add to existing IDs to prevent reprocessing
            existing_ids.add(metadata['unique_id'])
            
            logging.info(f"Successfully processed {metadata['unique_id']}")
            
        except Exception as e:
            logging.error(f"Error processing {metadata['unique_id']}: {str(e)}")
            continue
    
    logging.info("Finished processing papers")

def setup_dropbox():
    """Setup Dropbox client with refresh token capabilities."""
    APP_KEY = os.getenv('DROPBOX_APP_KEY')
    APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
    REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN')
    
    try:
        dbx = dropbox.Dropbox(
            oauth2_refresh_token=REFRESH_TOKEN,
            app_key=APP_KEY,
            app_secret=APP_SECRET
        )
        dbx.users_get_current_account()
        logging.info("Successfully connected to Dropbox")
        return dbx
    except Exception as e:
        logging.error(f"Failed to connect to Dropbox: {str(e)}")
        raise

def convert_to_mp3(wav_path: Path, output_base: Path) -> Path:
    """Convert WAV to MP3 for better streaming."""
    mp3_path = output_base / f"{wav_path.stem}.mp3"
    audio = AudioSegment.from_wav(str(wav_path))
    audio.export(str(mp3_path), format="mp3", bitrate="192k")
    return mp3_path

def upload_to_dropbox(dbx, file_path: Path) -> str:
    """Upload a file to Dropbox and return its shareable link."""
    dropbox_folder = os.getenv('DROPBOX_FOLDER_PATH', '/Apps/podcast_folder')
    dropbox_path = f"{dropbox_folder}/{file_path.name}"
    
    try:
        # Force upload, don't skip
        with open(file_path, 'rb') as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        logging.info(f"Successfully uploaded {file_path.name} to Dropbox")
        
        # Create a shared link
        shared_link = dbx.sharing_create_shared_link(dropbox_path)
        # Convert to direct download link
        dl_url = shared_link.url.replace('?dl=0', '?raw=1')
        return dl_url
    
    except ApiError as e:
        logging.error(f'Error uploading {file_path}: {str(e)}')
        raise

def create_rss_feed(output_base: Path, processed_files: dict, feed_url: str = None):
    """Create RSS feed for processed audio files."""
    fg = FeedGenerator()
    
    # Set required channel elements
    fg.title(os.getenv('RSS_FEED_TITLE', 'Research Paper Podcasts'))
    fg.description(os.getenv('RSS_FEED_DESCRIPTION', 'Audio versions of research papers'))
    fg.author({'name': os.getenv('RSS_FEED_AUTHOR', 'Research Paper Podcasts')})
    fg.language(os.getenv('RSS_FEED_LANGUAGE', 'en'))
    
    # Add timezone information to datetime objects
    current_time = datetime.now().astimezone()
    fg.pubDate(current_time)
    fg.lastBuildDate(current_time)
    
    # Set feed links
    if feed_url:
        # Convert feed URL to direct download format
        feed_url = feed_url.replace('www.dropbox.com', 'dl.dropboxusercontent.com')
        feed_url = feed_url.replace('?dl=0', '?raw=1')
        fg.link(href=feed_url, rel='self')
    fg.link(href=os.getenv('DROPBOX_BASE_URL', 'https://www.dropbox.com/home/Apps/podcast_folder'), rel='alternate')
    
    # Add entries for each audio file
    for audio_file, url in processed_files.items():
        fe = fg.add_entry()
        fe.id(f"pushpod-{audio_file.stem}")
        fe.title(audio_file.stem)
        fe.description(f"Audio version of {audio_file.stem}")
        
        # Convert URL to direct download format
        direct_url = url.replace('www.dropbox.com', 'dl.dropboxusercontent.com')
        direct_url = direct_url.replace('?dl=0', '?raw=1')
        
        fe.link(href=direct_url)
        
        # Add timezone information to publication date
        pub_date = datetime.fromtimestamp(audio_file.stat().st_mtime).astimezone()
        fe.published(pub_date)
        
        # Add enclosure with correct MIME type and file size
        file_size = str(audio_file.stat().st_size)
        fe.enclosure(url=direct_url, length=file_size, type='audio/wav')
    
    feed_path = output_base / 'feed.xml'
    fg.rss_file(str(feed_path))
    return feed_path

if __name__ == "__main__":
    # Set test_mode=True to process only one paper
    process_all_papers(test_mode=False)



# %%
