"""
text_generator.py
Updated to use configuration management system instead of hardcoded values.
"""

import os
import time
import lmstudio as lms
from openai import OpenAI

from config_manager import get_config
from utils import (
    read_file, 
    create_output_folder, 
    write_text_file
)

def initialize_api_clients():
    """Initialize API clients using configuration."""
    clients = {}
    
    # Initialize OpenAI client if configured
    openai_key = get_config("OPENAI_API_KEY")
    if openai_key:
        clients['openai'] = OpenAI(api_key=openai_key)
    
    # Initialize DeepSeek client if configured
    deepseek_key = get_config("DEEPSEEK_API_KEY")
    if deepseek_key:
        clients['deepseek'] = OpenAI(
            api_key=deepseek_key,
            base_url="https://api.deepseek.com"
        )
    
    return clients


def validate_api_keys():
    """Validate that at least one API key is configured."""
    openai_key = get_config("OPENAI_API_KEY")
    deepseek_key = get_config("DEEPSEEK_API_KEY")
    
    if not openai_key and not deepseek_key:
        print("✗ No API keys configured. Please run configuration setup.")
        return False
    return True


def generate_with_openai(system_prompt: str, user_prompt: str, content_type: str = "content") -> str:
    """Generate content using official OpenAI API."""
    try:
        print(f"✓ Attempting {content_type} generation with Official OpenAI API...")
        
        clients = initialize_api_clients()
        if 'openai' not in clients:
            print("✗ OpenAI client not configured")
            return None
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        model_id = get_config("openai_model_id", "gpt-4o-mini")
        completion = clients['openai'].chat.completions.create(
            model=model_id,
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
    """Generate content using DeepSeek API."""
    try:
        print(f"✓ Attempting {content_type} generation with DeepSeek...")
        
        clients = initialize_api_clients()
        if 'deepseek' not in clients:
            print("✗ DeepSeek client not configured")
            return None
        
        model_name = get_config("deepseek_model_name", "deepseek-chat")
        
        response = clients['deepseek'].chat.completions.create(
            model=model_name,
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
    """Generate content using LMStudio as final fallback."""
    try:
        model_name = get_config("lmstudio_model_name")
        if not model_name:
            print("✗ LMStudio not configured")
            return None
            
        print(f"✓ Attempting {content_type} generation with LMStudio (final fallback)...")
        
        # Give the server some time if it was just started
        time.sleep(2)
        
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
    """Generate content with automatic fallback between configured APIs."""
    # Try APIs in order of configuration
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
    print(f"✗ All methods failed for {content_type} generation!")
    return None


def generate_text_content(custom_title=None):
    """Generate title and story content using configured APIs."""
    try:
        # Validate API keys first
        if not validate_api_keys():
            print("✗ Cannot proceed without valid API keys")
            return None, None, None
        
        # Get configured paths
        title_prompt_path = get_config("title_prompt_path", "System_Title_Prompt.txt")
        story_prompt_path = get_config("story_prompt_path", "Story_System_Prompt.txt")
        
        # Check if prompt files exist
        if not os.path.exists(title_prompt_path):
            print(f"✗ Title prompt file not found: {title_prompt_path}")
            return None, None, None
            
        if not os.path.exists(story_prompt_path):
            print(f"✗ Story prompt file not found: {story_prompt_path}")
            return None, None, None
        
        print("✓ Reading system prompts...")
        system_prompt_title = read_file(title_prompt_path)
        system_prompt_story = read_file(story_prompt_path)

        # Handle title generation or use custom title
        if custom_title:
            print(f"✓ Using custom title: {custom_title}")
            response_title = custom_title
        else:
            title_prompt = "Generate a creative title for a story"
            response_title = generate_content_with_provider(
                system_prompt_title, 
                title_prompt, 
                "title",
                _active_provider
            )
            
            if response_title is None:
                print("✗ Failed to generate title with all methods")
                return None, None, None
        
        # Create output folder for this run
        output_base = get_config("output_path", os.path.expanduser("~/DaVinci Vids"))
        
        # Ensure output base directory exists
        os.makedirs(output_base, exist_ok=True)
        
        output_folder = create_output_folder(output_base, response_title)
        write_text_file(output_folder, "title.txt", response_title)
        print("✓ Title saved successfully")

        # Generate story using the title
        story_user_content = response_title 
        response_story = generate_content_with_provider(
            system_prompt_story, 
            story_user_content, 
            "story",
            _active_provider
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


def generate_all_stories_bulk(num_runs: int, custom_titles: list = None, ai_provider: str = None, use_batch: bool = False):
    """
    Generate all stories in bulk before processing audio/video.
    
    Args:
        num_runs: Number of stories to generate
        custom_titles: Optional list of custom titles
        ai_provider: Which AI to use ('openai', 'deepseek', 'lmstudio')
        use_batch: Whether to use batch API (OpenAI only)
    """
    # If using OpenAI batch mode, delegate to batch processor
    if ai_provider == 'openai' and use_batch:
        from batch_text_generator import generate_all_stories_batch
        return generate_all_stories_batch(num_runs, custom_titles)
    
    # Regular sequential processing
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{'='*50}")
    print(f"🚀 BULK STORY GENERATION PHASE")
    print(f"Using {ai_provider.upper() if ai_provider else 'configured'} API")
    print(f"Generating {num_runs} stories...")
    print(f"{'='*50}")
    
    successful_stories = []
    
    # Set the active provider for this session
    global _active_provider
    _active_provider = ai_provider
    
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

# Global variable to track active provider
_active_provider = None

def generate_content_with_provider(system_prompt: str, user_prompt: str, content_type: str = "content", provider: str = None) -> str:
    """Generate content with specific provider or fallback chain."""
    if provider == 'openai' or (not provider and _active_provider == 'openai'):
        return generate_with_openai(system_prompt, user_prompt, content_type)
    elif provider == 'deepseek' or (not provider and _active_provider == 'deepseek'):
        return generate_with_deepseek(system_prompt, user_prompt, content_type)
    elif provider == 'lmstudio' or (not provider and _active_provider == 'lmstudio'):
        return generate_with_lmstudio(system_prompt, user_prompt, content_type)
    else:
        # Use fallback chain
        return generate_content_with_fallback(system_prompt, user_prompt, content_type)