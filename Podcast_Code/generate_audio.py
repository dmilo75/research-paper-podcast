# 3️⃣ Initalize a pipeline
from kokoro import KPipeline
from IPython.display import display, Audio
import soundfile as sf
import numpy as np
import os
import re

import kokoro
print(kokoro.__version__)

# 🇺🇸 'a' => American English
# 🇬🇧 'b' => British English

# Define available voices
VOICES = [
    'af_bella',
    'af_sarah',
    'af_heart',
    'am_michael'
]

pipeline = KPipeline(lang_code='a')

def clean_text(text: str) -> str:
    """
    Clean text by replacing special characters with spaces while preserving contractions
    and compound words.
    
    Args:
        text (str): Input text to clean
        
    Returns:
        str: Cleaned text
    """
    # Replace % with " percent"
    text = text.replace('%', ' percent')
    
    # Replace asterisk with space
    text = text.replace('*', ' ')
    
    # Replace special characters with spaces, keeping apostrophes, hyphens, and basic punctuation
    cleaned = re.sub(r'[^a-zA-Z0-9.,!?\'\-\s]', ' ', text)
    
    # Replace multiple spaces with a single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Strip leading and trailing whitespace
    cleaned = cleaned.strip()
    return cleaned

def generate_audio(text: str, voice_name: str, output_path: str) -> None:
    """
    Generate audio from text using specified voice and save to output path.
    
    Args:
        text (str): Input text to convert to speech
        voice_name (str): Name of the voice to use (must be in VOICES list)
        output_path (str): Path where the final audio file will be saved
    """
    if voice_name not in VOICES:
        raise ValueError(f"Voice {voice_name} not found. Available voices: {VOICES}")
    
    # Clean the text before processing
    cleaned_text = clean_text(text)
    
    # Generate audio segments
    audio_segments = []
    generator = pipeline(
        cleaned_text,  # Use cleaned text instead of raw text
        voice=voice_name,
        speed=1,
        split_pattern=r'\n+'
    )
    
    # Collect all audio segments
    for i, (gs, ps, audio) in enumerate(generator):
        audio_segments.append(audio)
    
    # Concatenate all audio segments
    combined_audio = np.concatenate(audio_segments)
    
    # Save the combined audio file
    sf.write(output_path, combined_audio, 24000)

# Example usage:
if __name__ == "__main__":
    sample_text = "This is a test of the audio generation system."
    generate_audio(sample_text, "af_bella", "output.wav")

