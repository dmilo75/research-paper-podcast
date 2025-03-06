# Research Paper Podcast Generator

A tool that converts academic research papers into audio podcasts, creating an RSS feed that can be consumed in any podcast player.

## Overview

This project automates the process of turning research papers (PDFs) into audio podcasts. It handles:

1. Collecting papers from various sources (Zotero, NBER, etc.)
2. Processing the papers (text extraction, formatting)
3. Converting text to speech using advanced AI models
4. Creating and maintaining an RSS feed
5. Hosting the audio files and feed on Dropbox

## Project Structure

### Main Components

- **Make_All_Podcasts.py**: The main script that orchestrates the entire process
- **Scraping/**: Directory containing scripts for collecting papers from different sources
  - **zotero.py**: Integrates with Zotero to download papers and metadata
- **Podcast_Code/**: Contains the core functionality for processing papers and generating audio
  - **make_podcast.py**: Processes papers and generates audio
  - **llm_response.py**: Uses language models (OpenAI GPT-4 and Google Gemini) to improve text processing
  - **generate_audio.py**: Converts processed text to speech using Kokoro TTS

### Output

- **output/**: Directory where generated audio files and the RSS feed are stored
  - **NBER_Papers/**: Subdirectory for papers from NBER
  - **feed.xml**: The RSS feed file that podcast players can subscribe to

## How It Works

### Paper Collection

The system can collect papers from multiple sources:

1. **Zotero Integration**: Connects to your Zotero library to download papers and metadata from a specified collection
2. **Manual Addition**: Papers can also be manually added to the Data directory

### Paper Processing

For each paper, the system:

1. Extracts text from the PDF
2. Uses AI language models to:
   - Generate a high-school level summary
   - Create structured sections with key points
   - Format content for better listening experience
   - Provide final takeaways

#### AI Models Used

The system leverages two complementary AI models:

- **Google Gemini 2.0 Flash Experimental**: Used for most text processing tasks. This experimental model is currently free to use and provides excellent performance for general text processing and summarization.

- **OpenAI GPT-4**: Used specifically for structured responses where strict output formatting is required. While Gemini excels at general understanding, OpenAI's models are more compliant with structured output requirements, making them ideal for generating consistent, well-formatted content sections.

The combination of these models allows for both cost-effective processing and high-quality structured outputs.

### Text-to-Speech Conversion

The processed text is converted to speech using:

1. **Kokoro TTS**: A high-quality, open-source text-to-speech system that can run locally
2. **Multiple Voices**: Different voices are used for different sections to create a more engaging listening experience
3. **Audio Processing**: The generated audio is cleaned and formatted for optimal podcast listening

#### About Kokoro TTS

Kokoro is a lightweight, open-source text-to-speech platform that can run entirely locally on your machine. Despite its small footprint, it produces voice quality that rivals commercial services like ElevenLabs, performing exceptionally well in open benchmarks on Hugging Face.

Key advantages of Kokoro include:
- **Local processing**: No need to send data to external servers
- **Privacy**: All processing happens on your machine
- **No usage limits**: Unlike cloud-based services with token limits
- **Multiple voices**: Supports various voices with different characteristics
- **High-quality output**: Near commercial-grade voice synthesis

### RSS Feed Generation

The system creates and maintains an RSS feed that:

1. Contains entries for each processed paper
2. Includes metadata (title, authors, abstract)
3. Links to the audio files hosted on Dropbox
4. Can be subscribed to in any podcast player

#### Using the RSS Feed in Podcast Apps

One of the key advantages of this system is that it generates a standard RSS feed that works with virtually any podcast app:

- **iOS Podcasts App**: Simply copy the RSS feed URL and add it as a custom podcast source
- **Spotify**: Use a service like Podcast Import to add your custom feed
- **Pocket Casts, Overcast, Castro**: These apps directly support adding custom RSS feeds
- **Google Podcasts**: Add the feed URL to subscribe to your research papers

This approach means you can:
- Listen to research papers alongside your regular podcasts
- Use all podcast player features (speed control, bookmarks, etc.)
- Download papers for offline listening
- Track your listening progress across devices
- Receive notifications when new papers are added

## Setup Instructions

### Prerequisites

1. Python 3.8 or higher
2. A Dropbox account
3. A Zotero account (for paper collection)
4. OpenAI API key (for text processing)
5. Google API key (for Gemini model access)
6. Kokoro TTS setup (for text-to-speech)

### Environment Setup

1. Clone this repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following variables:
   ```
   # API Keys
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_API_KEY=your_google_api_key
   
   # Dropbox Configuration
   DROPBOX_APP_KEY=your_dropbox_app_key
   DROPBOX_APP_SECRET=your_dropbox_app_secret
   DROPBOX_REFRESH_TOKEN=your_dropbox_refresh_token
   DROPBOX_FOLDER_PATH=/Apps/podcast_folder
   DROPBOX_BASE_URL=https://www.dropbox.com/home/Apps/podcast_folder
   
   # Zotero API Credentials
   ZOTERO_LIBRARY_ID=your_zotero_library_id
   ZOTERO_API_KEY=your_zotero_api_key
   ZOTERO_COLLECTION_NAME=podcast_library
   
   # RSS Feed Configuration
   RSS_FEED_TITLE=Research Paper Podcasts
   RSS_FEED_DESCRIPTION=Audio versions of research papers
   RSS_FEED_AUTHOR=Research Paper Podcasts
   RSS_FEED_LANGUAGE=en
   ```

### Zotero Setup

[Zotero](https://www.zotero.org/) is a free, open-source reference management software that makes collecting research papers easy.

1. **Create a Zotero account**: Sign up at [zotero.org](https://www.zotero.org/)
2. **Install the Zotero desktop application**: Download from [zotero.org/download](https://www.zotero.org/download)
3. **Install the Zotero Connector browser extension**: Available for [Chrome](https://chrome.google.com/webstore/detail/zotero-connector/ekhagklcjbdpajgpjgmbionohlpdbjgc), [Firefox](https://www.zotero.org/download/), and [Safari](https://www.zotero.org/download/)
4. **Create a collection**: In the Zotero desktop app, create a new collection called "podcast_library" (or whatever name you specified in your .env file)
5. **Get your API credentials**:
   - Go to [zotero.org/settings/keys](https://www.zotero.org/settings/keys)
   - Create a new private key
   - Set permissions to allow read/write access
   - Copy the key to your .env file as ZOTERO_API_KEY
   - Your library ID can be found in the URL when you're logged into the Zotero web interface (e.g., https://www.zotero.org/users/1234567/library)

### Using Zotero to Collect Papers

1. **Browse to an academic paper**: When you find a paper you want to add to your podcast library, click the Zotero Connector icon in your browser
2. **Save to your collection**: Select the "podcast_library" collection
3. **Verify download**: The paper and its metadata will be downloaded to your Zotero library

Zotero can automatically extract metadata (title, authors, abstract, etc.) from many academic websites, including:
- Google Scholar
- JSTOR
- PubMed
- arXiv
- Most university library websites
- Most academic journal websites

For websites without built-in support, you can still save the page and manually add metadata.

### Dropbox Setup

1. Create a Dropbox app at [dropbox.com/developers/apps](https://www.dropbox.com/developers/apps)
   - Choose "App folder" access
   - Name your app (e.g., "ResearchPodcasts")
2. Under the "Permissions" tab, enable:
   - files.content.write
   - files.content.read
   - sharing.write
3. Generate an access token and refresh token:
   - Under "OAuth 2", click "Generate" for the refresh token
   - Add these credentials to your .env file

### Kokoro TTS Setup

The project uses Kokoro TTS for high-quality text-to-speech conversion:

1. Install the Kokoro package:
   ```bash
   pip install kokoro
   ```
2. The system supports multiple voices:
   - af_bella: Female voice with American accent
   - af_sarah: Female voice with American accent
   - af_heart: Female voice with American accent
   - am_michael: Male voice with American accent

## Usage

To run the full process:

```bash
python Make_All_Podcasts.py
```

This will:
1. Connect to your Zotero library and download any new papers
2. Process each paper (extract text, format, etc.)
3. Generate audio for each paper
4. Create/update the RSS feed
5. Upload everything to Dropbox

The RSS feed URL will be printed to the console when the process completes. You can add this URL to any podcast player to subscribe to your research paper podcast.

## Customization

You can customize various aspects of the podcast generation:

### Voice Settings

Edit the `VOICES` list in `Podcast_Code/generate_audio.py` to change the available voices.

### RSS Feed Metadata

Modify the RSS feed settings in your `.env` file:
```
RSS_FEED_TITLE=Your Custom Title
RSS_FEED_DESCRIPTION=Your custom description
RSS_FEED_AUTHOR=Your Name
```

### Paper Processing

The prompts in `Podcast_Code/make_podcast.py` can be extensively customized to tailor the script to your preferences:

- **SHARED_PROMPTS**: Controls formatting and structure of the content
  - Adjust the `five_sentences` prompt to change how summaries are structured
  - Modify the `clarity` prompt to change language style and complexity
  - Edit the `academic_components` to focus on different aspects of papers

- **SECTION_PROMPT**: Determines how sections are generated and what they focus on
  - Add specific instructions for different types of papers (empirical, theoretical, etc.)
  - Change the number of sections generated
  - Adjust the level of detail in each section

By modifying these prompts, you can create podcasts that range from highly technical and detailed to simplified and accessible, depending on your audience and preferences.

## Troubleshooting

If you encounter issues:
1. Check the log output for error messages
2. Verify your API credentials in the .env file
3. Ensure your Dropbox app has the necessary permissions
4. Check that your Zotero collection exists and contains papers
5. For TTS issues, verify that Kokoro is properly installed

## License

[Your license information here]

## Acknowledgements

This project uses several open-source libraries and APIs:
- [pyzotero](https://github.com/urschrei/pyzotero) for Zotero integration
- [dropbox](https://github.com/dropbox/dropbox-sdk-python) for Dropbox integration
- [feedgen](https://github.com/lkiesow/python-feedgen) for RSS feed generation
- [pydub](https://github.com/jiaaro/pydub) for audio processing
- [Kokoro TTS](https://github.com/reeselevine/kokoro) for text-to-speech conversion
- [OpenAI API](https://openai.com/api/) for GPT-4 language model
- [Google Generative AI](https://ai.google.dev/) for Gemini language model 