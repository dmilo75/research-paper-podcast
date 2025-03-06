import logging
from pathlib import Path
from typing import Dict, Optional
try:
    # When imported as a module
    from .llm_response import get_llm_response, get_openai_structured_response, PaperMetadata, PaperSections
    from .generate_audio import generate_audio, VOICES
except ImportError:
    # When run directly
    from llm_response import get_llm_response, get_openai_structured_response, PaperMetadata, PaperSections
    from generate_audio import generate_audio, VOICES
import os
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Shared prompts
SHARED_PROMPTS = {
    'format': {
        'five_sentences': """
        RESPOND WITH EXACTLY FIVE SENTENCES that are clear and standalone.
        Start each sentence directly with content.
        Do not include any introductory phrases or transitions.
        Use engaging, conversational style while maintaining accuracy.
        """,
        'clarity': """
        Spell out all acronyms and abbreviations in full throughout the entire response. DO NOT use any acronyms or abbrevations! 
        Write numbers as digits for quantities and percentages (e.g., 5%, 10 participants).
        Use clear, everyday language where possible without sacrificing accuracy.
        """
    },
    'structure': {
        'academic_components': """
        - Core argument and motivation
        - Theoretical framework
        - Methodology and approach
        - Evidence and analysis
        - Key implications
        """,
    }
}

# Dynamic section prompt
SECTION_PROMPT = """
Generate 2-4 sections that best explain this paper's content.

For empirical papers, consider including:
- Data sources, sample, and key variables
- Research design and methodology
- Key findings and implications

For theoretical/model papers, consider including:
- Intuitive model explanation with simple examples
- Key mechanisms and trade-offs
- Main insights and applications

For each section provide:
1. A clear, short, and abstract section name
2. A brief description of what content should be covered in that section

Format your response as a JSON list of objects with 'name' and 'content_prompt' fields.
Keep each content_prompt focused and specific about what should be covered.
"""

def get_structured_metadata(pdf_path: str) -> dict:
    """Extract structured metadata from paper using two-phase approach."""
    logging.info("Extracting paper metadata...")
    
    # Phase 1: Get unstructured data from Gemini
    raw_prompt = """
    Extract the following information from the paper:
    - Title
    - Authors 
    - Journal name (if available)0
    - Publication date (if available)
    
    Provide all available information in a detailed response.
    """
    raw_response = get_llm_response(raw_prompt, pdf_path)

    print(raw_response)
    
    # Phase 2: Structure with OpenAI
    return get_openai_structured_response(raw_response, PaperMetadata)

def get_high_school_summary(pdf_path: str, num_sentences: int = 5) -> str:
    """Generate a summary at high school level with configurable length."""
    logging.info("Generating high-school level summary...")
    summary_prompt = f"""
    Summarize this research paper in EXACTLY {num_sentences} sentences that a high school student could understand.
    Focus on:
    1. What problem they're trying to solve
    2. The current gap in knowledge or understanding
    3. What they did
    4. What they found
    5. How this changes or advances the field
    
    Respond with only the summary text.
    """
    return get_llm_response(summary_prompt, pdf_path)

def get_final_takeaways(script: str, num_sentences: int = 5) -> str:
    """Generate final takeaways based on the podcast script."""
    logging.info("Generating final takeaways...")
    summary_prompt = f"""
    {SHARED_PROMPTS['format']['five_sentences']}
    Cover:
    {SHARED_PROMPTS['structure']['academic_components']}

    # Podcast script:
    {script}
    """
    return get_llm_response(summary_prompt)

def get_all_section_bullets_at_once(pdf_path: str) -> dict:
    """Generate sections and bullet points using two-phase approach."""
    logging.info("Generating dynamic sections and bullet points...")
    
    # Phase 1: Get unstructured content from Gemini
    raw_response = get_llm_response(SECTION_PROMPT, pdf_path)
    
    # Phase 2: Structure with OpenAI
    return get_openai_structured_response(raw_response, PaperSections)

def get_next_voice(voices: list[str], current_index: int) -> tuple[str, int]:
    """Get the next voice in rotation."""
    next_index = (current_index + 1) % len(voices)
    return voices[next_index], next_index

def get_background_overview(pdf_path: str) -> str:
    """Generate a background overview focusing on the topic's literature context."""
    logging.info("Generating background conceptual overview...")
    overview_prompt = """
    Provide a conceptual overview focusing solely on the background and literature context of the topic.
    Do not mention what the paper specifically does. Instead, consider:
    - Explaining why this research topic is important
    - Summarizing relevant literature or common findings in the field
    - Highlighting general knowledge and established theories related to this topic
    Use clear, engaging, and concise language.
    """
    return get_llm_response(overview_prompt, pdf_path)

def generate_section_details(pdf_path: str, section: dict, all_bullets: str) -> str:
    """Generate detailed content for a specific section using bullet points."""
    logging.info(f"Generating {section['name']} section...")
    
    full_prompt = f"""
    {SHARED_PROMPTS['format']['five_sentences']}
    {SHARED_PROMPTS['format']['clarity']}
    
    # IMPORTANT: 
    - Do not use any introductory or concluding phrases
    - Start directly with the content
    - Use conversational, engaging language
    - Maintain technical accuracy
    - You are writing the section on {section['name']}
    
    # Section-specific focus:
    {section['content_prompt']}

    Context from paper:
    # Bullet points for all sections:
    {all_bullets}
    """
    
    content = get_llm_response(full_prompt, pdf_path)
    logging.info(f"{section['name']} section generation complete")
    return content

