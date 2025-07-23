"""
audio_generator.py
Handles audio generation using f5-tts_infer-cli.
"""
import os
import shutil


def generate_audio_from_story(story: str, output_folder: str) -> None:
    """Generate audio narration for the story using f5-tts_infer-cli and save as gene_audio.wav."""
    ref_audio = os.path.join(os.path.dirname(__file__), "ref_audio.mp3")
    ref_text = os.path.join(os.path.dirname(__file__), "ref_txt.txt")
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
        
        print("Audio generated at normal speed")
        
    finally:
        os.chdir(original_cwd)