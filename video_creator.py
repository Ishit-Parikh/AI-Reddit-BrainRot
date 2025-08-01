"""
video_creator.py
Updated to use configuration management and improved folder handling.
"""
import os
import json
import random
import subprocess
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip

from config_manager import get_config
from utils import get_audio_duration
from video_utils import get_all_video_files, pick_non_repeating_videos, analyze_video_structure


def save_speed_info(output_folder: str, original_duration: float, final_duration: float, speed_factor: float):
    """Save speed information for transcription synchronization."""
    speed_info = {
        'original_audio_duration': original_duration,
        'final_video_duration': final_duration,
        'speed_factor': speed_factor
    }
    
    speed_info_file = os.path.join(output_folder, "speed_info.json")
    with open(speed_info_file, 'w') as f:
        json.dump(speed_info, f, indent=2)
    
    print(f"💾 Speed info saved: {speed_factor:.2f}x")


def get_speedup_factor(duration_seconds: float) -> float:
    """
    Calculate speedup factor based on video duration:
    - If video <= 90 seconds: no speedup (1x)
    - If video is 91-179 seconds: gradual speedup from 1x to 2x
    - If video >= 180 seconds: speedup to random duration between 150-166 seconds
    """
    if duration_seconds <= 90:
        return 1.0
    elif duration_seconds < 180:
        # Linear interpolation between 1x and 2x for 91-179 seconds
        return 1.0 + (duration_seconds - 90) / (179 - 90)
    else:
        # For videos >= 180 seconds, pick random target duration
        target_duration = random.uniform(150, 166)
        speed_factor = duration_seconds / target_duration
        
        print(f"Video duration: {duration_seconds:.2f}s")
        print(f"Target duration: {target_duration:.2f}s")
        print(f"Required speed factor: {speed_factor:.2f}x")
        
        return speed_factor


