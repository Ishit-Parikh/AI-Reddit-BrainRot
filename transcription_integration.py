"""
transcription_integration.py
Enhanced transcription module integrated with the FRBV pipeline.
This version has been corrected for syntax errors, indentation issues,
and a corrupted function definition.
"""
import whisper
import os
import shutil
import json
import re
import subprocess
import traceback
from utils import get_audio_duration

def transcribe_audio_to_srt(audio_file_path: str, output_folder: str, model_size: str = "tiny") -> str:
    """
    Transcribe audio file and create SRT subtitle file with word-level timestamps.

    Args:
        audio_file_path (str): Path to the audio file to transcribe.
        output_folder (str): Directory where the SRT file will be saved.
        model_size (str): Whisper model size ("tiny", "base", "small", "medium", "large").

    Returns:
        str: Path to the generated SRT file, or None if failed.
    """
    try:
        print(f"🎤 Starting transcription with Whisper ({model_size} model)...")

        # Load the Whisper model
        model = whisper.load_model(model_size)

        # Perform transcription with word-level timestamps
        result = model.transcribe(
            audio_file_path,
            language="en",
            word_timestamps=True,
        )

        transcribed_text = result["text"]
        segments = result["segments"]

        # Create SRT file path
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

        print(f"✅ Transcription completed: {srt_file}")

        # Save the full transcription as a text file
        transcript_file = os.path.join(output_folder, "transcript.txt")
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(transcribed_text)
        print(f"✅ Full transcript saved: {transcript_file}")

        return srt_file

    except Exception as e:
        print(f"❌ Transcription failed: {e}")
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

def adjust_srt_timing_for_video_speed(audio_file: str, video_file: str, srt_file: str, output_folder: str) -> str:
    """
    Adjust SRT timing to match the sped-up video using saved speed information.

    Args:
        audio_file (str): Path to original audio file.
        video_file (str): Path to final video file.
        srt_file (str): Path to original SRT file.
        output_folder (str): Output directory.

    Returns:
        str: Path to speed-adjusted SRT file, or original srt_file if no adjustment is needed/possible.
    """
    try:
        speed_info_file = os.path.join(output_folder, "speed_info.json")
        speed_factor = 1.0

        if os.path.exists(speed_info_file):
            with open(speed_info_file, 'r') as f:
                speed_info = json.load(f)
            speed_factor = speed_info.get('speed_factor', 1.0)
            print(f"📊 Using saved speed info: {speed_factor:.2f}x")
        else:
            print("⚠️ speed_info.json not found. Calculating speed factor from file durations...")
            original_audio_duration = get_audio_duration(audio_file)
            
            # Get final video duration using ffprobe
            probe_result = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration", 
                "-of", "default=noprint_wrappers=1:nokey=1", video_file
            ], capture_output=True, text=True)
            
            if probe_result.returncode == 0 and probe_result.stdout.strip():
                video_duration = float(probe_result.stdout.strip())
                if video_duration > 0:
                    speed_factor = original_audio_duration / video_duration
                print(f"  Original audio: {original_audio_duration:.2f}s, Final video: {video_duration:.2f}s")
                print(f"  Calculated speed factor: {speed_factor:.2f}x")
            else:
                print("⚠️ Could not get video duration. Using original SRT timing.")
                return srt_file

        # If no significant speed change, return original
        if abs(speed_factor - 1.0) < 0.01:
            print("No timing adjustment needed.")
            return srt_file

        with open(srt_file, 'r', encoding='utf-8') as f:
            srt_content = f.read()

        def adjust_timestamp(match):
            h, m, s, ms = map(int, match.groups())
            total_seconds = h * 3600 + m * 60 + s + ms / 1000
            adjusted_seconds = total_seconds / speed_factor
            return _seconds_to_srt_time(adjusted_seconds)

        timestamp_pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})')
        adjusted_content = timestamp_pattern.sub(adjust_timestamp, srt_content)
        
        adjusted_srt_file = os.path.join(output_folder, "subtitles_synced.srt")
        with open(adjusted_srt_file, 'w', encoding='utf-8') as f:
            f.write(adjusted_content)

        print(f"✅ Speed-adjusted SRT created: {os.path.basename(adjusted_srt_file)}")
        return adjusted_srt_file

    except Exception as e:
        print(f"⚠️ Failed to adjust SRT timing: {e}. Using original SRT timing.")
        traceback.print_exc()
        return srt_file

def process_transcription_for_story(output_folder: str, create_subtitled_video: bool = False) -> dict:
    """
    Process transcription for a single story's audio and optionally create subtitled video.

    Args:
        output_folder (str): Path to the story's output folder.
        create_subtitled_video (bool): Whether to create a video with embedded subtitles.

    Returns:
        dict: Results of transcription processing.
    """
    results = {'srt_file': None, 'transcript_file': None, 'subtitled_video': None, 'success': False}
    audio_file = os.path.join(output_folder, "gene_audio.wav")
    
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        return results

    # Transcribe audio to get the initial SRT file
    original_srt_file = transcribe_audio_to_srt(audio_file, output_folder)
    if not original_srt_file:
        return results

    # Adjust SRT timing if a final video exists
    video_file = os.path.join(output_folder, "final_output.mp4")
    final_srt_file = original_srt_file
    if os.path.exists(video_file):
        final_srt_file = adjust_srt_timing_for_video_speed(audio_file, video_file, original_srt_file, output_folder)
    
    results['srt_file'] = final_srt_file
    results['transcript_file'] = os.path.join(output_folder, "transcript.txt")
    results['success'] = True

    # Optionally create video with embedded subtitles
    if create_subtitled_video:
        if os.path.exists(video_file):
            results['subtitled_video'] = create_video_with_embedded_subtitles(video_file, results['srt_file'], output_folder)
        else:
            print(f"⚠️ Video file not found for subtitle embedding: {video_file}")
    
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
                print(f"  📄 Transcript: {os.path.basename(transcription_results['transcript_file'])}")
                if transcription_results['subtitled_video']:
                    print(f"  🎬 Subtitled video: {os.path.basename(transcription_results['subtitled_video'])}")
            else:
                print(f"❌ Transcription {i} failed: {title}")
        except Exception as e:
            print(f"❌ Unhandled error in transcription for '{title}': {e}")
            traceback.print_exc()

    print(f"\n{'='*50}\n📊 BULK TRANSCRIPTION COMPLETE")
    print(f"Successfully processed: {len(successful_transcriptions)}/{len(stories_data)} transcriptions")
    print(f"{'='*50}")
    return successful_transcriptions

# --- Corrected Integration Functions ---

def add_transcription_to_single_story_pipeline(output_folder: str, create_subtitled_video: bool = True):
    """
    Add transcription step to the single story pipeline. This is a wrapper function.
    This function was previously corrupted and has been fixed.
    """
    print("\n🎤 Adding transcription to pipeline...")
    transcription_results = process_transcription_for_story(output_folder, create_subtitled_video)
    
    if transcription_results['success']:
        print("✅ Transcription step completed successfully!")
    else:
        print("❌ Transcription step failed!")
    
    return transcription_results

def add_transcription_to_bulk_pipeline(stories_data: list, create_subtitled_videos: bool = True):
    """
    Add transcription step to the bulk pipeline. This is a wrapper function.
    """
    return process_transcription_bulk(stories_data, create_subtitled_videos)
