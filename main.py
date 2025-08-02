"""
main.py
Enhanced main execution script with clean organization and AI provider selection.
Pipeline: Stories → Audio → Video → Transcription → Subtitled Video (optional)
"""
import time
import os
import sys
from tqdm import tqdm
import traceback


def clear_terminal():
    """Clear the terminal screen for cleaner output."""
    os.system('cls' if os.name == 'nt' else 'clear')

# Import configuration manager first
from config_manager import initialize_config, get_config, get_config_manager

# Then import other modules
from text_generator import generate_all_stories_bulk, generate_text_content
from audio_generator import generate_audio_from_story
from video_creator import create_video_with_audio
from transcription_integration import (
    process_transcription_bulk, 
    add_transcription_to_single_story_pipeline
)


class PipelineConfig:
    """Container for all pipeline configuration options."""
    def __init__(self):
        self.num_runs = 0
        self.custom_titles = []
        self.ai_provider = None
        self.use_batch_api = False
        self.enable_transcription = False
        self.create_subtitled_videos = False
        self.use_ass = False
        self.include_title_in_ass = False
        self.use_bulk_mode = True


def get_user_preferences(whisper_available: bool) -> PipelineConfig:
    """Gather all user preferences for the pipeline."""
    config = PipelineConfig()
    
    # Clear terminal for clean interface
    clear_terminal()
    
    # Select AI provider
    print("🤖 Selecting AI provider...")
    config_manager = get_config_manager()
    config.ai_provider, config.use_batch_api = config_manager.select_ai_provider()
    print(f"✅ Using {config.ai_provider.upper()}" + 
          (" with batch processing" if config.use_batch_api else ""))
    
    # Number of stories
    config.num_runs = int(input("\nHow many stories would you like to create? (Enter a number): "))
    
    # Custom titles
    config.custom_titles = get_custom_titles(config.num_runs)
    
    # Transcription preferences
    if whisper_available:
        transcription_settings = get_transcription_preferences()
        config.enable_transcription = transcription_settings[0]
        config.create_subtitled_videos = transcription_settings[1]
        config.use_ass = transcription_settings[2]
        config.include_title_in_ass = transcription_settings[3]
    else:
        print("\n⚠️ Transcription will be skipped (Whisper not available)")
    
    # Processing mode is always bulk for multiple stories
    # Batch API is only available for OpenAI and already selected above
    config.use_bulk_mode = config.num_runs > 1
    
    if config.use_bulk_mode:
        print("\n📋 Using BULK MODE for multiple stories")
        print("   All stories will be generated first, then audio, video, and transcription")
    else:
        print("\n📋 Using single story processing")
    
    return config


def get_custom_titles(num_runs: int) -> list:
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


def get_transcription_preferences() -> tuple:
    """Get user preferences for transcription options."""
    print("\n🎤 Transcription Options:")
    print("1. Generate SRT subtitles only")
    print("2. Generate SRT subtitles + videos with embedded subtitles")
    print("3. Generate ASS subtitles (viral style) + videos with embedded subtitles")
    print("4. Skip transcription")
    
    choice = input("\nChoose transcription option (1, 2, 3, or 4): ").strip()
    
    # Check if user wants to include title in ASS subtitles
    include_title_in_ass = False
    if choice == "3":
        include_title_choice = input("\nInclude story title in ASS subtitles? (y/n) [n]: ").strip().lower()
        include_title_in_ass = include_title_choice == 'y'
        print("Note: Title will always be included in SRT subtitles")
    
    if choice == "1":
        return True, False, False, False  # transcribe, don't embed, no ASS, no title in ASS
    elif choice == "2":
        return True, True, False, False   # transcribe and embed SRT
    elif choice == "3":
        return True, True, True, include_title_in_ass    # transcribe and embed ASS
    else:
        return False, False, False, False # skip transcription


def process_audio_for_all_stories(stories_data: list) -> list:
    """Process audio generation for all stories."""
    clear_terminal()
    print(f"{'='*50}")
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


def process_video_for_all_stories(stories_data: list) -> list:
    """Process video creation for all stories."""
    clear_terminal()
    print(f"{'='*50}")
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


