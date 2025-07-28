"""
text_generator.py
Updated to use official OpenAI API first, then DeepSeek, then LMStudio as fallback.
"""

import os
import time
import lmstudio as lms
from openai import OpenAI

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from utils import (
    read_file, 
    create_output_folder, 
    write_text_file
)

# Get API keys from environment variables
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
FINE_TUNED_FOR_STORIES = os.getenv("FINE_TUNED_FOR_STORIES")

# Initialize the official OpenAI client (PRIMARY)
openai_client = OpenAI(
    api_key=FINE_TUNED_FOR_STORIES
    # No base_url needed - uses official OpenAI API
)

# Initialize the DeepSeek client using OpenAI SDK format (SECONDARY)
deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.chatanywhere.tech/v1"
)


def validate_api_keys():
    """Validate that required API keys are present."""
    missing_keys = []
    
    if not FINE_TUNED_FOR_STORIES:
        missing_keys.append("FINE_TUNED_FOR_STORIES")
    if not DEEPSEEK_API_KEY:
        missing_keys.append("DEEPSEEK_API_KEY")
    
    if missing_keys:
        print(f"✗ Missing API keys: {', '.join(missing_keys)}")
        print("Please add them to your .env file")
        return False
    return True


def generate_with_openai(system_prompt: str, user_prompt: str, content_type: str = "content") -> str:
    """
    Generate content using official OpenAI API.
    
    Args:
        system_prompt (str): System prompt for the model
        user_prompt (str): User prompt/request
        content_type (str): Type of content being generated (for logging)
        
    Returns:
        str: Generated content or None if failed
    """
    try:
        print(f"✓ Attempting {content_type} generation with Official OpenAI API...")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        modelID = "ft:gpt-4o-mini-2024-07-18:personal:spurned::BrmvSeQE"

        completion = openai_client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:personal:spunred:BrmvSeQE",  # <-- lowercase ID
            messages=messages,
            temperature=0.7
        )


        
        result = completion.choices[0].message.content
        print(f"✓ Official OpenAI {content_type} generation successful!")
        return result
        
    except Exception as e:
        print(f"✗ Official OpenAI {content_type} generation failed: {e}")
        return None


def generate_with_deepseek(system_prompt: str, user_prompt: str, content_type: str = "content") -> str:
    """
    Generate content using DeepSeek API with OpenAI SDK format.
    
    Args:
        system_prompt (str): System prompt for the model
        user_prompt (str): User prompt/request
        content_type (str): Type of content being generated (for logging)
        
    Returns:
        str: Generated content or None if failed
    """
    try:
        print(f"✓ Attempting {content_type} generation with DeepSeek...")
        
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            stream=False
        )
        
        content = response.choices[0].message.content
        print(f"✓ DeepSeek {content_type} generation successful!")
        return content
        
    except Exception as e:
        print(f"✗ DeepSeek {content_type} generation failed: {e}")
        return None


def generate_with_lmstudio(system_prompt: str, user_prompt: str, content_type: str = "content") -> str:
    """
    Generate content using LMStudio as final fallback.
    
    Args:
        system_prompt (str): System prompt for the model
        user_prompt (str): User prompt/request
        content_type (str): Type of content being generated (for logging)
        
    Returns:
        str: Generated content or None if failed
    """
    try:
        print(f"✓ Attempting {content_type} generation with LMStudio (final fallback)...")
        
        # Give the server some time if it was just started
        time.sleep(2)
        
        model_name = "gemma-3-12b-it"
        model = lms.llm(model_name)
        
        messages = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        response = model.respond(messages)
        result = response.content
        
        model.unload()
        print(f"✓ LMStudio {content_type} generation successful!")
        return result
        
    except Exception as e:
        print(f"✗ LMStudio {content_type} generation failed: {e}")
        return None


