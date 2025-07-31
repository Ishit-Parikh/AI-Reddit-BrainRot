"""
transcription_integration.py
Enhanced transcription module with viral ASS captions integrated with the FRBV pipeline.
Uses random fonts, colors, and advanced styling for professional viral-style subtitles.
"""
import whisper
import os
import shutil
import json
import re
import subprocess
import traceback
import random
from utils import get_audio_duration

# Configuration
FONTS_DIR = "/home/lord/Desktop/tst/fonts"  # Update this path as needed

def choose_random_font(fonts_dir):
    """
    Randomly selects and returns the FONT NAME (not file path) from the given folder.
    ASS requires the font name, not the file path.
    """
    if not os.path.exists(fonts_dir):
        print(f"⚠️ Fonts directory not found: {fonts_dir}")
        return "Arial"  # fallback font
    
    fonts = [f for f in os.listdir(fonts_dir) if os.path.isfile(os.path.join(fonts_dir, f))]
    
    if not fonts:
        print("⚠️ No font files found in the folder.")
        return "Arial"  # fallback font
    
    chosen_file = random.choice(fonts)
    # Extract font name (without extension)
    font_name = os.path.splitext(chosen_file)[0]
    print(f"🎨 Random font selected: {font_name}")
    return font_name

def ends_with_punctuation(text):
    """Check if text ends with punctuation marks."""
    punctuation_marks = ['.', '!', '?', ';', ':']
    return any(text.rstrip().endswith(mark) for mark in punctuation_marks)

def write_punctuation_group(file_handle, group, color_style):
    """Write a group of words with the same color."""
    for item in group:
        start_time_ass = format_time_ass(item['start'])
        end_time_ass = format_time_ass(item['end'])
        text = item['text'].strip()
        file_handle.write(f"Dialogue: 0,{start_time_ass},{end_time_ass},{color_style},,0,0,0,,{text}\n")

