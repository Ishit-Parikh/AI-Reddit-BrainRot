"""
main.py
Updated main execution script for bulk story generation first, then audio/video processing.
Uses Official OpenAI API primary with DeepSeek and LMStudio fallback.
"""
import time
import os
import sys
from tqdm import tqdm
import traceback

from text_generator import generate_all_stories_bulk
from audio_generator import generate_audio_from_story
from video_creator import create_video_with_audio


def get_custom_titles(num_runs):
    """Get custom titles from user if they want to provide them."""
    custom_titles = []
    
    use_custom = input("Do you have specific titles in mind for the stories? (y/n): ").lower().strip()
    
    if use_custom in ['y', 'yes']:
        print(f"\nPlease enter {num_runs} title(s):")
        for i in range(num_runs):
            while True:
                title = input(f"Title {i+1}: ").strip()
                if title:
                    custom_titles.append(title)
                    break
                else:
                    print("Please enter a valid title (cannot be empty)")
        
        print(f"\n✓ Got {len(custom_titles)} custom titles!")
        for i, title in enumerate(custom_titles, 1):
            print(f"  {i}. {title}")
    
    return custom_titles


def process_audio_for_all_stories(stories_data):
    """
    Process audio generation for all stories.
    
    Args:
        stories_data (list): List of tuples (title, story, output_folder)
        
    Returns:
        list: List of tuples (title, story, output_folder) for successful audio generations
    """
    print(f"\n{'='*50}")
    print(f"🎵 BULK AUDIO GENERATION PHASE")
    print(f"Processing audio for {len(stories_data)} stories...")
    print(f"{'='*50}")
    
    successful_audio = []
    
    for i, (title, story, output_folder) in enumerate(stories_data, 1):
        print(f"\n🎙️ Processing audio {i}/{len(stories_data)}: {title}")
        print("-" * 40)
        
        try:
            generate_audio_from_story(story, output_folder)
            successful_audio.append((title, story, output_folder))
            print(f"✅ Audio {i} completed: {title}")
        except Exception as e:
            print(f"❌ Audio {i} failed: {title} - {e}")
            traceback.print_exc()
    
    print(f"\n{'='*50}")
    print(f"📊 BULK AUDIO GENERATION COMPLETE")
    print(f"Successfully processed: {len(successful_audio)}/{len(stories_data)} audio files")
    print(f"{'='*50}")
    
    return successful_audio


def process_video_for_all_stories(stories_data):
    """
    Process video creation for all stories.
    
    Args:
        stories_data (list): List of tuples (title, story, output_folder)
        
    Returns:
        list: List of tuples (title, story, output_folder) for successful video creations
    """
    print(f"\n{'='*50}")
    print(f"🎬 BULK VIDEO CREATION PHASE")
    print(f"Processing videos for {len(stories_data)} stories...")
    print(f"{'='*50}")
    
    successful_videos = []
    
    for i, (title, story, output_folder) in enumerate(stories_data, 1):
        print(f"\n📹 Processing video {i}/{len(stories_data)}: {title}")
        print("-" * 40)
        
        try:
            create_video_with_audio(output_folder)
            successful_videos.append((title, story, output_folder))
            print(f"✅ Video {i} completed: {title}")
        except Exception as e:
            print(f"❌ Video {i} failed: {title} - {e}")
            traceback.print_exc()
    
    print(f"\n{'='*50}")
    print(f"📊 BULK VIDEO CREATION COMPLETE")
    print(f"Successfully processed: {len(successful_videos)}/{len(stories_data)} videos")
    print(f"{'='*50}")
    
    return successful_videos


def run_bulk_pipeline(num_runs: int, custom_titles: list = None):
    """
    Execute the complete bulk pipeline: Stories → Audio → Video.
    
    Args:
        num_runs (int): Number of stories to process
        custom_titles (list, optional): List of custom titles to use
        
    Returns:
        dict: Summary of results for each phase
    """
    print(f"\n{'='*60}")
    print(f"🚀 STARTING BULK CONTENT GENERATION PIPELINE")
    print(f"Target: {num_runs} complete stories with audio and video")
    print(f"{'='*60}")
    
    # Phase 1: Generate all stories
    stories_data = generate_all_stories_bulk(num_runs, custom_titles)
    
    if not stories_data:
        print("❌ No stories were generated successfully. Aborting pipeline.")
        return {
            'stories': 0,
            'audio': 0,
            'videos': 0,
            'total_requested': num_runs
        }
    
    # Phase 2: Process audio for all stories
    audio_data = process_audio_for_all_stories(stories_data)
    
    if not audio_data:
        print("❌ No audio files were generated successfully. Aborting video creation.")
        return {
            'stories': len(stories_data),
            'audio': 0,
            'videos': 0,
            'total_requested': num_runs
        }
    
    # Phase 3: Process video for all stories
    video_data = process_video_for_all_stories(audio_data)
    
    return {
        'stories': len(stories_data),
        'audio': len(audio_data),
        'videos': len(video_data),
        'total_requested': num_runs
    }


