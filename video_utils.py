"""
video_utils.py
Video utility functions with flexible folder handling.
Supports both flat folder structure and subfolders.
"""
import os
import random
from pathlib import Path


def get_all_video_files(videos_root: str):
    """
    Return a dict mapping folder names to lists of video file paths.
    Handles both:
    - Flat structure (videos directly in videos_root)
    - Subfolder structure (videos organized in subfolders)
    """
    folder_to_videos = {}
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    
    videos_root_path = Path(videos_root)
    if not videos_root_path.exists():
        print(f"Warning: Videos root path does not exist: {videos_root}")
        return folder_to_videos
    
    # First, check for videos directly in the root folder
    root_videos = []
    for file in videos_root_path.iterdir():
        if file.is_file() and file.suffix.lower() in video_extensions:
            root_videos.append(str(file))
    
    # If we found videos in root, treat it as a single "folder"
    if root_videos:
        folder_to_videos["_root"] = root_videos
    
    # Then check for subfolders with videos
    for item in videos_root_path.iterdir():
        if item.is_dir():
            folder_videos = []
            for file in item.iterdir():
                if file.is_file() and file.suffix.lower() in video_extensions:
                    folder_videos.append(str(file))
            
            if folder_videos:
                folder_to_videos[item.name] = folder_videos
    
    # If no videos found anywhere, print helpful message
    if not folder_to_videos:
        print(f"No video files found in {videos_root}")
        print(f"Supported formats: {', '.join(video_extensions)}")
        print("\nFolder structure options:")
        print("1. Place videos directly in the videos folder")
        print("2. Organize videos in subfolders within the videos folder")
    
    return folder_to_videos


def pick_non_repeating_videos(folder_to_videos, count):
    """
    Pick 'count' videos with advanced rules:
    - No video repetition
    - No consecutive videos from same folder (when possible)
    - Round-robin folder selection (when multiple folders exist)
    - Falls back gracefully when constraints can't be met
    """
    # Calculate total available videos
    total_videos = sum(len(videos) for videos in folder_to_videos.values())
    if count > total_videos:
        raise ValueError(f"Cannot select {count} unique videos. Maximum is {total_videos}.")
    
    # If only one folder exists, simply pick random videos without repetition
    if len(folder_to_videos) == 1:
        folder_name = list(folder_to_videos.keys())[0]
        all_videos = folder_to_videos[folder_name]
        return random.sample(all_videos, min(count, len(all_videos)))
    
    # Multiple folders exist - apply advanced selection rules
    result = []
    used_videos = set()
    last_folder = None
    
    # Round-robin state tracking
    available_folders_in_round = set(folder_to_videos.keys())
    folders_with_videos = {folder: list(videos) for folder, videos in folder_to_videos.items() if videos}
    
    for _ in range(count):
        # If no folders available in current round, start new round
        if not available_folders_in_round:
            # Reset round with folders that still have unused videos
            available_folders_in_round = {
                folder for folder, videos in folders_with_videos.items() 
                if any(video not in used_videos for video in videos)
            }
            
            # If no folders have unused videos, we're done
            if not available_folders_in_round:
                break
        
        # Get candidate folders (exclude last used folder to avoid consecutive)
        candidate_folders = list(available_folders_in_round)
        if last_folder and last_folder in candidate_folders and len(candidate_folders) > 1:
            candidate_folders.remove(last_folder)
        
        # Try to find a folder with unused videos
        selected_folder = None
        random.shuffle(candidate_folders)  # Randomize selection
        
        for folder in candidate_folders:
            unused_videos = [v for v in folders_with_videos[folder] if v not in used_videos]
            if unused_videos:
                selected_folder = folder
                break
        
        # If no candidate folder found, try last_folder as fallback
        if not selected_folder and last_folder in available_folders_in_round:
            unused_videos = [v for v in folders_with_videos[last_folder] if v not in used_videos]
            if unused_videos:
                selected_folder = last_folder
        
        # If still no folder found, pick any available folder with unused videos
        if not selected_folder:
            for folder in available_folders_in_round:
                unused_videos = [v for v in folders_with_videos[folder] if v not in used_videos]
                if unused_videos:
                    selected_folder = folder
                    break
        
        # If we found a folder, select a random unused video from it
        if selected_folder:
            unused_videos = [v for v in folders_with_videos[selected_folder] if v not in used_videos]
            selected_video = random.choice(unused_videos)
            
            # Add to result and mark as used
            result.append(selected_video)
            used_videos.add(selected_video)
            
            # Update round tracking
            available_folders_in_round.discard(selected_folder)
            last_folder = selected_folder
        else:
            # No valid selection possible
            break
    
    return result


def analyze_video_structure(videos_root: str):
    """
    Analyze and report the video folder structure to help users organize their content.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    folder_to_videos = get_all_video_files(videos_root)
    
    if not folder_to_videos:
        return
    
    print(f"\n📁 Video Library Analysis:")
    print(f"{'='*50}")
    
    total_videos = 0
    for folder, videos in sorted(folder_to_videos.items()):
        folder_display = "Root folder" if folder == "_root" else f"Subfolder: {folder}"
        print(f"{folder_display}: {len(videos)} videos")
        total_videos += len(videos)
    
    print(f"{'='*50}")
    print(f"Total videos available: {total_videos}")
    
    if len(folder_to_videos) == 1 and "_root" in folder_to_videos:
        print("\n💡 Tip: You can organize videos into subfolders for better variety")
        print("   Example: Videos/Nature/, Videos/City/, Videos/Abstract/")
    elif len(folder_to_videos) > 1:
        print("\n✅ Great! Videos are organized in multiple folders for variety")