def generate_content_with_fallback(system_prompt: str, user_prompt: str, content_type: str = "content") -> str:
    """
    Generate content with Official OpenAI primary, DeepSeek secondary, and LMStudio final fallback.
    
    Args:
        system_prompt (str): System prompt for the model
        user_prompt (str): User prompt/request
        content_type (str): Type of content being generated (for logging)
        
    Returns:
        str: Generated content or None if all methods fail
    """
    # Try Official OpenAI first
    result = generate_with_openai(system_prompt, user_prompt, content_type)
    
    if result is not None:
        return result
    
    # If OpenAI fails, try DeepSeek
    print(f"⚠ Official OpenAI failed for {content_type}, trying DeepSeek...")
    result = generate_with_deepseek(system_prompt, user_prompt, content_type)
    
    if result is not None:
        return result
    
    # If DeepSeek also fails, try LMStudio
    print(f"⚠ DeepSeek also failed for {content_type}, trying LMStudio fallback...")
    result = generate_with_lmstudio(system_prompt, user_prompt, content_type)
    
    if result is not None:
        return result
    
    # If all methods fail
    print(f"✗ All methods (OpenAI, DeepSeek, LMStudio) failed for {content_type} generation!")
    return None


def generate_text_content(custom_title=None):
    """
    Generate title and story content using Official OpenAI (primary), DeepSeek (secondary), and LMStudio (fallback).
    
    Args:
        custom_title (str, optional): Custom title to use instead of generating one
        
    Returns:
        tuple: (title, story, output_folder)
    """
    try:
        # Validate API keys first
        if not validate_api_keys():
            print("✗ Cannot proceed without valid API keys")
            return None, None, None
        
        # File paths for system prompts
        title_prompt_path = "System_Title_Prompt.txt"
        story_prompt_path = "Story_System_Prompt.txt"
        
        print("✓ Reading system prompts...")
        system_prompt_title = read_file(title_prompt_path)
        system_prompt_story = read_file(story_prompt_path)

        # Handle title generation or use custom title
        if custom_title:
            print(f"✓ Using custom title: {custom_title}")
            response_title = custom_title
        else:
            title_prompt = "Generate a creative title for a story"
            response_title = generate_content_with_fallback(
                system_prompt_title, 
                title_prompt, 
                "title"
            )
            
            if response_title is None:
                print("✗ Failed to generate title with all methods")
                return None, None, None
        
        # Create output folder for this run
        output_base = "/media/lord/One Touch/DaVinci Vids"
        output_folder = create_output_folder(output_base, response_title)
        write_text_file(output_folder, "title.txt", response_title)
        print("✓ Title saved successfully")

        # Generate story using the title
        story_user_content = response_title 
        response_story = generate_content_with_fallback(
            system_prompt_story, 
            story_user_content, 
            "story"
        )
        
        if response_story is None:
            print("✗ Failed to generate story with all methods")
            return None, None, None
        
        write_text_file(output_folder, "story.txt", response_story)
        print("✓ Story saved successfully")

        return response_title, response_story, output_folder
          
    except Exception as e:
        print(f"✗ Unexpected error in text generation: {e}")
        return None, None, None


def generate_all_stories_bulk(num_runs: int, custom_titles: list = None):
    """
    Generate all stories in bulk before processing audio/video.
    
    Args:
        num_runs (int): Number of stories to generate
        custom_titles (list, optional): List of custom titles to use
        
    Returns:
        list: List of tuples (title, story, output_folder) for successful generations
    """
    print(f"\n{'='*50}")
    print(f"🚀 BULK STORY GENERATION PHASE")
    print(f"Generating {num_runs} stories...")
    print(f"{'='*50}")
    
    successful_stories = []
    
    for i in range(num_runs):
        print(f"\n📝 Generating story {i+1}/{num_runs}")
        print("-" * 30)
        
        # Use custom title if available, otherwise None for auto-generation
        current_title = custom_titles[i] if custom_titles else None
        
        result = generate_text_content(current_title)
        if result[0] is not None:  # Check if title is not None
            successful_stories.append(result)
            print(f"✅ Story {i+1} completed: {result[0]}")
        else:
            print(f"❌ Story {i+1} failed")
    
    print(f"\n{'='*50}")
    print(f"📊 BULK STORY GENERATION COMPLETE")
    print(f"Successfully generated: {len(successful_stories)}/{num_runs} stories")
    print(f"{'='*50}")
    
    return successful_stories