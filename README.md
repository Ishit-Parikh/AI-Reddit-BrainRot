# BrainRot Content Generation Pipeline

🎬 **An automated pipeline for generating AI-powered viral-style videos with professional audio narration, background videos, and animated subtitles.**

---

## 🌟 What This Project Does

BrainRot is a comprehensive content generation pipeline that automates the entire process of creating engaging viral-style videos. The pipeline works in four main phases:

### **Phase 1: Story Generation**
- Uses AI providers (OpenAI, DeepSeek, or LMStudio) to generate creative titles and compelling stories
- Supports custom titles or AI-generated ones
- Batch processing available for generating hundreds of stories at once

### **Phase 2: Audio Narration**
- Converts generated stories into natural-sounding speech using F5-TTS
- Voice cloning capability using your own reference audio
- Produces high-quality WAV audio files for video integration

### **Phase 3: Video Creation**
- Automatically selects and combines background videos with generated audio
- Smart video selection and trimming to match audio length
- Hardware-accelerated processing (VAAPI for AMD, NVENC for NVIDIA)
- Speed optimization for perfect audio-video synchronization

### **Phase 4: Subtitle Generation (Optional)**
- **SRT Subtitles**: Standard format compatible with all video players
- **ASS Subtitles**: Viral-style animated subtitles with:
  - Random font selection
  - Color-changing text at punctuation marks
  - Timed word-level precision
  - Title inclusion options
- **Embedded Subtitles**: Burn subtitles directly into video for immediate sharing

### **Key Features:**
- 🤖 **Multi-AI Support**: Choose between OpenAI, DeepSeek, or local LMStudio
- 📦 **Batch Processing**: Process hundreds of stories with OpenAI's cost-effective batch API
- 🎙️ **Voice Cloning**: Natural-sounding narration using your reference voice using F5-tts
- 🎬 **Smart Video Handling**: Automatic background video selection and optimization
- 📝 **Professional Subtitles**: Both standard and viral-style animated formats
- ⚡ **Hardware Acceleration**: GPU support for faster video processing
- 🔧 **Plug-and-Play**: One-time setup with persistent configuration

---

## 📋 Dependencies

### **System Requirements**
- **Python**: 3.8 or higher
- **FFmpeg**: Required for video processing
- **RAM**: Minimum 8GB (16GB recommended for batch processing)
- **GPU**: Optional but recommended (AMD/NVIDIA with proper drivers)
- **Storage**: Sufficient space for videos and output files

### **Core Python Dependencies**
```
moviepy==1.0.3          # Video processing and manipulation
openai                  # OpenAI API client
lmstudio                # LMStudio local AI integration
python-dotenv           # Environment variable management
tqdm                    # Progress bars for better UX
openai-whisper          # For transcription/subtitle generation
f5-tts                  # Advanced text-to-speech synthesis
```

### **External Tools**
- **FFmpeg**: Essential for video processing and encoding
- **F5-TTS**: Advanced text-to-speech with voice cloning capabilities 

---

## 🚀 Which Dependencies to Choose and How to Install Them

### **1. Essential Setup (Required for Basic Functionality)**

#### **Install Python Dependencies**
```bash
# Install core requirements
pip install moviepy==1.0.3 openai lmstudio python-dotenv tqdm

# Or use requirements.txt if available
pip install -r requirements.txt
```

#### **Install FFmpeg**
- **Ubuntu/Debian**: `sudo apt update && sudo apt install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org) and add to PATH
- **macOS**: `brew install ffmpeg`
- **Verify installation**: `ffmpeg -version`

### **2. AI Provider Setup (Choose At Least One)**

#### **Option A: OpenAI (Recommended for Quality)**
- **Pros**: Highest quality stories, batch processing available, most reliable
- **Cons**: Costs money per API call
- **Setup**: Get API key from [platform.openai.com](https://platform.openai.com)
- **Models**: `gpt-4o-mini` (cost-effective), `gpt-4o` (premium quality)

#### **Option B: DeepSeek (Budget-Friendly)**
- **Pros**: Very cost-effective, good quality, faster than OpenAI
- **Cons**: No batch processing, newer service
- **Setup**: Get API key from [deepseek.com](https://deepseek.com)
- **Models**: `deepseek-chat` (recommended)

#### **Option C: LMStudio (Free/Local)**
- **Pros**: Completely free, runs locally, no API limits
- **Cons**: Requires powerful hardware, slower processing, setup complexity
- **Setup**: Download from [lmstudio.ai](https://lmstudio.ai)
- **Requirements**: 16GB+ RAM, decent GPU recommended
- **Models**: Any compatible model (Llama, Mistral, etc.)

### **3. Audio Processing Setup**

#### **F5-TTS Installation (Recommended)**
```bash
# Install F5-TTS for voice cloning
pip install f5-tts

# Verify installation
python -c "import f5_tts; print('F5-TTS installed successfully')"
```

#### **Prepare Audio References**
- **Reference Audio**: `ref_audio.mp3` - 12 seconds of clear speech
- **Reference Text**: `ref_txt.txt` - Exact transcript of the reference audio. (Will Automatically generate the transcription if not provided)
- **Quality Tips**: Use clear, noise-free audio for best voice cloning results

### **4. Subtitle Generation Setup (Optional)**

#### **Install Whisper for Transcription**
```bash
# Install OpenAI Whisper
pip install openai-whisper

