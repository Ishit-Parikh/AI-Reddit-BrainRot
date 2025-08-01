"""
main.py
Updated main execution script with configuration management.
Pipeline: Stories → Audio → Video → Transcription → Subtitled Video (optional)
"""
import time
import os
import sys
from tqdm import tqdm
import traceback

# Import configuration manager first
from config_manager import initialize_config, get_config

# Then import other modules
from text_generator import generate_all_stories_bulk
from audio_generator import generate_audio_from_story
from video_creator import create_video_with_audio
from transcription_integration import (
    process_transcription_bulk, 
    add_transcription_to_single_story_pipeline
)


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


def get_transcription_preferences():
    """Get user preferences for transcription options."""
    print("\n🎤 Transcription Options:")
    print("1. Generate SRT subtitles only")
    print("2. Generate SRT subtitles + videos with embedded subtitles")
    print("3. Generate ASS subtitles (viral style) + videos with embedded subtitles")
    print("4. Skip transcription")
    
    choice = input("\nChoose transcription option (1, 2, 3, or 4): ").strip()
    
    # Check if user wants to include title in subtitles
    include_title = False
    if choice in ["1", "2", "3"]:
        include_title_choice = input("\nInclude story title in subtitles? (y/n) [n]: ").strip().lower()
        include_title = include_title_choice == 'y'
    
    if choice == "1":
        return True, False, False, include_title  # transcribe, don't embed, no ASS
    elif choice == "2":
        return True, True, False, include_title   # transcribe and embed SRT
    elif choice == "3":
        return True, True, True, include_title    # transcribe and embed ASS
    else:
        return False, False, False, False # skip transcription


def process_audio_for_all_stories(stories_data):
    """Process audio generation for all stories."""
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
    """Process video creation for all stories."""
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


def run_bulk_pipeline(num_runs: int, custom_titles: list = None, enable_transcription: bool = True, 
                      create_subtitled_videos: bool = False, use_ass: bool = False, include_title: bool = False):
    """
    Execute the complete bulk pipeline: Stories → Audio → Video → Transcription.
    """
    print(f"\n{'='*60}")
    print(f"🚀 STARTING ENHANCED BULK CONTENT GENERATION PIPELINE")
    print(f"Target: {num_runs} complete stories with audio, video", end="")
    if enable_transcription:
        print(", and transcription", end="")
        if create_subtitled_videos:
            print(" + subtitled videos", end="")
    print(f"\n{'='*60}")
    
    # Phase 1: Generate all stories
    stories_data = generate_all_stories_bulk(num_runs, custom_titles)
    
    if not stories_data:
        print("❌ No stories were generated successfully. Aborting pipeline.")
        return {
            'stories': 0, 'audio': 0, 'videos': 0, 'transcriptions': 0,
            'total_requested': num_runs
        }
    
    # Phase 2: Process audio for all stories
    audio_data = process_audio_for_all_stories(stories_data)
    
    if not audio_data:
        print("❌ No audio files were generated successfully. Aborting video creation.")
        return {
            'stories': len(stories_data), 'audio': 0, 'videos': 0, 'transcriptions': 0,
            'total_requested': num_runs
        }
    
    # Phase 3: Process video for all stories
    video_data = process_video_for_all_stories(audio_data)
    
    # Phase 4: Process transcription for all stories (if enabled)
    transcription_data = []
    if enable_transcription and video_data:
        transcription_data = process_transcription_bulk(video_data, create_subtitled_videos, use_ass, include_title)
    
    return {
        'stories': len(stories_data),
        'audio': len(audio_data),
        'videos': len(video_data),
        'transcriptions': len(transcription_data),
        'total_requested': num_runs
    }


def run_single_story(custom_title=None, enable_transcription=True, create_subtitled_video=False, 
                     use_ass=False, include_title=False):
    """
    Execute one complete run of the content generation pipeline with transcription.
    """
    steps = [
        "Generating title and story with AI" if not custom_title else "Generating story with custom title using AI",
        "Generating audio narration", 
        "Creating video with audio and applying speed",
    ]
    
    if enable_transcription:
        steps.append("Generating transcription and subtitles")
        if create_subtitled_video:
            steps.append("Creating video with embedded subtitles")
    
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
            
            # Phase 4: Transcription (if enabled)
            if enable_transcription:
                pbar.set_postfix_str(steps[3])
                transcription_results = add_transcription_to_single_story_pipeline(
                    output_folder, create_subtitled_video, use_ass, include_title
                )
                pbar.update(1)
                
                if create_subtitled_video and transcription_results:
                    pbar.update(1)  # For the subtitled video step
            
            print(f"✓ Run completed successfully! Output saved to: {output_folder}")
            
            # Print summary of generated files
            print("\n📁 Generated files:")
            print(f"   📝 Story: story.txt")
            print(f"   🎵 Audio: gene_audio.wav")
            print(f"   🎬 Video: final_output.mp4")
            if enable_transcription:
                print(f"   📄 Transcript: transcript.txt")
                if transcription_results and transcription_results.get('srt_file'):
                    srt_filename = os.path.basename(transcription_results['srt_file'])
                    if 'synced' in srt_filename:
                        print(f"   📺 Subtitles: {srt_filename} (speed-adjusted)")
                    else:
                        print(f"   📺 Subtitles: {srt_filename}")
                if use_ass and transcription_results and transcription_results.get('ass_file'):
                    print(f"   🎨 ASS Subtitles: {os.path.basename(transcription_results['ass_file'])}")
                if create_subtitled_video and transcription_results and transcription_results.get('subtitled_video'):
                    print(f"   🎬 Subtitled Video: final_output_with_subtitles.mp4")
            
            return True

        except Exception as e:
            print(f"✗ An error occurred during processing: {e}")
            traceback.print_exc()
            return False


