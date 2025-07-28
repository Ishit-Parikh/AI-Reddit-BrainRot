"""
transcription_integration.py
Enhanced transcription module integrated with the FRBV pipeline.
Fixed to create only one SRT file using final_output.mp4 timing.
"""
import whisper
import os
import shutil
import json
import re
import subprocess
import traceback
from utils import get_audio_duration

def transcribe_video_to_srt(video_file_path: str, output_folder: str, model_size: str = "tiny") -> str:
    """
    Transcribe video file directly and create SRT subtitle file with correct timing.
    This eliminates the need for separate timing adjustment.

    Args:
        video_file_path (str): Path to the final video file to transcribe.
        output_folder (str): Directory where the SRT file will be saved.
        model_size (str): Whisper model size ("tiny", "base", "small", "medium", "large").

    Returns:
        str: Path to the generated SRT file, or None if failed.
    """
    try:
        print(f"🎤 Starting video transcription with Whisper ({model_size} model)...")

        # Load the Whisper model
        model = whisper.load_model(model_size)

        # Perform transcription with word-level timestamps directly on the video
        result = model.transcribe(
            video_file_path,
            language="en",
            word_timestamps=True,
        )

        transcribed_text = result["text"]
        segments = result["segments"]

        # Create single SRT file path
        srt_file = os.path.join(output_folder, "subtitles.srt")

        # Generate SRT content with word-level timestamps
        with open(srt_file, "w", encoding="utf-8") as f:
            subtitle_index = 1
            for segment in segments:
                # Check if the segment has word-level timestamps
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
                            i += 2  # Move past both words
                        else:
                            i += 1 # Move to the next word

                        # Write the subtitle entry
                        start_time_srt = _seconds_to_srt_time(start_time)
                        end_time_srt = _seconds_to_srt_time(end_time)
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{start_time_srt} --> {end_time_srt}\n")
                        f.write(f"{combined_text}\n\n")
                        subtitle_index += 1
                else:
                    # Fallback to segment-level timestamps if no words are found
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

        print(f"✅ Video transcription completed: {srt_file}")

        return srt_file

    except Exception as e:
        print(f"❌ Video transcription failed: {e}")
        traceback.print_exc()
        return None

def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,ms)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds * 1000) % 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def create_video_with_embedded_subtitles(video_path: str, srt_path: str, output_folder: str) -> str:
    """
    Create a new video with embedded subtitles using FFmpeg.

    Args:
        video_path (str): Path to the input video file.
        srt_path (str): Path to the SRT subtitle file.
        output_folder (str): Directory for the output video.

    Returns:
        str: Path to the video with embedded subtitles, or None if failed.
    """
    try:
        output_path = os.path.join(output_folder, "final_output_with_subtitles.mp4")

        # FFmpeg command to embed subtitles (hardcode style)
        # Using a platform-independent path format for the filter
        escaped_srt_path = srt_path.replace('\\', '/').replace(':', '\\:')
        ffmpeg_command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f"subtitles='{escaped_srt_path}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,BorderStyle=3,Shadow=1'",
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-y', output_path
        ]

        print("🎬 Adding subtitles to video...")
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
    This creates only one SRT file with correct timing.

    Args:
        output_folder (str): Path to the story's output folder.
        create_subtitled_video (bool): Whether to create a video with embedded subtitles.

    Returns:
        dict: Results of transcription processing.
    """
    results = {'srt_file': None, 'subtitled_video': None, 'success': False}
    
    # Use final video file for transcription instead of audio
    video_file = os.path.join(output_folder, "gene_video.mp4")
    
    if not os.path.exists(video_file):
        print(f"❌ Video file not found: {video_file}")
        return results

    # Transcribe video directly to get SRT file with correct timing
    srt_file = transcribe_video_to_srt(video_file, output_folder)
    if not srt_file:
        return results

    results['srt_file'] = srt_file
    results['success'] = True

    # Optionally create video with embedded subtitles
    if create_subtitled_video:
        results['subtitled_video'] = create_video_with_embedded_subtitles(video_file, srt_file, output_folder)
        
        # If subtitled video was created successfully, replace final_output.mp4 with it
        if results['subtitled_video'] and os.path.exists(results['subtitled_video']):
            final_video_path = os.path.join(output_folder, "gene_video.mp4")
            
            # Remove original final_output.mp4
            if os.path.exists(video_file):
                os.remove(video_file)
                print(f"🗑️ Removed original video: {os.path.basename(video_file)}")
            
            # Rename subtitled video to gene_video.mp4
            os.rename(results['subtitled_video'], final_video_path)
            print(f"✅ Final video renamed to: gene_video.mp4")
            results['subtitled_video'] = final_video_path
    else:
        # If no subtitled video requested, just rename final_output.mp4 to gene_video.mp4
        final_video_path = os.path.join(output_folder, "gene_video.mp4")
        if os.path.exists(video_file):
            os.rename(video_file, final_video_path)
            print(f"✅ Final video renamed to: gene_video.mp4")
    
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
    print(f"\n{'='*50}\n🎤 BULK TRANSCRIPTION PHASE")
    print(f"Processing transcription for {len(stories_data)} stories...")
    if create_subtitled_videos:
        print("📺 Will also create videos with embedded subtitles")
    print(f"{'='*50}")

    successful_transcriptions = []
    for i, (title, story, output_folder) in enumerate(stories_data, 1):
        print(f"\n🎙️ Processing transcription {i}/{len(stories_data)}: {title}\n" + "-" * 40)
        try:
            transcription_results = process_transcription_for_story(output_folder, create_subtitled_videos)
            if transcription_results['success']:
                successful_transcriptions.append((title, story, output_folder, transcription_results))
                print(f"✅ Transcription {i} completed: {title}")
                print(f"  📝 SRT file: {os.path.basename(transcription_results['srt_file'])}")
                if transcription_results['subtitled_video']:
                    print(f"  🎬 Final video: gene_video.mp4 (with embedded subtitles)")
                else:
                    print(f"  🎬 Final video: gene_video.mp4")
            else:
                print(f"❌ Transcription {i} failed: {title}")
        except Exception as e:
            print(f"❌ Unhandled error in transcription for '{title}': {e}")
            traceback.print_exc()

    print(f"\n{'='*50}\n📊 BULK TRANSCRIPTION COMPLETE")
    print(f"Successfully processed: {len(successful_transcriptions)}/{len(stories_data)} transcriptions")
    print(f"{'='*50}")
    return successful_transcriptions

# --- Integration Functions ---

def add_transcription_to_single_story_pipeline(output_folder: str, create_subtitled_video: bool = True):
    """
    Add transcription step to the single story pipeline. This is a wrapper function.
    Now creates only one SRT file using the final video.
    """
    print("\n🎤 Adding transcription to pipeline...")
    transcription_results = process_transcription_for_story(output_folder, create_subtitled_video)
    
    if transcription_results['success']:
        print("✅ Transcription step completed successfully!")
        print("📝 Created single SRT file with correct video timing")
    else:
        print("❌ Transcription step failed!")
    
    return transcription_results

def add_transcription_to_bulk_pipeline(stories_data: list, create_subtitled_videos: bool = True):
    """
    Add transcription step to the bulk pipeline. This is a wrapper function.
    """
    return process_transcription_bulk(stories_data, create_subtitled_videos)