# Verify installation
whisper --help
```

#### **Custom Fonts Setup (Optional)**
- Create a fonts directory with TTF/OTF font files
- Fonts will be randomly selected for ASS subtitle styling
- Leave empty to use system default fonts
- Change Font name to what you searched while downloading the TTF file on the internet

### **5. Complete Installation Example**
```bash

MAKE SURE TO PROPERLY INSTALL f5-tts depending on your SYSTEM

```



```bash
# 1. Clone the repository
git clone https://github.com/Ishit-Parikh/AI-Reddit-BrainRot.git
cd GenAI-BrainRot

# 2. Install all dependencies
pip install moviepy==1.0.3 openai lmstudio python-dotenv tqdm
pip install openai-whisper

# 3. Install FFmpeg (Ubuntu example)
sudo apt update && sudo apt install ffmpeg

# 4. Prepare required files
mkdir Videos                    # Background videos folder
touch System_Title_Prompt.txt   # Title generation instructions
touch Story_System_Prompt.txt   # Story generation instructions
touch ref_audio.mp3            # Reference audio for voice cloning
touch ref_txt.txt              # Transcript of reference audio

# 5. Run the pipeline
python main.py
```

### **6. Dependency Installation Tips**

#### **For Windows Users:**
```bash
# Use Command Prompt or PowerShell as Administrator
pip install --upgrade pip
pip install moviepy==1.0.3 openai lmstudio python-dotenv tqdm openai-whisper 

# Install FFmpeg using chocolatey (if available)
choco install ffmpeg
```

#### **For macOS Users:**
```bash
# Using Homebrew (recommended)
brew install python ffmpeg
pip3 install moviepy==1.0.3 openai lmstudio python-dotenv tqdm openai-whisper 
```

#### **For GPU Acceleration:**
- **NVIDIA**: Ensure CUDA drivers are installed
- **AMD**: Ensure VAAPI drivers are installed
- The pipeline automatically detects and uses hardware acceleration when available

---

## 📁 Output

### **Demo Video**
  <video width="600" controls>
    <source src="README ASSETS/gene_video.mp4" type="video/mp4">
    Your browser does not support the video tag.
  </video>

### **Generated File Structure**
Each story creates a dedicated folder with the following structure:

```
Output_Directory/
└── Story_Title_Here/
    ├── title.txt              # Generated or custom title
    ├── story.txt              # AI-generated story content
    ├── gene_audio.wav         # AI-generated audio narration
    ├── gene_video.mp4         # Final video (with embedded subtitles if selected)
    ├── subtitles.srt          # Standard subtitle file (always created)
    ├── subtitles.ass          # Animated subtitle file (if ASS option selected)
    └── speed_info.json        # Video processing metadata
```

### **File Descriptions**

#### **Text Files**
- **`title.txt`**: Contains the story title (AI-generated or user-provided)
- **`story.txt`**: The complete AI-generated story text used for narration

#### **Audio Files**
- **`gene_audio.wav`**: High-quality audio narration generated using F5-TTS
  - Format: WAV, 44.1kHz sample rate
  - Voice-cloned using your reference audio
  - Duration varies based on story length

#### **Video Files**
- **`gene_video.mp4`**: Final processed video file
  - Format: MP4 with H.264 encoding
  - Resolution: Matches source background videos
  - Audio: Synchronized with generated narration
  - Subtitles: Embedded if subtitle options were selected

#### **Subtitle Files**
- **`subtitles.srt`**: Standard subtitle format
  - Compatible with all video players
  - Always includes story title at the beginning (00:00:00 - 00:00:03)
  - Word-level timing for better readability
  
- **`subtitles.ass`**: Advanced subtitle format (if selected)
  - Viral-style animated subtitles
  - Random font selection from custom font directory
  - Color changes at punctuation marks for visual appeal
  - Optional title inclusion based on user preference

#### **Metadata Files**
- **`speed_info.json`**: Contains video processing information
  - Original video duration
  - Audio duration
  - Speed adjustment factor
  - Processing timestamps

### **Output Quality**
- **Videos**: Full HD (1080p) when possible, matches source quality
- **Audio**: 44.1kHz WAV for maximum quality
- **Subtitles**: Word-level timing precision for professional appearance

### **Storage Requirements**
- **Per Story**: Approximately 50-200MB depending on video length
- **Bulk Processing**: Plan for several GB when generating multiple stories
- **Background Videos**: Store in separate directory, reused across stories

### **File Management Tips**
- Output folders are automatically organized by story title
- Duplicate titles get numbered suffixes (Story_Title_2, Story_Title_3, etc.)
- All files can be safely moved or renamed after generation
- SRT files work with any video player for subtitle support

---

## ⚙️ First-Time Configuration

On first run, the pipeline guides you through a one-time setup wizard:

1. **Folder Paths**: Videos directory, output location
2. **System Prompts**: Instructions for AI story generation
3. **Audio References**: Voice cloning files
4. **AI Providers**: At least one API key required
5. **Optional Settings**: Custom fonts, model preferences

Configuration is saved securely and persists across runs. Use the update wizard anytime to modify settings.

---

## 🔧 Troubleshooting

### **Common Issues**
- **"No API keys configured"**: Run setup wizard, ensure at least one AI provider
- **"FFmpeg not found"**: Install FFmpeg and restart terminal
- **Audio generation fails**: Check F5-TTS installation and reference files
- **GPU acceleration disabled**: Install proper drivers, falls back to CPU automatically

### **Reset Configuration**
```bash
rm -rf ~/.brainrot_pipeline
python main.py  # Reconfigure from scratch
```

---

🎬 **Ready to create viral content? Run `python main.py` to get started!**