def create_video_with_audio(output_folder: str):
    """Create a video with random background footage matching the audio duration."""
    # Get configured videos path
    videos_root = get_config("videos_path")
    if not videos_root:
        videos_root = os.path.join(os.path.dirname(__file__), "Videos")
        print(f"Using default videos path: {videos_root}")
    
    audio_path = os.path.join(output_folder, "gene_audio.wav")
    
    # Check if audio file exists
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        print("Make sure the audio generation step completed successfully.")
        return
    
    try:
        audio_duration = get_audio_duration(audio_path)
        print(f"Creating video to match audio duration: {audio_duration:.2f}s")
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return
    
    # Get all videos with flexible folder handling
    folder_to_videos = get_all_video_files(videos_root)
    if not folder_to_videos:
        print(f"Error: No video files found in {videos_root}")
        print("\nPlease ensure you have video files in one of these formats:")
        print("  .mp4, .mov, .avi, .mkv, .webm")
        print("\nYou can organize videos in two ways:")
        print("1. Place all videos directly in the videos folder")
        print("2. Organize videos in subfolders (e.g., Videos/Nature/, Videos/City/)")
        return
    
    # Analyze video structure (helpful for users)
    analyze_video_structure(videos_root)
    
    # Decide how many clips to use
    count = int(audio_duration // 5) + 1  # e.g. 1 clip per 5 seconds
    
    # Get total available videos
    total_videos = sum(len(videos) for videos in folder_to_videos.values())
    count = min(count, total_videos)  # Don't request more than available
    
    try:
        selected_videos = pick_non_repeating_videos(folder_to_videos, count)
    except ValueError as e:
        print(e)
        return
    
    # Load video clips and trim if needed
    video_clips = []
    total_duration = 0
    for video_path in selected_videos:
        try:
            clip = VideoFileClip(video_path)
            video_clips.append(clip)
            total_duration += clip.duration
            if total_duration >= audio_duration:
                break
        except Exception as e:
            print(f"Error loading video {video_path}: {e}")
            continue
    
    if not video_clips:
        print("Error: No video clips could be loaded")
        return
    
    try:
        # Concatenate and trim to audio duration
        final_clip = concatenate_videoclips(video_clips).subclip(0, audio_duration)
        
        # Load the original audio with MoviePy
        audio_clip = AudioFileClip(audio_path)
        
        # Combine video and audio
        final_clip = final_clip.set_audio(audio_clip)
        
        # Save the normal speed video first at 60 fps
        normal_output = os.path.join(output_folder, "normal_speed.mp4")
        final_clip.write_videofile(normal_output, codec="libx264", audio_codec="aac", 
                                   fps=60, verbose=False, logger=None)
        
        # Apply duration-based speed and save speed info
        _apply_duration_based_speed(normal_output, output_folder, audio_duration)
        
        # Close all clips
        for clip in video_clips:
            clip.close()
        audio_clip.close()
        final_clip.close()
        
    except Exception as e:
        print(f"Error during video creation: {e}")
        # Clean up any clips that were opened
        for clip in video_clips:
            try:
                clip.close()
            except:
                pass


def _apply_duration_based_speed(normal_output: str, output_folder: str, duration_seconds: float):
    """Apply duration-based speed to the video with hardware acceleration if available."""
    # Calculate speed factor based on duration
    speed_factor = get_speedup_factor(duration_seconds)
    
    print(f"Video duration: {duration_seconds:.2f}s")
    print(f"Applying {speed_factor:.2f}x speed based on duration rules...")
    
    # If no speedup needed, just rename the file
    if speed_factor == 1.0:
        sped_up_output = os.path.join(output_folder, "gene_video.mp4")
        os.rename(normal_output, sped_up_output)
        print(f"✓ No speedup applied (≤90s video): {sped_up_output}")
        save_speed_info(output_folder, duration_seconds, duration_seconds, 1.0)
        return
    
    # Try hardware acceleration first, then CPU fallback
    sped_up_output = os.path.join(output_folder, "gene_video.mp4")
    
    # Try VAAPI first (AMD GPU)
    if _try_vaapi_encoding(normal_output, sped_up_output, speed_factor, duration_seconds):
        return
    
    # Try NVIDIA NVENC
    if _try_nvenc_encoding(normal_output, sped_up_output, speed_factor, duration_seconds):
        return
    
    # Fallback to CPU encoding
    if _try_cpu_encoding(normal_output, sped_up_output, speed_factor, duration_seconds):
        return
    
    # If all methods fail, keep normal speed
    print("⚠️ All encoding methods failed. Keeping normal speed video.")
    if os.path.exists(normal_output):
        os.rename(normal_output, sped_up_output)
        save_speed_info(output_folder, duration_seconds, duration_seconds, 1.0)


def _try_vaapi_encoding(input_path: str, output_path: str, speed_factor: float, original_duration: float) -> bool:
    """Try VAAPI hardware encoding (AMD GPUs)."""
    setpts_value = round(1.0 / speed_factor, 3)
    atempo_value = speed_factor
    
    # Try both common VAAPI devices
    for device in ['/dev/dri/renderD128', '/dev/dri/renderD129']:
        print(f"Trying VAAPI device: {device}")
        
        ffmpeg_command = [
            'ffmpeg', 
            '-vaapi_device', device,
            '-i', input_path,
            '-vf', f'format=nv12,hwupload,setpts={setpts_value}*PTS',
            '-filter:a', f'atempo={atempo_value}',
            '-r', '60',
            '-c:v', 'h264_vaapi',
            '-qp', '23',
            '-threads', '12',
            '-y', output_path
        ]
        
        try:
            result = subprocess.run(
                ffmpeg_command,
                capture_output=True,
                text=True,
                timeout=120,
                check=False
            )
            
            if result.returncode == 0:
                print(f"✓ VAAPI encoding successful with {device}")
                save_speed_info(os.path.dirname(output_path), original_duration, 
                              original_duration / speed_factor, speed_factor)
                if os.path.exists(input_path):
                    os.remove(input_path)
                return True
                
        except subprocess.TimeoutExpired:
            print(f"✗ VAAPI encoding timed out on {device}")
        except Exception as e:
            print(f"✗ VAAPI error on {device}: {e}")
    
    return False


def _try_nvenc_encoding(input_path: str, output_path: str, speed_factor: float, original_duration: float) -> bool:
    """Try NVIDIA NVENC hardware encoding."""
    print("Trying NVIDIA NVENC encoding...")
    
    setpts_value = round(1.0 / speed_factor, 3)
    atempo_value = speed_factor
    
    ffmpeg_command = [
        'ffmpeg',
        '-i', input_path,
        '-filter:v', f'setpts={setpts_value}*PTS',
        '-filter:a', f'atempo={atempo_value}',
        '-r', '60',
        '-c:v', 'h264_nvenc',
        '-preset', 'fast',
        '-cq', '23',
        '-y', output_path
    ]
    
    try:
        result = subprocess.run(
            ffmpeg_command,
            capture_output=True,
            text=True,
            timeout=120,
            check=False
        )
        
        if result.returncode == 0:
            print("✓ NVENC encoding successful")
            save_speed_info(os.path.dirname(output_path), original_duration, 
                          original_duration / speed_factor, speed_factor)
            if os.path.exists(input_path):
                os.remove(input_path)
            return True
        else:
            print("✗ NVENC encoding failed")
            
    except Exception as e:
        print(f"✗ NVENC error: {e}")
    
    return False


def _try_cpu_encoding(input_path: str, output_path: str, speed_factor: float, original_duration: float) -> bool:
    """CPU-based encoding fallback."""
    print("Using CPU encoding...")
    
    setpts_value = round(1.0 / speed_factor, 3)
    atempo_value = speed_factor
    
    ffmpeg_command = [
        'ffmpeg',
        '-i', input_path,
        '-filter:v', f'setpts={setpts_value}*PTS',
        '-filter:a', f'atempo={atempo_value}',
        '-r', '60',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-threads', '0',  # Use all available threads
        '-y', output_path
    ]
    
    try:
        result = subprocess.run(
            ffmpeg_command,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes for CPU encoding
            check=False
        )
        
        if result.returncode == 0:
            print("✓ CPU encoding successful")
            save_speed_info(os.path.dirname(output_path), original_duration, 
                          original_duration / speed_factor, speed_factor)
            if os.path.exists(input_path):
                os.remove(input_path)
            return True
        else:
            print("✗ CPU encoding failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
                
    except subprocess.TimeoutExpired:
        print("✗ CPU encoding timed out")
    except Exception as e:
        print(f"✗ CPU encoding error: {e}")
    
    return False