def check_lmstudio_needed():
    """Check if LMStudio server needs to be started."""
    lmstudio_model = get_config('lmstudio_model_name')
    if lmstudio_model:
        print("ℹ Starting LMStudio server as final fallback option...")
        print("  (Official OpenAI will be tried first, DeepSeek second, LMStudio serves as final backup)")
        return True
    return False


def check_whisper_installation():
    """Check if Whisper is installed for transcription."""
    try:
        import whisper
        print("✅ Whisper is installed and ready for transcription")
        return True
    except ImportError:
        print("⚠️ Whisper not found. To enable transcription, install it with:")
        print("   pip install openai-whisper")
        return False


if __name__ == "__main__":
    print("🎬 Enhanced FRBV Content Generation Pipeline")
    print("=" * 60)
    
    # Initialize configuration
    print("\n📋 Loading configuration...")
    config = initialize_config()
    print("✅ Configuration loaded successfully!")
    
    # Check Whisper installation
    whisper_available = check_whisper_installation()
    
    num_runs = int(input("\nHow many stories would you like to create? (Enter a number): "))
    
    # Get custom titles if user wants to provide them
    custom_titles = get_custom_titles(num_runs)
    
    # Get transcription preferences
    enable_transcription, create_subtitled_videos, use_ass, include_title = False, False, False, False
    if whisper_available:
        enable_transcription, create_subtitled_videos, use_ass, include_title = get_transcription_preferences()
    else:
        print("\n⚠️ Transcription will be skipped (Whisper not available)")
    
    # Ask user for processing mode
    if num_runs > 1:
        print("\n📋 Processing Mode Options:")
        print("1. BULK MODE (Recommended): Generate all stories first, then process audio/video/transcription")
        print("2. LEGACY MODE: Process each story completely before moving to next")
        
        mode_choice = input("\nChoose processing mode (1 or 2): ").strip()
        use_bulk_mode = mode_choice != "2"
    else:
        use_bulk_mode = False  # Single story always uses legacy mode
    
    # Start LMStudio server if configured
    if check_lmstudio_needed():
        print("\n✓ Starting LMStudio server (fallback)...")
        os.system("lms server start")
        print("✓ LMStudio server started successfully")
        print("ℹ Will attempt Official OpenAI first, DeepSeek second, then LMStudio if needed\n")
    
    if use_bulk_mode:
        # BULK MODE: Generate all content in phases
        results = run_bulk_pipeline(num_runs, custom_titles, enable_transcription, 
                                   create_subtitled_videos, use_ass, include_title)
        
        print(f"\n{'='*60}")
        print("📊 FINAL PIPELINE SUMMARY")
        print(f"{'='*60}")
        print(f"📝 Stories Generated: {results['stories']}/{results['total_requested']}")
        print(f"🎵 Audio Files Created: {results['audio']}/{results['total_requested']}")
        print(f"🎬 Videos Created: {results['videos']}/{results['total_requested']}")
        
        if enable_transcription:
            print(f"🎤 Transcriptions Created: {results['transcriptions']}/{results['total_requested']}")
            success_metric = results['transcriptions']
        else:
            success_metric = results['videos']
            
        print(f"✅ Complete Success Rate: {success_metric}/{results['total_requested']} ({success_metric/results['total_requested']*100:.1f}%)")
        
    else:
        # LEGACY MODE: Process each story completely before moving to next
        pipeline_name = "Enhanced Legacy Mode" if enable_transcription else "Legacy Mode"
        print(f"\n🔄 Using {pipeline_name}: Processing {num_runs} stories sequentially...")
        successful_runs = 0
        
        for i in range(num_runs):
            print(f"\n{'='*50}")
            print(f"Run {i+1} of {num_runs}")
            print(f"{'='*50}")
            
            # Use custom title if available, otherwise None for auto-generation
            current_title = custom_titles[i] if custom_titles else None
            
            if run_single_story(current_title, enable_transcription, create_subtitled_videos, use_ass, include_title):
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
    print("🎉 ENHANCED PIPELINE COMPLETE!")
    print(f"{'='*60}")
    print("\n🔧 API Priority Summary:")
    print("• Primary: Official OpenAI API")
    print("• Secondary: DeepSeek API")
    print("• Final Fallback: LMStudio (local, always available)")
    print("• System automatically chose the best available option for each generation")
    
    if enable_transcription:
        print(f"\n🎤 Transcription Features:")
        print("• Word-level subtitle timing for better readability")
        print("• SRT files compatible with all video players")
        print("• Full transcript text files for reference")
        if use_ass:
            print("• ASS files with viral-style animated subtitles")
        if create_subtitled_videos:
            print("• Videos with embedded subtitles for direct sharing")
        if include_title:
            print("• Story titles included in subtitles")
    
    if use_bulk_mode:
        print(f"\n📈 Bulk Processing Benefits:")
        print("• Faster overall completion time")
        print("• Better resource utilization")
        print("• Easier error tracking and recovery")
        print("• Cleaner progress visualization")
        if enable_transcription:
            print("• Efficient batch transcription processing")