def run_bulk_pipeline(config: PipelineConfig) -> dict:
    """Execute the complete bulk pipeline: Stories → Audio → Video → Transcription."""
    clear_terminal()
    print(f"{'='*60}")
    print(f"🚀 STARTING ENHANCED BULK CONTENT GENERATION PIPELINE")
    print(f"Target: {config.num_runs} complete stories with audio, video", end="")
    if config.enable_transcription:
        print(", and transcription", end="")
        if config.create_subtitled_videos:
            print(" + subtitled videos", end="")
    print(f"\n{'='*60}")
    
    # Phase 1: Generate all stories
    stories_data = generate_all_stories_bulk(
        config.num_runs, 
        config.custom_titles, 
        config.ai_provider, 
        config.use_batch_api
    )
    
    if not stories_data:
        print("❌ No stories were generated successfully. Aborting pipeline.")
        return {
            'stories': 0, 'audio': 0, 'videos': 0, 'transcriptions': 0,
            'total_requested': config.num_runs
        }
    
    # Phase 2: Process audio for all stories
    audio_data = process_audio_for_all_stories(stories_data)
    
    if not audio_data:
        print("❌ No audio files were generated successfully. Aborting video creation.")
        return {
            'stories': len(stories_data), 'audio': 0, 'videos': 0, 'transcriptions': 0,
            'total_requested': config.num_runs
        }
    
    # Phase 3: Process video for all stories
    video_data = process_video_for_all_stories(audio_data)
    
    # Phase 4: Process transcription for all stories (if enabled)
    transcription_data = []
    if config.enable_transcription and video_data:
        transcription_data = process_transcription_bulk(
            video_data, 
            config.create_subtitled_videos, 
            config.use_ass, 
            config.include_title_in_ass
        )
    
    return {
        'stories': len(stories_data),
        'audio': len(audio_data),
        'videos': len(video_data),
        'transcriptions': len(transcription_data),
        'total_requested': config.num_runs
    }


def run_single_story(title: str, config: PipelineConfig) -> bool:
    """Execute one complete run of the content generation pipeline."""
    steps = [
        "Generating title and story with AI" if not title else "Generating story with custom title using AI",
        "Generating audio narration", 
        "Creating video with audio and applying speed",
    ]
    
    if config.enable_transcription:
        steps.append("Generating transcription and subtitles")
        if config.create_subtitled_videos:
            steps.append("Creating video with embedded subtitles")
    
    with tqdm(total=len(steps), file=sys.stdout, 
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] {postfix}') as pbar:
        try:
            # Phase 1: Generate text content
            pbar.set_postfix_str(steps[0])
            if title: 
                print(f"Using custom title: {title}")
            
            title, story, output_folder = generate_text_content(title)
            
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
            if config.enable_transcription:
                pbar.set_postfix_str(steps[3])
                transcription_results = add_transcription_to_single_story_pipeline(
                    output_folder, 
                    config.create_subtitled_videos, 
                    config.use_ass, 
                    config.include_title_in_ass
                )
                pbar.update(1)
                
                if config.create_subtitled_videos and transcription_results:
                    pbar.update(1)  # For the subtitled video step
            
            print(f"✓ Run completed successfully! Output saved to: {output_folder}")
            print_output_summary(config, transcription_results if config.enable_transcription else None)
            
            return True

        except Exception as e:
            print(f"✗ An error occurred during processing: {e}")
            traceback.print_exc()
            return False


def run_legacy_mode(config: PipelineConfig) -> int:
    """Process stories one at a time in legacy mode."""
    clear_terminal()
    print(f"🔄 Using Legacy Mode: Processing {config.num_runs} stories sequentially...")
    successful_runs = 0
    
    # Set global provider for legacy mode
    import text_generator
    text_generator._active_provider = config.ai_provider
    
    for i in range(config.num_runs):
        clear_terminal()
        print(f"{'='*50}")
        print(f"Run {i+1} of {config.num_runs}")
        print(f"{'='*50}")
        
        # Use custom title if available
        current_title = config.custom_titles[i] if i < len(config.custom_titles) else None
        
        if run_single_story(current_title, config):
            successful_runs += 1
        
        if i < config.num_runs - 1:  # Not the last run
            print(f"Completed run {i+1}. Preparing for next run...")
            time.sleep(3)  # Brief pause between runs
    
    return successful_runs


def print_output_summary(config: PipelineConfig, transcription_results: dict = None):
    """Print summary of generated files."""
    print("\n📁 Generated files:")
    print("   📝 Story: story.txt")
    print("   📝 Title: title.txt")
    print("   🎵 Audio: gene_audio.wav")
    print("   🎬 Video: gene_video.mp4", end="")
    
    if config.enable_transcription and config.create_subtitled_videos and transcription_results and transcription_results.get('subtitled_video'):
        print(" (with embedded subtitles)")
    else:
        print()
    
    if config.enable_transcription and transcription_results:
        if transcription_results.get('srt_file'):
            print("   📺 SRT Subtitles: subtitles.srt (title always included)")
        if config.use_ass and transcription_results.get('ass_file'):
            print("   🎨 ASS Subtitles: subtitles.ass", end="")
            if config.include_title_in_ass:
                print(" (title included)")
            else:
                print(" (title NOT included)")


