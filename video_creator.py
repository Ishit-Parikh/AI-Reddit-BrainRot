"""
video_creator.py
Handles video creation, editing, and speed modification.
"""
import os
import random
import subprocess
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip

from utils import get_audio_duration
from video_utils import get_all_video_files, pick_non_repeating_videos


def get_speedup_factor(duration_seconds: float) -> float:
    """
    Calculate speedup factor based on video duration:
    - If video <= 90 seconds: no speedup (1x)
    - If video is 91-179 seconds: gradual speedup from 1x to 2x
    - If video >= 180 seconds: speedup to random duration between 150-166 seconds
    
    Args:
        duration_seconds (float): Original video duration in seconds
        
    Returns:
        float: Speed factor to apply to the video
    """
    
    if duration_seconds <= 90:
        return 1.0
    elif duration_seconds < 180:
        # Linear interpolation between 1x and 2x for 91-179 seconds
        # At 91 seconds: 1x, At 179 seconds: 2x
        return 1.0 + (duration_seconds - 90) / (179 - 90)
    else:
        # For videos >= 180 seconds, pick random target duration between 150-166 seconds
        target_duration = random.uniform(150, 166)
        speed_factor = duration_seconds / target_duration
        
        print(f"Video duration: {duration_seconds:2F}s")
        print(f"Target duration: {target_duration:2F}s")
        print(f"Required speed factor: {speed_factor:2F}x")
        
        return speed_factor