def combine_audio_files(file_list: list[str], output_file: str, target_sr: int = 44100):
    """Concatenate audio files from the provided list and write to output_file."""
    from pathlib import Path
    import soundfile as sf
    import numpy as np
    from scipy import signal

    # Ensure that the output directory exists
    output_dir = Path(output_file).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    combined = []
    
    for file in file_list:
        data, sr = sf.read(file)
        # Resample if the sample rate doesn't match target
        if sr != target_sr:
            logging.info(f"Resampling {file} from {sr}Hz to {target_sr}Hz")
            num_samples = int(len(data) * target_sr / sr)
            data = signal.resample(data, num_samples)
        combined.append(data)
    
    final_audio = np.concatenate(combined)
    sf.write(output_file, final_audio, target_sr)

def cleanup_temp_files(temp_dir: Path) -> None:
    """Remove temporary audio directory and all its contents."""
    if temp_dir.exists():
        # First remove all files in the directory
        for file in temp_dir.glob('*'):
            try:
                file.unlink()
            except FileNotFoundError:
                pass
        
        # Then remove the directory itself
        try:
            temp_dir.rmdir()
        except OSError as e:
            logging.warning(f"Could not remove temp directory: {e}")

def make_podcast(pdf_path: str, output_path: str, metadata_dict: dict, summary_sentences: int = 5) -> None:
    """Create a podcast from a research paper PDF."""
    # Check if output file already exists
    if Path(output_path).exists():
        logging.info(f"Podcast already exists at {output_path}, skipping generation")
        return

    logging.info(f"Starting podcast creation for {pdf_path}")
    
    # Create temporary directory for audio files
    temp_dir = Path("temp_audio")
    temp_dir.mkdir(exist_ok=True)
    
    # Initialize voice rotation
    voices = VOICES
    current_voice_idx = -1
    
    #If metadata dict is empty then generate one
    if not metadata_dict:
        metadata_dict = get_structured_metadata(pdf_path)

    # Get high school summary
    high_school_summary = get_high_school_summary(pdf_path, summary_sentences)

    # Get all section bullet points
    all_bullet_points = get_all_section_bullets_at_once(pdf_path)
    
    logging.info("Generated all section bullet points")
    
    # Generate audio sections with rotating voices
    audio_files = []
    full_script = []  # Store the complete script for final takeaways
    
    # Metadata
    metadata_text = f"Title: {metadata_dict['title']}."
    if metadata_dict.get('authors'):
        author_names = metadata_dict['authors']
        metadata_text += f" By {', '.join(author_names)}."
    if metadata_dict.get('journal'):
        metadata_text += f" Published in {metadata_dict['journal']}."
    if metadata_dict.get('publication_date'):
        metadata_text += f" Date: {metadata_dict['publication_date']}."
    
    metadata_file = temp_dir / "metadata.wav"
    generate_audio(metadata_text, voices[0], str(metadata_file))
    audio_files.append(metadata_file)
    full_script.append(metadata_text)
    
    # High school summary
    voice, current_voice_idx = get_next_voice(voices, current_voice_idx)
    high_school_intro = "First, let me give you a simple overview that anyone can understand."
    summary_file = temp_dir / "high_school_summary.wav"
    generate_audio(high_school_intro + " " + high_school_summary, voice, str(summary_file))
    audio_files.append(summary_file)
    full_script.append(high_school_intro + " " + high_school_summary)
    
    # Add background overview
    voice, current_voice_idx = get_next_voice(voices, current_voice_idx)
    background_intro = "Now, let me provide some context about the broader research landscape."
    background_content = get_background_overview(pdf_path)
    background_file = temp_dir / "background_overview.wav"
    generate_audio(background_intro + " " + background_content, voice, str(background_file))
    audio_files.append(background_file)
    full_script.append(background_intro + " " + background_content)
    
    for section in all_bullet_points["sections"]:
        logging.info(f"Processing section: {section['name']}")
        voice, current_voice_idx = get_next_voice(voices, current_voice_idx)
        # Convert bullet list into a string for the prompt
        bullet_str = "\n".join(section.get("bullets", []))
        content = generate_section_details(pdf_path, section, bullet_str)
        section_file = temp_dir / f"{section['name']}.wav"
        generate_audio(content, voice, str(section_file))
        audio_files.append(section_file)
        full_script.append(content)
        logging.info(f"Completed section: {section['name']}")
    
    # Final takeaways
    voice, current_voice_idx = get_next_voice(voices, current_voice_idx)
    script_text = "\n\n".join(full_script)
    final_takeaways = get_final_takeaways(script_text)
    takeaway_intro = "To wrap up, here are the key takeaways from our discussion:"
    takeaway_file = temp_dir / "final_takeaways.wav"
    full_text = takeaway_intro + " " + final_takeaways
    generate_audio(full_text, voice, str(takeaway_file))
    audio_files.append(takeaway_file)

    print(full_text)
    
    # Combine all audio files
    combine_audio_files([str(f) for f in audio_files], output_path)
    
    # Cleanup
    cleanup_temp_files(temp_dir)

def process_paper(pdf_path, output_path,metadata_dict) -> None:
    """Process a single paper, with proper cleanup handling."""
    temp_dir = Path("temp_audio")
    try:
        make_podcast(pdf_path, output_path,metadata_dict)
    except Exception as e:
        logging.error(f"Error processing {pdf_path}: {e}")
        raise e
    finally:
        cleanup_temp_files(temp_dir)



if __name__ == "__main__":

    #Change directory back one
    os.chdir("..")

    # Example usage
    pdf_path = '/Users/dmilo/Dropbox/Side Projects/Kokoro/Data/NBER Papers/nber_w33405.pdf'
    output_path = "output/podcast.wav"
    