def print_final_summary(config: PipelineConfig, results: dict = None, successful_runs: int = None):
    """Print final summary of the pipeline execution."""
    clear_terminal()
    print(f"{'='*60}")
    print("🎉 ENHANCED PIPELINE COMPLETE!")
    print(f"{'='*60}")
    
    # AI Provider info
    print(f"\n🤖 AI Provider Used: {config.ai_provider.upper()}")
    if config.use_batch_api:
        print("   - Batch processing mode (up to 24 hours)")
    else:
        print("   - Sequential processing mode")
    
    # Results summary
    if results:  # Bulk mode
        print("\n📊 FINAL PIPELINE SUMMARY")
        print(f"📝 Stories Generated: {results['stories']}/{results['total_requested']}")
        print(f"🎵 Audio Files Created: {results['audio']}/{results['total_requested']}")
        print(f"🎬 Videos Created: {results['videos']}/{results['total_requested']}")
        
        if config.enable_transcription:
            print(f"🎤 Transcriptions Created: {results['transcriptions']}/{results['total_requested']}")
            success_metric = results['transcriptions']
        else:
            success_metric = results['videos']
            
        print(f"✅ Complete Success Rate: {success_metric}/{results['total_requested']} ({success_metric/results['total_requested']*100:.1f}%)")
    
    elif successful_runs is not None:  # Legacy mode
        print(f"\n📊 Successfully completed: {successful_runs}/{config.num_runs} stories")
    
    # Feature summary
    if config.enable_transcription:
        print("\n🎤 Transcription Features:")
        print("• Word-level subtitle timing for better readability")
        print("• SRT files compatible with all video players")
        if config.use_ass:
            print("• ASS files with viral-style animated subtitles")
        if config.create_subtitled_videos:
            print("• Videos with embedded subtitles for direct sharing")
        if config.include_title_in_ass and config.use_ass:
            print("• Story titles included in ASS subtitles")
        print("• Story titles always included in SRT subtitles")
    
    if config.use_bulk_mode:
        print("\n📈 Bulk Processing Benefits:")
        print("• Faster overall completion time")
        print("• Better resource utilization")
        print("• Easier error tracking and recovery")
        print("• Cleaner progress visualization")
        if config.enable_transcription:
            print("• Efficient batch transcription processing")


def check_whisper_installation() -> bool:
    """Check if Whisper is installed for transcription."""
    try:
        import whisper
        print("✅ Whisper is installed and ready for transcription")
        return True
    except ImportError:
        print("⚠️ Whisper not found. To enable transcription, install it with:")
        print("   pip install openai-whisper")
        return False


def check_lmstudio_needed() -> bool:
    """Check if LMStudio server needs to be started."""
    lmstudio_model = get_config('lmstudio_model_name')
    if lmstudio_model:
        print("ℹ Starting LMStudio server...")
        return True
    return False


def main():
    """Main entry point for the Brain Rot pipeline."""
    clear_terminal()
    print("🎬 Enhanced Brain Rot Content Generation Pipeline")
    print("=" * 60)
    
    # Initialize configuration
    print("\n📋 Loading configuration...")
    initialize_config()
    print("✅ Configuration loaded successfully!")
    
    # Check dependencies
    whisper_available = check_whisper_installation()
    
    # Get user preferences
    config = get_user_preferences(whisper_available)
    
    # Start LMStudio if needed
    if config.ai_provider == 'lmstudio' and check_lmstudio_needed():
        os.system("lms server start")
        print("✓ LMStudio server started successfully")
    
    # Execute pipeline
    try:
        if config.use_bulk_mode:
            results = run_bulk_pipeline(config)
            print_final_summary(config, results=results)
        else:
            successful_runs = run_legacy_mode(config)
            print("\nAll runs completed!")
            print(f"Successful runs: {successful_runs}/{config.num_runs}")
            print_final_summary(config, successful_runs=successful_runs)
    
    finally:
        # Stop LMStudio if it was started
        if config.ai_provider == 'lmstudio':
            print("\n✓ Stopping LMStudio server...")
            os.system("lms server stop")


if __name__ == "__main__":
    main()