def create_video_with_audio(output_folder: str):
    """Create a video with random background footage matching the audio duration, then speed it up based on duration."""
    videos_root = os.path.join(os.path.dirname(__file__), "Videos")
    audio_path = os.path.join(output_folder, "gene_audio.wav")
    
    # Check if audio file exists before proceeding
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
    
    # Get all videos
    folder_to_videos = get_all_video_files(videos_root)
    if not folder_to_videos:
        print(f"Error: No video files found in {videos_root}")
        return
        
    # Decide how many clips to use
    count = int(audio_duration // 5) + 1  # e.g. 1 clip per 5 seconds
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
        
        # Apply duration-based speed with VAAPI
        _apply_duration_based_speed_vaapi(normal_output, output_folder, audio_duration)
        
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


def _apply_duration_based_speed_vaapi(normal_output: str, output_folder: str, duration_seconds: float):
    """Apply duration-based speed to the video using VAAPI hardware acceleration."""
    # Calculate speed factor based on duration
    speed_factor = get_speedup_factor(duration_seconds)
    
    print(f"Video duration: {duration_seconds:.2f}s")
    print(f"Applying {speed_factor:.2f}x speed based on duration rules using VAAPI...")
    
    # If no speedup needed, just rename the file
    if speed_factor == 1.0:
        sped_up_output = os.path.join(output_folder, "final_output.mp4")
        os.rename(normal_output, sped_up_output)
        print(f"✓ No speedup applied (≤60s video): {sped_up_output}")
        return
    
    # Use ffmpeg to speed up the video with VAAPI
    sped_up_output = os.path.join(output_folder, "final_output.mp4")
    setpts_value = round(1.0 / speed_factor, 3)  # For video speed
    atempo_value = speed_factor  # For audio speed
    
    # VAAPI FFmpeg command for AMD GPU hardware acceleration
    ffmpeg_command = [
        'ffmpeg', 
        '-vaapi_device', '/dev/dri/renderD128',  # VAAPI device
        '-i', normal_output,
        '-vf', f'format=nv12,hwupload,setpts={setpts_value}*PTS',  # Upload to GPU and apply speed
        '-filter:a', f'atempo={atempo_value}',  # Audio speed
        '-r', '60',  # Frame rate
        '-c:v', 'h264_vaapi',  # Use VAAPI H.264 encoder
        '-qp', '23',  # Quality parameter (lower = better quality)
        '-threads', '12',  # CPU threads for non-encoding tasks
        '-y', sped_up_output
    ]
    
    try:
        print("Processing video speed change with VAAPI... This should be fast with hardware acceleration.")
        
        # Run ffmpeg with VAAPI hardware acceleration
        result = subprocess.run(
            ffmpeg_command,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutes timeout (hardware encoding should be fast)
            check=False
        )
        
        if result.returncode == 0:
            print(f"✓ Video created with {speed_factor:.2f}x speed using VAAPI: {sped_up_output}")
            # Remove the normal speed video to save space
            if os.path.exists(normal_output):
                os.remove(normal_output)
        else:
            print("✗ VAAPI encoding failed, trying different VAAPI device...")
            if result.stderr:
                print(f"VAAPI error: {result.stderr}")
                
            # Try different VAAPI device (renderD129)
            if _try_alternative_vaapi_device(normal_output, output_folder, speed_factor):
                return
                
            # If VAAPI fails, try CPU fallback
            print("Trying CPU fallback...")
            if _apply_duration_based_speed_cpu_fallback(normal_output, output_folder, speed_factor):
                return
                
            # If both fail, rename normal speed as final output
            if os.path.exists(normal_output):
                os.rename(normal_output, sped_up_output)
                
    except subprocess.TimeoutExpired:
        print("✗ VAAPI encoding timed out after 2 minutes.")
        print("Falling back to CPU encoding...")
        # Try CPU fallback
        if _apply_duration_based_speed_cpu_fallback(normal_output, output_folder, speed_factor):
            return
        print("Keeping normal speed video as final output.")
        if os.path.exists(normal_output):
            os.rename(normal_output, sped_up_output)
            
    except FileNotFoundError:
        print("✗ FFmpeg not found. Please make sure FFmpeg is installed and in your PATH.")
        print("Keeping normal speed video as final output.")
        if os.path.exists(normal_output):
            os.rename(normal_output, sped_up_output)
            
    except Exception as e:
        print(f"✗ Unexpected error during VAAPI encoding: {e}")
        print("Trying CPU fallback...")
        if _apply_duration_based_speed_cpu_fallback(normal_output, output_folder, speed_factor):
            return
        print("Keeping normal speed video as final output.")
        if os.path.exists(normal_output):
            os.rename(normal_output, sped_up_output)
    
    print(f"Final video: {sped_up_output}")


def _try_alternative_vaapi_device(normal_output: str, output_folder: str, speed_factor: float):
    """Try alternative VAAPI device (renderD129) if renderD128 fails."""
    print("Trying alternative VAAPI device (renderD129)...")
    
    sped_up_output = os.path.join(output_folder, "final_output.mp4")
    setpts_value = round(1.0 / speed_factor, 3)
    atempo_value = speed_factor
    
    # Try renderD129
    ffmpeg_command = [
        'ffmpeg', 
        '-vaapi_device', '/dev/dri/renderD129',  # Alternative VAAPI device
        '-i', normal_output,
        '-vf', f'format=nv12,hwupload,setpts={setpts_value}*PTS',
        '-filter:a', f'atempo={atempo_value}',
        '-r', '60',
        '-c:v', 'h264_vaapi',
        '-qp', '23',
        '-threads', '12',
        '-y', sped_up_output
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
            print(f"✓ Alternative VAAPI device successful: {speed_factor:.2f}x speed applied")
            if os.path.exists(normal_output):
                os.remove(normal_output)
            return True
        else:
            print("✗ Alternative VAAPI device also failed")
            if result.stderr:
                print(f"Alternative VAAPI error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Alternative VAAPI device error: {e}")
        return False


def _apply_duration_based_speed_cpu_fallback(normal_output: str, output_folder: str, speed_factor: float):
    """CPU fallback for when hardware encoding fails."""
    print("Using CPU encoding as fallback...")
    
    sped_up_output = os.path.join(output_folder, "final_output.mp4")
    setpts_value = round(1.0 / speed_factor, 3)
    atempo_value = speed_factor
    
    # CPU-based FFmpeg command
    ffmpeg_command = [
        'ffmpeg', '-i', normal_output,
        '-filter:v', f'setpts={setpts_value}*PTS',
        '-filter:a', f'atempo={atempo_value}',
        '-r', '60',
        '-c:v', 'libx264',  # Use CPU encoder
        '-preset', 'fast',
        '-crf', '23',
        '-threads', '12',
        '-y', sped_up_output
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
            print(f"✓ CPU fallback successful: {speed_factor:.2f}x speed applied")
            if os.path.exists(normal_output):
                os.remove(normal_output)
            return True
        else:
            print("✗ CPU fallback also failed")
            if result.stderr:
                print(f"CPU encoding error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ CPU fallback error: {e}")
        return False
    
    print(f"Final video: {sped_up_output}")


def _apply_duration_based_speed_moviepy(normal_output: str, output_folder: str, duration_seconds: float):
    """Alternative method using MoviePy for speed changes (slower but more reliable)."""
    speed_factor = get_speedup_factor(duration_seconds)
    print(f"Video duration: {duration_seconds:.2f}s")
    print(f"Applying {speed_factor:.2f}x speed using MoviePy...")
    
    sped_up_output = os.path.join(output_folder, "final_output.mp4")
    
    # If no speedup needed, just rename the file
    if speed_factor == 1.0:
        os.rename(normal_output, sped_up_output)
        print(f"✓ No speedup applied (≤60s video): {sped_up_output}")
        return
    
    try:
        # Load the video and apply speed change
        clip = VideoFileClip(normal_output)
        sped_clip = clip.fx(lambda gf: gf.speedx(speed_factor))
        
        # Write the sped up video
        sped_clip.write_videofile(
            sped_up_output,
            codec="libx264",
            audio_codec="aac",
            fps=60,
            verbose=False,
            logger=None
        )
        
        # Clean up
        clip.close()
        sped_clip.close()
        
        # Remove normal speed video
        if os.path.exists(normal_output):
            os.remove(normal_output)
            
        print(f"✓ Video created with {speed_factor:.2f}x speed using MoviePy: {sped_up_output}")
        
    except Exception as e:
        print(f"✗ MoviePy speed change failed: {e}")
        print("Keeping normal speed video as final output.")
        if os.path.exists(normal_output):
            os.rename(normal_output, sped_up_output)