"""
audio_generator.py
Updated to use configuration management for paths.
"""
import os
import shutil
from config_manager import get_config


def generate_audio_from_story(story: str, output_folder: str) -> None:
    """Generate audio narration for the story using f5-tts_infer-cli and save as gene_audio.wav."""
    # Get configured paths
    ref_audio = get_config("ref_audio_path")
    ref_text = get_config("ref_text_path")
    
    # If not configured, try default locations
    if not ref_audio:
        ref_audio = os.path.join(os.path.dirname(__file__), "ref_audio.mp3")
    if not ref_text:
        ref_text = os.path.join(os.path.dirname(__file__), "ref_txt.txt")
    
    # Check if reference files exist
    if not os.path.exists(ref_audio):
        print(f"✗ Reference audio file not found: {ref_audio}")
        print("Please configure the correct path in settings.")
        raise FileNotFoundError(f"Reference audio not found: {ref_audio}")
    
    if not os.path.exists(ref_text):
        print(f"✗ Reference text file not found: {ref_text}")
        print("Please configure the correct path in settings.")
        raise FileNotFoundError(f"Reference text not found: {ref_text}")
    
    original_cwd = os.getcwd()
    
    try:
        os.chdir(output_folder)
        command = (
            f"f5-tts_infer-cli --model F5TTS_v1_Base "
            f"--ref_audio '{ref_audio}' "
            f"--ref_text \"$(cat '{ref_text}')\" "
            f"--gen_text \"{story.replace('\\', ' ').replace('"', '')}\" "
        )
        os.system(command)
        
        # Recursively find any .wav file in output_folder or subfolders
        gene_audio_path = os.path.join(output_folder, 'gene_audio.wav')
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                if file.endswith('.wav'):
                    src = os.path.join(root, file)
                    if src != gene_audio_path:
                        shutil.move(src, gene_audio_path)
                    break
        
        # Remove tests folder if created
        tests_path = os.path.join(output_folder, "tests")
        if os.path.exists(tests_path) and os.path.isdir(tests_path):
            shutil.rmtree(tests_path)
        
        print("✅ Audio generated successfully")
        
    finally:
        os.chdir(original_cwd)