def run_single_story(custom_title=None):
    """
    Execute one complete run of the content generation pipeline (legacy mode).
    
    Args:
        custom_title (str, optional): Custom title to use instead of generating one
        
    Returns:
        bool: True if successful, False otherwise
    """
    steps = [
        "Generating title and story with Official OpenAI/DeepSeek/LMStudio" if not custom_title else "Generating story with custom title using Official OpenAI/DeepSeek/LMStudio",
        "Generating audio narration", 
        "Creating video with audio and applying speed",
    ]
    
    with tqdm(total=len(steps), file=sys.stdout, 
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] {postfix}') as pbar:
        try:
            # Import here to avoid circular import
            from text_generator import generate_text_content
            
            # Phase 1: Generate text content
            pbar.set_postfix_str(steps[0])
            if custom_title: 
                print(f"Using custom title: {custom_title}")
            
            title, story, output_folder = generate_text_content(custom_title)
            
            if not title or not story or not output_folder:
                print("✗ Failed to generate text content. Aborting this run.")
                return False
            
            pbar.update(1)

            # Phase 2: Audio generation
            pbar.set_postfix_str(steps[1])
            generate_audio_from_story(story, output_folder)
            pbar.update(1)

            # Phase 3: Video creation
            pbar.set_postfix_str(steps[2])
            create_video_with_audio(output_folder)
            pbar.update(1)
            
            print(f"✓ Run completed successfully! Output saved to: {output_folder}")
            return True

        except Exception as e:
            print(f"✗ An error occurred during processing: {e}")
            traceback.print_exc()
            return False


def check_lmstudio_needed():
    """
    Check if LMStudio server needs to be started.
    We'll start it preemptively since we might need it as final fallback.
    """
    print("ℹ Starting LMStudio server as final fallback option...")
    print("  (Official OpenAI will be tried first, DeepSeek second, LMStudio serves as final backup)")
    return True


if __name__ == "__main__":
    print("🎬 FRBV Content Generation Pipeline")
    print("=" * 50)
    
    num_runs = int(input("How many stories would you like to create? (Enter a number): "))
    
    # Get custom titles if user wants to provide them
    custom_titles = get_custom_titles(num_runs)
    
    # Ask user for processing mode
    if num_runs > 1:
        print("\n📋 Processing Mode Options:")
        print("1. BULK MODE (Recommended): Generate all stories first, then process audio/video")
        print("2. LEGACY MODE: Process each story completely before moving to next")
        
        mode_choice = input("\nChoose processing mode (1 or 2): ").strip()
        use_bulk_mode = mode_choice != "2"
    else:
        use_bulk_mode = False  # Single story always uses legacy mode
    
    # Start LMStudio server as fallback option
    if check_lmstudio_needed():
        print("\n✓ Starting LMStudio server (fallback)...")
        os.system("lms server start")
        print("✓ LMStudio server started successfully")
        print("ℹ Will attempt Official OpenAI first, DeepSeek second, then LMStudio if needed\n")
    
    if use_bulk_mode:
        # BULK MODE: Generate all stories first, then process audio/video
        results = run_bulk_pipeline(num_runs, custom_titles)
        
        print(f"\n{'='*60}")
        print("📊 FINAL PIPELINE SUMMARY")
        print(f"{'='*60}")
        print(f"📝 Stories Generated: {results['stories']}/{results['total_requested']}")
        print(f"🎵 Audio Files Created: {results['audio']}/{results['total_requested']}")
        print(f"🎬 Videos Created: {results['videos']}/{results['total_requested']}")
        print(f"✅ Complete Success Rate: {results['videos']}/{results['total_requested']} ({results['videos']/results['total_requested']*100:.1f}%)")
        
    else:
        # LEGACY MODE: Process each story completely before moving to next
        print(f"\n🔄 Using Legacy Mode: Processing {num_runs} stories sequentially...")
        successful_runs = 0
        
        for i in range(num_runs):
            print(f"\n{'='*50}")
            print(f"Run {i+1} of {num_runs}")
            print(f"{'='*50}")
            
            # Use custom title if available, otherwise None for auto-generation
            current_title = custom_titles[i] if custom_titles else None
            
            if run_single_story(current_title):
                successful_runs += 1
            
            if i < num_runs - 1:  # Not the last run
                print("Completed run {}. Preparing for next run...".format(i+1))
                time.sleep(3)  # Brief pause between runs
        
        print(f"\n{'='*50}")
        print("All runs completed!")
        print(f"Successful runs: {successful_runs}/{num_runs}")
        print(f"{'='*50}")
    
    print("\n✓ Stopping LMStudio server...")
    os.system("lms server stop")
    
    # Final summary
    print(f"\n{'='*60}")
    print("🎉 PIPELINE COMPLETE!")
    print(f"{'='*60}")
    print("\n🔧 API Priority Summary:")
    print("• Primary: Official OpenAI API (gpt-4o-mini)")
    print("• Secondary: DeepSeek API (fast, powerful reasoning)")
    print("• Final Fallback: LMStudio (local, always available)")
    print("• System automatically chose the best available option for each generation")
    
    if use_bulk_mode:
        print(f"\n📈 Bulk Processing Benefits:")
        print("• Faster overall completion time")
        print("• Better resource utilization")
        print("• Easier error tracking and recovery")
        print("• Cleaner progress visualization")