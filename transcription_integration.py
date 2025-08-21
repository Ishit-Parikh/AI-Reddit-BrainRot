"""
transcription_integration.py
Enhanced transcription module with option to include title in subtitles.
Uses configuration management for fonts directory.
FIXED: Title handling, file generation, and user choice handling
"""
import whisper
import os
import subprocess
import traceback
import random
from config_manager import get_config

def choose_random_font(fonts_dir=None):
    """
    Randomly selects and returns the FONT NAME from the configured fonts folder.
    """
    if not fonts_dir:
        fonts_dir = get_config("fonts_dir")
    
    if not fonts_dir or not os.path.exists(fonts_dir):
        print("⚠️ No custom fonts directory configured, using Arial")
        return "Arial"
    
    fonts = [f for f in os.listdir(fonts_dir) if os.path.isfile(os.path.join(fonts_dir, f))]
    
    if not fonts:
        print("⚠️ No font files found in configured directory.")
        return "Arial"
    
    chosen_file = random.choice(fonts)
    # Extract font name (without extension)
    font_name = os.path.splitext(chosen_file)[0]
    print(f"🎨 Random font selected: {font_name}")
    return font_name

def ends_with_punctuation(text):
    """Check if text ends with punctuation marks."""
    punctuation_marks = ['.', '!', '?', ';', ':']
    return any(text.rstrip().endswith(mark) for mark in punctuation_marks)