def format_time_ass(seconds):
    """Convert seconds to ASS time format (H:MM:SS.CC)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds * 100) % 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

def transcribe_video_to_ass_and_srt(video_file_path: str, output_folder: str, model_size: str = "tiny") -> dict:
    """
    Transcribe video file and create both ASS (for styling) and SRT (for compatibility) subtitle files.

    Args:
        video_file_path (str): Path to the final video file to transcribe.
        output_folder (str): Directory where subtitle files will be saved.
        model_size (str): Whisper model size ("tiny", "base", "small", "medium", "large").

    Returns:
        dict: Paths to generated files and metadata.
    """
    try:
        print(f"🎤 Starting video transcription with Whisper ({model_size} model)...")

        # Choose random font for ASS styling
        chosen_font = choose_random_font(FONTS_DIR)
        
        # Available color styles
        color_styles = ["Yellow", "Red", "White", "Blue", "Orange", "Green"]
        current_color_index = 0

        # Load the Whisper model
        model = whisper.load_model(model_size)

        # Perform transcription with word-level timestamps
        result = model.transcribe(
            video_file_path,
            language="en",
            word_timestamps=True,
        )

        transcribed_text = result["text"]
        segments = result["segments"]

        # Create file paths
        ass_file = os.path.join(output_folder, "subtitles.ass")
        srt_file = os.path.join(output_folder, "subtitles.srt")

        # Generate ASS file with viral styling
        with open(ass_file, "w", encoding="utf-8") as f:
            # Write ASS header
            f.write("[Script Info]\n")
            f.write("Title: Viral Captions\n")
            f.write("ScriptType: v4.00+\n")
            f.write("WrapStyle: 0\n")
            f.write("ScaledBorderAndShadow: yes\n")
            f.write("YCbCr Matrix: TV.709\n\n")
            
            # Styles section
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            
            # Define styles with chosen random font
            styles = {
                "Yellow": "&H0000FFFF",
                "Red": "&H000000FF", 
                "White": "&H00FFFFFF",
                "Blue": "&H00FF0000",
                "Orange": "&H000080FF",
                "Green": "&H0000FF00"
            }
            for name, color in styles.items():
                f.write(f"Style: {name},{chosen_font},12,{color},&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,1,1,5,10,10,10,1\n")
            f.write("\n")
            
            # Events section
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            # Collect word groups
            punctuation_groups = []
            for segment in segments:
                if "words" in segment and segment["words"]:
                    words = segment["words"]
                    i = 0
                    while i < len(words):
                        current_word = words[i]["word"].strip()
                        start_time = words[i]["start"]
                        combined_text = current_word
                        end_time = words[i]["end"]
                        
                        # Combine short words with next word for better readability
                        if len(current_word) <= 3 and i + 1 < len(words):
                            combined_text += ' ' + words[i + 1]["word"].strip()
                            end_time = words[i + 1]["end"]
                            i += 2
                        else:
                            i += 1
                        
                        punctuation_groups.append({
                            'text': combined_text,
                            'start': start_time,
                            'end': end_time
                        })
                else:
                    # Fallback to segment-level timestamps
                    punctuation_groups.append({
                        'text': segment["text"].strip(),
                        'start': segment["start"],
                        'end': segment["end"]
                    })
            
            # Write groups with alternating colors
            current_group = []
            for item in punctuation_groups:
                current_group.append(item)
                if ends_with_punctuation(item['text']):
                    write_punctuation_group(f, current_group, color_styles[current_color_index])
                    current_color_index = (current_color_index + 1) % len(color_styles)
                    current_group = []
            if current_group:
                write_punctuation_group(f, current_group, color_styles[current_color_index])

        # Generate SRT file for compatibility
        with open(srt_file, "w", encoding="utf-8") as f:
            subtitle_index = 1
            for segment in segments:
                if "words" in segment and segment["words"]:
                    words = segment["words"]
                    i = 0
                    while i < len(words):
                        start_time = words[i]["start"]
                        end_time = words[i]["end"]
                        combined_text = words[i]["word"].strip()

                        # Combine short words for better readability
                        if len(combined_text) <= 3 and i + 1 < len(words):
                            next_word_info = words[i + 1]
                            combined_text += " " + next_word_info["word"].strip()
                            end_time = next_word_info["end"]
                            i += 2
                        else:
                            i += 1

                        # Write the subtitle entry
                        start_time_srt = _seconds_to_srt_time(start_time)
                        end_time_srt = _seconds_to_srt_time(end_time)
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{start_time_srt} --> {end_time_srt}\n")
                        f.write(f"{combined_text}\n\n")
                        subtitle_index += 1
                else:
                    # Fallback to segment-level timestamps
                    start_time = segment["start"]
                    end_time = segment["end"]
                    text = segment["text"].strip()
                    
                    if not text:
                        continue

                    start_time_srt = _seconds_to_srt_time(start_time)
                    end_time_srt = _seconds_to_srt_time(end_time)
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{start_time_srt} --> {end_time_srt}\n")
                    f.write(f"{text}\n\n")
                    subtitle_index += 1

        print(f"✅ Video transcription completed!")
        print(f"  🎨 ASS subtitles: {os.path.basename(ass_file)} (with {chosen_font} font)")
        print(f"  📺 SRT subtitles: {os.path.basename(srt_file)}")

        return {
            'ass_file': ass_file,
            'srt_file': srt_file,
            'font_used': chosen_font,
            'success': True
        }

    except Exception as e:
        print(f"❌ Video transcription failed: {e}")
        traceback.print_exc()
        return {'success': False}

def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,ms)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds * 1000) % 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def create_video_with_embedded_subtitles(video_path: str, subtitle_path: str, output_folder: str, use_ass: bool = True) -> str:
    """
    Create a new video with embedded subtitles using FFmpeg.
    Supports both ASS (with styling) and SRT (basic) subtitle formats.

    Args:
        video_path (str): Path to the input video file.
        subtitle_path (str): Path to the subtitle file (ASS or SRT).
        output_folder (str): Directory for the output video.
        use_ass (bool): Whether to use ASS styling (requires fonts directory).

    Returns:
        str: Path to the video with embedded subtitles, or None if failed.
    """
    try:
        output_path = os.path.join(output_folder, "final_output_with_subtitles.mp4")

        if use_ass and subtitle_path.endswith('.ass'):
            # FFmpeg command for ASS subtitles with font directory
            escaped_subtitle_path = subtitle_path.replace('\\', '/').replace(':', '\\:')
            escaped_fonts_dir = FONTS_DIR.replace('\\', '/').replace(':', '\\:')
            
            ffmpeg_command = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles='{escaped_subtitle_path}':fontsdir='{escaped_fonts_dir}'",
                '-c:a', 'copy',  # Copy audio without re-encoding
                '-y', output_path
            ]
            print("🎬 Adding styled ASS subtitles to video...")
        else:
            # FFmpeg command for SRT subtitles with basic styling
            escaped_subtitle_path = subtitle_path.replace('\\', '/').replace(':', '\\:')
            ffmpeg_command = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles='{escaped_subtitle_path}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,BorderStyle=3,Shadow=1'",
                '-c:a', 'copy',
                '-y', output_path
            ]
            print("🎬 Adding basic SRT subtitles to video...")

        result = subprocess.run(
            ffmpeg_command,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
            check=False
        )

        if result.returncode == 0:
            print(f"✅ Video with subtitles created: {output_path}")
            return output_path
        else:
            print(f"❌ Failed to embed subtitles. FFmpeg stderr:\n{result.stderr}")
            return None

    except Exception as e:
        print(f"❌ Error embedding subtitles: {e}")
        return None

def process_transcription_for_story(output_folder: str, create_subtitled_video: bool = False) -> dict:
    """
    Process transcription for a single story using the final video file directly.
    Creates both ASS (styled) and SRT (compatible) subtitle files.

    Args:
        output_folder (str): Path to the story's output folder.
        create_subtitled_video (bool): Whether to create a video with embedded subtitles.

    Returns:
        dict: Results of transcription processing.
    """
    results = {'ass_file': None, 'srt_file': None, 'subtitled_video': None, 'success': False}
    
    # Use final video file for transcription
    video_file = os.path.join(output_folder, "gene_video.mp4")
    
    if not os.path.exists(video_file):
        print(f"❌ Video file not found: {video_file}")
        return results

    # Transcribe video to get both ASS and SRT files
    transcription_result = transcribe_video_to_ass_and_srt(video_file, output_folder)
    if not transcription_result['success']:
        return results

    results.update(transcription_result)

    # Optionally create video with embedded subtitles (prioritize ASS over SRT)
    if create_subtitled_video:
        # Try ASS first (with styling), fallback to SRT
        subtitle_file = results['ass_file'] if results['ass_file'] else results['srt_file']
        use_ass = results['ass_file'] is not None
        
        subtitled_video = create_video_with_embedded_subtitles(
            video_file, subtitle_file, output_folder, use_ass
        )
        
        if subtitled_video and os.path.exists(subtitled_video):
            # Replace original video with subtitled version
            if os.path.exists(video_file):
                os.remove(video_file)
                print(f"🗑️ Removed original video: {os.path.basename(video_file)}")
            
            # Rename subtitled video to gene_video.mp4
            final_video_path = os.path.join(output_folder, "gene_video.mp4")
            os.rename(subtitled_video, final_video_path)
            print(f"✅ Final video renamed to: gene_video.mp4 (with embedded subtitles)")
            results['subtitled_video'] = final_video_path
    
    return results

def process_transcription_bulk(stories_data: list, create_subtitled_videos: bool = False) -> list:
    """
    Process transcription for multiple stories in bulk.

    Args:
        stories_data (list): List of tuples (title, story, output_folder).
        create_subtitled_videos (bool): Whether to create videos with embedded subtitles.

    Returns:
        list: List of tuples (title, story, output_folder, transcription_results).
    """
    print(f"\n{'='*50}")
    print("🎤 BULK TRANSCRIPTION PHASE")
    print(f"Processing transcription for {len(stories_data)} stories...")
    if create_subtitled_videos:
        print("🎨 Will create videos with viral-style ASS subtitles")
    print(f"{'='*50}")

    successful_transcriptions = []
    for i, (title, story, output_folder) in enumerate(stories_data, 1):
        print(f"\n🎙️ Processing transcription {i}/{len(stories_data)}: {title}")
        print("-" * 40)
        try:
            transcription_results = process_transcription_for_story(output_folder, create_subtitled_videos)
            if transcription_results['success']:
                successful_transcriptions.append((title, story, output_folder, transcription_results))
                print(f"✅ Transcription {i} completed: {title}")
                print(f"  🎨 ASS subtitles: subtitles.ass ({transcription_results.get('font_used', 'default')} font)")
                print(f"  📺 SRT subtitles: subtitles.srt")
                if transcription_results['subtitled_video']:
                    print(f"  🎬 Final video: gene_video.mp4 (with embedded viral subtitles)")
                else:
                    print(f"  🎬 Final video: gene_video.mp4")
            else:
                print(f"❌ Transcription {i} failed: {title}")
        except Exception as e:
            print(f"❌ Unhandled error in transcription for '{title}': {e}")
            traceback.print_exc()

    print(f"\n{'='*50}")
    print("📊 BULK TRANSCRIPTION COMPLETE")
    print(f"Successfully processed: {len(successful_transcriptions)}/{len(stories_data)} transcriptions")
    print(f"{'='*50}")
    return successful_transcriptions

# --- Integration Functions ---

def add_transcription_to_single_story_pipeline(output_folder: str, create_subtitled_video: bool = True):
    """
    Add transcription step to the single story pipeline with viral-style ASS subtitles.
    """
    print("\n🎤 Adding viral transcription to pipeline...")
    transcription_results = process_transcription_for_story(output_folder, create_subtitled_video)
    
    if transcription_results['success']:
        print("✅ Viral transcription step completed successfully!")
        print("🎨 Created ASS subtitles with random font and alternating colors")
        print("📺 Created SRT subtitles for compatibility")
    else:
        print("❌ Transcription step failed!")
    
    return transcription_results

def add_transcription_to_bulk_pipeline(stories_data: list, create_subtitled_videos: bool = True):
    """
    Add transcription step to the bulk pipeline with viral-style ASS subtitles.
    """
    return process_transcription_bulk(stories_data, create_subtitled_videos)