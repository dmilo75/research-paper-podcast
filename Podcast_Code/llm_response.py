import google.generativeai as genai
from typing import Union, Optional, Any, List
from pathlib import Path
import typing_extensions as typing
from pydantic import BaseModel
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
openai_api_key = os.environ.get('OPENAI_API_KEY')
google_api_key = os.environ.get('GOOGLE_API_KEY')

# Initialize clients with keys from environment variables
client = OpenAI(api_key=openai_api_key)
genai.configure(api_key=google_api_key)

class PaperMetadata(BaseModel):
    """Schema for paper metadata"""
    title: str
    authors: List[str]
    journal: Optional[str] = None
    publication_date: Optional[str] = None

class SectionContent(BaseModel):
    """Schema for each section's content"""
    name: str
    content_prompt: str

class PaperSections(BaseModel):
    """Schema for all sections"""
    sections: List[SectionContent]

def get_llm_response(
    prompt: str,
    pdf_path: Optional[Union[str, Path]] = None,
    model_name: str = "gemini-2.0-flash-exp",
    response_schema: Optional[Any] = None
) -> Union[str, dict]:
    """
    Get LLM response for a prompt with optional PDF input and structured output.
    
    Args:
        prompt: Text prompt to send to the LLM
        pdf_path: Optional path to PDF file
        model_name: Name of the Gemini model to use
        response_schema: Optional schema for structured JSON output
        
    Returns:
        Union[str, dict]: Text response or structured JSON from the LLM
    """
    model = genai.GenerativeModel(model_name=model_name)
    
    # If PDF provided, include it in the content
    content = []
    if pdf_path:
        file_ref = genai.upload_file(str(pdf_path))
        content.append(file_ref)
    content.append(f"\n\n{prompt}")
    
    # Generate response with optional schema
    try:
        if response_schema:
            response = model.generate_content(
                content,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1  # Lower temperature for more consistent structured output
                )
            )
            
            # Validate response format
            if not response.text:
                raise ValueError("Empty response received")
            
            return response.text  # Return the text content directly
        else:
            response = model.generate_content(content)
            return response.text
            
    except Exception as e:
        return str(e)

def get_openai_structured_response(
    prompt: str,
    response_schema: BaseModel,
    model: str = "gpt-4o",  # Updated to latest model supporting structured outputs
    temperature: float = 0.1
) -> Union[dict, str]:
    """
    Get structured output from OpenAI using a Pydantic schema.
    
    Args:
        prompt: Text prompt to send to the LLM
        response_schema: Pydantic model defining the expected response structure
        model: OpenAI model to use (must support structured outputs)
        temperature: Temperature setting for response generation
        
    Returns:
        Union[dict, str]: Structured response following the schema or error message
    """
    
    try:
        # Use parse method for automatic schema handling
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": "Extract structured information from the input."},
                {"role": "user", "content": prompt}
            ],
            response_format=response_schema,
            temperature=temperature
        )
        
        # Return parsed response if successful
        return completion.choices[0].message.parsed.model_dump()
        
    except Exception as e:
        raise e