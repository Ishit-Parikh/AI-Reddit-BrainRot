"""
utils.py
Common utility functions used across the Brain Rot pipeline.
"""
import os
import re
import random
import subprocess

def read_file(filepath: str) -> str:
    """Read and return the contents of a file."""
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()


def create_output_folder(base_path: str, folder_name: str) -> str:
    """Create a new folder for each run, named after the title, and return its path."""
    # Sanitize folder name to remove invalid characters
    safe_folder_name = re.sub(r'[^\w\-_ ]', '', folder_name).strip().replace(' ', '_')
    folder_path = os.path.join(base_path, safe_folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def write_text_file(folder: str, filename: str, content: str) -> None:
    """Write content to a text file inside the specified folder."""
    file_path = os.path.join(folder, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def silent_system(command: str) -> tuple:
    """Run a shell command and return (return_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def get_audio_duration(audio_path: str) -> float:
    """Return the duration of the audio file in seconds using ffprobe or MoviePy as fallback."""
    # Check if audio file exists
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    try:
        # Try ffprobe first
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", audio_path
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        
        duration_str = result.stdout.strip()
        if duration_str and result.returncode == 0:
            return float(duration_str)
        else:
            print(f"ffprobe failed or returned empty result. Error: {result.stderr}")
            raise ValueError("ffprobe failed")
            
    except (subprocess.SubprocessError, ValueError, FileNotFoundError) as e:
        print(f"ffprobe method failed: {e}")
        print("Falling back to MoviePy for duration detection...")
        
        # Fallback to MoviePy
        try:
            from moviepy.editor import AudioFileClip
            with AudioFileClip(audio_path) as audio_clip:
                duration = audio_clip.duration
            return duration
        except Exception as moviepy_error:
            print(f"MoviePy fallback also failed: {moviepy_error}")
            raise RuntimeError(f"Could not determine duration for {audio_path}")