def format_time_ass(seconds):
    """Convert seconds to ASS time format (H:MM:SS.CC)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds * 100) % 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,ms)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds * 1000) % 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def read_title_from_folder(output_folder: str) -> str:
    """Read the title from title.txt file in the output folder."""
    title_file = os.path.join(output_folder, "title.txt")
    if os.path.exists(title_file):
        try:
            with open(title_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"⚠️ Could not read title file: {e}")
    return None

def transcribe_video_to_srt(video_file_path: str, output_folder: str, model_size: str = "small") -> dict:
    """
    Transcribe video file and create SRT subtitle file only.
    SRT always includes title.
    
    Args:
        video_file_path (str): Path to the final video file to transcribe.
        output_folder (str): Directory where subtitle files will be saved.
        model_size (str): Whisper model size ("tiny", "base", "small", "medium", "large").
    
    Returns:
        dict: Paths to generated files and metadata.
    """
    try:
        print(f"🎤 Starting video transcription with Whisper ({model_size} model)...")
        
        # Read title from the output folder
        title = read_title_from_folder(output_folder)
        if title:
            print(f"📝 Found title: {title}")
        else:
            print("⚠️ No title found in folder")

        # Load the Whisper model
        print("Loading Whisper model...")
        model = whisper.load_model(model_size)

        # Perform transcription with word-level timestamps
        print("Transcribing video (this may take a moment)...")
        result = model.transcribe(
            video_file_path,
            language="en",
            word_timestamps=True,
            verbose=False
        )

        transcribed_text = result.get("text", "")
        segments = result.get("segments", [])
        
        if not transcribed_text:
            print("❌ No text was transcribed from the video!")
            return {'success': False, 'error': 'No transcription text'}
        
        print(f"✅ Transcription complete. Text length: {len(transcribed_text)} characters")
        print(f"   Found {len(segments)} segments")

        # Create SRT file path
        srt_file = os.path.join(output_folder, "subtitles.srt")

        # Generate SRT file
        print("Creating SRT subtitle file...")
        with open(srt_file, "w", encoding="utf-8") as f:
            subtitle_index = 1
            
            # Always add title to SRT
            if title:
                f.write(f"{subtitle_index}\n")
                f.write("00:00:00,000 --> 00:00:03,000\n")
                f.write(f"{title}\n\n")
                subtitle_index += 1
                print("  - Title added to SRT")
            
            # Process segments
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
                    start_time = segment.get("start", 0)
                    end_time = segment.get("end", 0)
                    text = segment.get("text", "").strip()
                    
                    if not text:
                        continue

                    start_time_srt = _seconds_to_srt_time(start_time)
                    end_time_srt = _seconds_to_srt_time(end_time)
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{start_time_srt} --> {end_time_srt}\n")
                    f.write(f"{text}\n\n")
                    subtitle_index += 1

        # Verify file was written
        if os.path.exists(srt_file):
            file_size = os.path.getsize(srt_file)
            print(f"✅ SRT file created successfully: {os.path.basename(srt_file)} ({file_size} bytes)")
            if file_size == 0:
                print("⚠️ Warning: SRT file is empty!")
                return {'success': False, 'error': 'SRT file is empty'}
        else:
            print("❌ Failed to create SRT file!")
            return {'success': False, 'error': 'SRT file not created'}

        return {
            'srt_file': srt_file,
            'title': title,
            'transcribed_text': transcribed_text,
            'success': True
        }

    except Exception as e:
        print(f"❌ Video transcription failed: {e}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def transcribe_video_to_ass(video_file_path: str, output_folder: str, include_title: bool = False, model_size: str = "small") -> dict:
    """
    Transcribe video file and create ASS subtitle file with viral styling.
    
    Args:
        video_file_path (str): Path to the final video file to transcribe.
        output_folder (str): Directory where subtitle files will be saved.
        include_title (bool): Whether to include the story title in ASS file.
        model_size (str): Whisper model size ("tiny", "base", "small", "medium", "large").
    
    Returns:
        dict: Paths to generated files and metadata.
    """
    try:
        print(f"🎤 Starting video transcription with Whisper ({model_size} model)...")
        
        # Read title from the output folder
        title = read_title_from_folder(output_folder)
        if title:
            print(f"📝 Found title: {title}")
        else:
            print("⚠️ No title found in folder")

        # Choose random font for ASS styling
        chosen_font = choose_random_font()
        
        # Available color styles
        color_styles = ["Yellow", "Red", "White", "Blue", "Orange", "Green"]
        current_color_index = 0

        # Load the Whisper model
        print("Loading Whisper model...")
        model = whisper.load_model(model_size)

        # Perform transcription with word-level timestamps
        print("Transcribing video (this may take a moment)...")
        result = model.transcribe(
            video_file_path,
            language="en",
            word_timestamps=True,
            verbose=False
        )

        transcribed_text = result.get("text", "")
        segments = result.get("segments", [])
        
        if not transcribed_text:
            print("❌ No text was transcribed from the video!")
            return {'success': False, 'error': 'No transcription text'}
        
        print(f"✅ Transcription complete. Text length: {len(transcribed_text)} characters")
        print(f"   Found {len(segments)} segments")

        # Create ASS file path
        ass_file = os.path.join(output_folder, "subtitles.ass")

        # Generate ASS file with viral styling
        print("Creating ASS subtitle file with viral styling...")
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
                "Blue": "&H00FFBF00",
                "Orange": "&H000080FF",
                "Green": "&H0000FF00",
                "Title": "&H00FFFF00"  # Special style for title
            }
            for name, color in styles.items():
                if name == "Title":
                    # Larger font size for title
                    f.write(f"Style: {name},{chosen_font},16,{color},&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,2,5,10,10,10,1\n")
                else:
                    f.write(f"Style: {name},{chosen_font},12,{color},&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,1,1,5,10,10,10,1\n")
            f.write("\n")
            
            # Events section
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            # Add title to ASS only if requested
            if title and include_title:
                # Display title for first 3 seconds
                f.write(f"Dialogue: 0,0:00:00.00,0:00:03.00,Title,,0,0,0,,{title}\n")
                print("  - Title added to ASS")
            
            # Process segments for ASS with color changes at punctuation
            found_first_sentence_end = include_title  # If including title, we don't need to skip
            
            for segment in segments:
                if "words" in segment and segment["words"]:
                    words = segment["words"]
                    i = 0
                    
                    while i < len(words):
                        current_word = words[i]["word"].strip()
                        start_time = words[i]["start"]
                        end_time = words[i]["end"]
                        
                        # Check if we've found the first sentence-ending punctuation (skip first sentence)
                        if not found_first_sentence_end:
                            if ends_with_punctuation(current_word):
                                found_first_sentence_end = True
                            i += 1
                            continue  # Skip words until we find first sentence end
                        
                        # Combine short words with next word for better readability
                        combined_text = current_word
                        if len(current_word) <= 3 and i + 1 < len(words):
                            combined_text += ' ' + words[i + 1]["word"].strip()
                            end_time = words[i + 1]["end"]
                            i += 2
                        else:
                            i += 1
                        
                        # Write this word/phrase with current color
                        start_time_ass = format_time_ass(start_time)
                        end_time_ass = format_time_ass(end_time)
                        f.write(f"Dialogue: 0,{start_time_ass},{end_time_ass},{color_styles[current_color_index]},,0,0,0,,{combined_text}\n")
                        
                        # Check if this word/phrase ends with punctuation - if so, change color for next word
                        if ends_with_punctuation(combined_text):
                            current_color_index = (current_color_index + 1) % len(color_styles)
                else:
                    # Fallback to segment-level timestamps
                    if not found_first_sentence_end:
                        if ends_with_punctuation(segment.get("text", "").strip()):
                            found_first_sentence_end = True
                        continue  # Skip this segment
                    
                    # Write segment with current color
                    text = segment.get("text", "").strip()
                    if text:
                        start_time_ass = format_time_ass(segment.get("start", 0))
                        end_time_ass = format_time_ass(segment.get("end", 0))
                        f.write(f"Dialogue: 0,{start_time_ass},{end_time_ass},{color_styles[current_color_index]},,0,0,0,,{text}\n")
                        
                        # Change color if segment ends with punctuation
                        if ends_with_punctuation(text):
                            current_color_index = (current_color_index + 1) % len(color_styles)

        # Verify file was written
        if os.path.exists(ass_file):
            file_size = os.path.getsize(ass_file)
            print(f"✅ ASS file created successfully: {os.path.basename(ass_file)} ({file_size} bytes)")
            print(f"  🎨 Using font: {chosen_font}")
            if file_size == 0:
                print("⚠️ Warning: ASS file is empty!")
                return {'success': False, 'error': 'ASS file is empty'}
        else:
            print("❌ Failed to create ASS file!")
            return {'success': False, 'error': 'ASS file not created'}

        return {
            'ass_file': ass_file,
            'font_used': chosen_font,
            'title_in_ass': include_title and title is not None,
            'title': title,
            'transcribed_text': transcribed_text,
            'success': True
        }

    except Exception as e:
        print(f"❌ Video transcription failed: {e}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def create_video_with_embedded_subtitles(video_path: str, subtitle_path: str, output_folder: str, use_ass: bool = True) -> str:
    """
    Create a new video with embedded subtitles using FFmpeg.
    Supports both ASS (with styling) and SRT (basic) subtitle formats.
    """
    try:
        output_path = os.path.join(output_folder, "final_output_with_subtitles.mp4")
        
        # Get fonts directory from config
        fonts_dir = get_config("fonts_dir")

        if use_ass and subtitle_path.endswith('.ass') and fonts_dir:
            # FFmpeg command for ASS subtitles with font directory
            escaped_subtitle_path = subtitle_path.replace('\\', '/').replace(':', '\\:')
            escaped_fonts_dir = fonts_dir.replace('\\', '/').replace(':', '\\:')
            
            ffmpeg_command = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles='{escaped_subtitle_path}':fontsdir='{escaped_fonts_dir}'",
                '-c:a', 'copy',
                '-y', output_path
            ]
            print("🎬 Adding styled ASS subtitles to video...")
        else:
            # FFmpeg command for SRT subtitles or ASS without custom fonts
            escaped_subtitle_path = subtitle_path.replace('\\', '/').replace(':', '\\:')
            ffmpeg_command = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles='{escaped_subtitle_path}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,BorderStyle=3,Shadow=1'",
                '-c:a', 'copy',
                '-y', output_path
            ]
            print("🎬 Adding subtitles to video...")

        result = subprocess.run(
            ffmpeg_command,
            capture_output=True,
            text=True,
            timeout=300,
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

def process_transcription_for_story(output_folder: str, create_subtitled_video: bool = False, 
                                   use_ass: bool = False, include_title_in_ass: bool = False) -> dict:
    """
    Process transcription for a single story.
    Creates only the requested subtitle format (SRT or ASS).
    """
    results = {'ass_file': None, 'srt_file': None, 'subtitled_video': None, 'success': False}
    
    # Use final video file for transcription
    video_file = os.path.join(output_folder, "gene_video.mp4")
    
    if not os.path.exists(video_file):
        print(f"❌ Video file not found: {video_file}")
        return results

    # Generate subtitles based on user choice
    if use_ass:
        # User wants ASS format (choice 3)
        print("📝 Generating ASS subtitles with viral styling...")
        transcription_result = transcribe_video_to_ass(video_file, output_folder, include_title_in_ass)
        
        if transcription_result['success']:
            results['ass_file'] = transcription_result['ass_file']
            results['success'] = True
            
            # Also generate SRT for compatibility
            print("📝 Also generating SRT for compatibility...")
            srt_result = transcribe_video_to_srt(video_file, output_folder)
            if srt_result['success']:
                results['srt_file'] = srt_result['srt_file']
    else:
        # User wants SRT format only (choices 1 or 2)
        print("📝 Generating SRT subtitles...")
        transcription_result = transcribe_video_to_srt(video_file, output_folder)
        
        if transcription_result['success']:
            results['srt_file'] = transcription_result['srt_file']
            results['success'] = True

    if not results['success']:
        print(f"❌ Transcription failed: {transcription_result.get('error', 'Unknown error')}")
        return results

    # Optionally create video with embedded subtitles
    if create_subtitled_video and results['success']:
        # Choose subtitle file based on user preference
        if use_ass and results['ass_file']:
            subtitle_file = results['ass_file']
            print("🎬 Embedding ASS subtitles into video...")
        elif results['srt_file']:
            subtitle_file = results['srt_file']
            print("🎬 Embedding SRT subtitles into video...")
        else:
            print("❌ No subtitle file available for embedding")
            return results
        
        subtitled_video = create_video_with_embedded_subtitles(
            video_file, subtitle_file, output_folder, use_ass
        )
        
        if subtitled_video and os.path.exists(subtitled_video):
            # Delete the original gene_video.mp4
            if os.path.exists(video_file):
                os.remove(video_file)
                print(f"🗑️ Removed original video: {os.path.basename(video_file)}")
            
            # Rename subtitled video to gene_video.mp4
            final_video_path = os.path.join(output_folder, "gene_video.mp4")
            os.rename(subtitled_video, final_video_path)
            print(f"✅ Final video renamed to: gene_video.mp4 (with embedded subtitles)")
            results['subtitled_video'] = final_video_path
    
    return results

def process_transcription_bulk(stories_data: list, create_subtitled_videos: bool = False, 
                              use_ass: bool = False, include_title_in_ass: bool = False) -> list:
    """
    Process transcription for multiple stories in bulk.
    Creates only the requested subtitle format for each story.
    """
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear terminal
    print(f"{'='*50}")
    print("🎤 BULK TRANSCRIPTION PHASE")
    print(f"Processing transcription for {len(stories_data)} stories...")
    
    if use_ass:
        print("🎨 ASS files will be created with viral-style")
        if include_title_in_ass:
            print("📝 Titles will be included in ASS files")
        else:
            print("📝 Titles will NOT be included in ASS files")
        print("📺 SRT files will also be created for compatibility")
    else:
        print("📺 SRT files will be created")
        print("📝 Titles will always be included in SRT files")
    
    if create_subtitled_videos:
        print("🎬 Videos with embedded subtitles will be created")
    print(f"{'='*50}")

    successful_transcriptions = []
    for i, (title, story, output_folder) in enumerate(stories_data, 1):
        print(f"\n🎙️ Processing transcription {i}/{len(stories_data)}: {title}")
        print("-" * 40)
        try:
            transcription_results = process_transcription_for_story(
                output_folder, create_subtitled_videos, use_ass, include_title_in_ass
            )
            if transcription_results['success']:
                successful_transcriptions.append((title, story, output_folder, transcription_results))
                print(f"✅ Transcription {i} completed: {title}")
                
                if transcription_results['srt_file']:
                    print(f"  📺 SRT subtitles: subtitles.srt (with title)")
                if transcription_results['ass_file']:
                    print(f"  🎨 ASS subtitles: subtitles.ass")
                if transcription_results['subtitled_video']:
                    print(f"  🎬 Final video: gene_video.mp4 (with embedded subtitles)")
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

def add_transcription_to_single_story_pipeline(output_folder: str, create_subtitled_video: bool = True, 
                                              use_ass: bool = False, include_title_in_ass: bool = False):
    """
    Add transcription step to the single story pipeline.
    Creates only the requested subtitle format.
    """
    print("\n🎤 Adding transcription to pipeline...")
    transcription_results = process_transcription_for_story(
        output_folder, create_subtitled_video, use_ass, include_title_in_ass
    )
    
    if transcription_results['success']:
        print("✅ Transcription step completed successfully!")
        
        if transcription_results.get('srt_file'):
            print("📺 Created SRT subtitles (with title)")
        if transcription_results.get('ass_file'):
            print("🎨 Created ASS subtitles with random font and alternating colors")
            if include_title_in_ass:
                print("   - Title included in ASS")
            else:
                print("   - Title NOT included in ASS")
        
        if transcription_results.get('subtitled_video'):
            print("🎬 Created video with embedded subtitles")
    else:
        print("❌ Transcription step failed!")
    
    return transcription_results