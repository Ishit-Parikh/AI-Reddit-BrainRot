"""
video_utils.py
Video utility functions for handling video files and selections.
"""
import os
import random


def get_all_video_files(videos_root: str):
    """Return a dict mapping folder names to lists of video file paths."""
    folder_to_videos = {}
    for folder in os.listdir(videos_root):
        folder_path = os.path.join(videos_root, folder)
        if os.path.isdir(folder_path):
            videos = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                      if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]
            if videos:
                folder_to_videos[folder] = videos
    return folder_to_videos


def pick_non_repeating_videos(folder_to_videos, count):
    """
    Pick 'count' videos with advanced rules:
    - No video repetition
    - No consecutive videos from same folder
    - Round-robin folder selection (folder only reused after all others used once)
    """
    # Calculate total available videos
    total_videos = sum(len(videos) for videos in folder_to_videos.values())
    if count > total_videos:
        raise ValueError(f"Cannot select {count} unique videos. Maximum is {total_videos}.")
    
    # Initialize tracking variables
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
        candidate_folders = available_folders_in_round.copy()
        if last_folder and last_folder in candidate_folders and len(candidate_folders) > 1:
            candidate_folders.remove(last_folder)
        
        # Try to find a folder with unused videos
        selected_folder = None
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
            available_folders_in_round.remove(selected_folder)
            last_folder = selected_folder
        else:
            # No valid selection possible
            break
    
    return result