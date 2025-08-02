# FRBV Content Generation Pipeline

🎬 An automated pipeline for generating AI-powered stories with audio narration, video backgrounds, and professional subtitles.

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [AI Provider Setup](#ai-provider-setup)
- [Usage](#usage)
- [Batch Processing](#batch-processing)
- [Output Structure](#output-structure)
- [Troubleshooting](#troubleshooting)

## 🌟 Overview

FRBV (Fast Reddit Background Videos) is a comprehensive content generation pipeline that automates the entire process of creating viral-style videos. It generates stories using AI, converts them to speech, combines them with background videos, and adds professional subtitles.

### Key Features:
- 🤖 **Multiple AI Provider Support**: OpenAI, DeepSeek, and LMStudio
- 📦 **Batch Processing**: Process hundreds of stories with OpenAI's batch API (up to 24 hours)
- 🎙️ **Voice Cloning**: Uses F5-TTS for natural-sounding narration
- 🎬 **Smart Video Selection**: Intelligently selects and combines background videos
- 📝 **Professional Subtitles**: Both SRT and ASS formats with viral-style animations
- ⚡ **Hardware Acceleration**: Supports VAAPI (AMD) and NVENC (NVIDIA)
- 🔧 **Plug-and-Play**: One-time configuration that persists across runs

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- FFmpeg installed and in PATH
- At least 8GB RAM
- GPU recommended for video processing (AMD/NVIDIA)

### Python Dependencies
```bash
moviepy==1.0.3
lmstudio
openai
openai-whisper
python-dotenv
```

### External Tools
- **F5-TTS**: For voice synthesis
  ```bash
  pip install f5-tts
  ```
- **FFmpeg**: For video processing
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org)
  - macOS: `brew install ffmpeg`

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/frbv-pipeline.git
   cd frbv-pipeline
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install F5-TTS for voice synthesis**
   ```bash
   pip install f5-tts
   ```

4. **Prepare required files**
   - Create `System_Title_Prompt.txt` - Instructions for title generation
   - Create `Story_System_Prompt.txt` - Instructions for story generation
   - Add `ref_audio.mp3` - Reference audio for voice cloning
   - Add `ref_txt.txt` - Text transcript of reference audio
   - Create `Videos/` folder with background videos

## ⚙️ Configuration

### First-Time Setup

The pipeline uses a configuration wizard on first run. Configuration is saved in:
- `~/.frbv_pipeline/config.json` - Non-sensitive settings
- `~/.frbv_pipeline/secrets.json` - API keys (encrypted permissions)

### Required Configuration Fields

| Field | Description | Example |
|-------|-------------|---------|
| **videos_path** | Folder containing background videos | `/home/user/Videos` |
| **output_path** | Where to save generated content | `/home/user/DaVinci Vids` |
| **title_prompt_path** | System prompt for titles | `System_Title_Prompt.txt` |
| **story_prompt_path** | System prompt for stories | `Story_System_Prompt.txt` |
| **ref_audio_path** | Reference audio for voice cloning | `ref_audio.mp3` |
| **ref_text_path** | Reference text file | `ref_txt.txt` |

### Optional Configuration Fields

| Field | Description | Required When |
|-------|-------------|---------------|
| **fonts_dir** | Custom fonts for subtitles | Using ASS subtitles |
| **openai_model_id** | OpenAI model name | OpenAI API key is set |
| **deepseek_model_name** | DeepSeek model | DeepSeek API key is set |
| **lmstudio_model_name** | LMStudio model | Using LMStudio |

### AI Provider Requirements

**At least ONE AI provider must be configured:**

1. **OpenAI**
   - API Key: `FINE_TUNED_FOR_STORIES`
   - Model ID: `openai_model_id`

2. **DeepSeek**
   - API Key: `DEEPSEEK_API_KEY`

3. **LMStudio**
   - Model Name: `lmstudio_model_name`

## 🤖 AI Provider Setup

### OpenAI Setup
1. Get API key from [platform.openai.com](https://platform.openai.com)
2. Enter key during configuration
3. Choose between:
   - **Sequential API**: Faster for small batches
   - **Batch API**: Cost-effective for large batches (up to 24 hours)

### DeepSeek Setup
1. Get API key from [deepseek.com](https://deepseek.com)
2. Enter key during configuration
3. Uses sequential processing only

### LMStudio Setup
1. Download LMStudio from [lmstudio.ai](https://lmstudio.ai)
2. Download a compatible model
3. Enter model name during configuration
4. The pipeline auto-starts/stops the server

## 📖 Usage

### Basic Usage

```bash
python main.py
```

The pipeline will:
1. Load saved configuration (or run setup wizard)
2. Let you select AI provider (if multiple configured)
3. Ask for number of stories
4. Process stories → audio → video → subtitles

### Processing Modes

1. **Bulk Mode** (Recommended for multiple stories)
   - Generates all stories first
   - Then processes all audio
   - Then creates all videos
   - Finally adds subtitles
   - More efficient resource usage

2. **Legacy Mode** (One story at a time)
   - Completes each story fully before starting next
   - Good for testing single stories

### Transcription Options

1. **SRT Only**: Basic subtitles
2. **SRT + Embedded**: Subtitles burned into video
3. **ASS + Embedded**: Viral-style animated subtitles
4. **Skip**: No subtitles

### Title Options

- **Custom Titles**: Provide your own titles
- **AI Generated**: Let the AI create titles
- **Title in Subtitles**: Choose whether to include title in ASS files

## ⚡ Batch Processing

### OpenAI Batch API

When using OpenAI with batch processing:

```
⚠️ WARNING: Batch processing can take up to 24 HOURS!
   However, it's more cost-effective for large batches.
   You can close this program and results will be saved.
```

### How Batch Processing Works

1. **Phase 1**: Generate all titles (if needed)
2. **Phase 2**: Generate all stories based on titles
3. **Automatic polling**: Checks status every 60 seconds
4. **Persistent state**: Can resume if interrupted

### Batch Processing Benefits
- 50% cost reduction compared to sequential
- Process hundreds of stories in one batch
- Automatic retry on failures
- Progress tracking

## 📁 Output Structure

Each generated story creates a folder with:

```
Story_Title/
├── title.txt          # Story title
├── story.txt          # Generated story text
├── gene_audio.wav     # AI-generated narration
├── gene_video.mp4     # Final video with/without subtitles
├── subtitles.srt      # Standard subtitles (always created)
├── subtitles.ass      # Viral-style subtitles (if selected)
└── speed_info.json    # Video speed information
```

## 🔧 Troubleshooting

### Common Issues

1. **"No API keys configured"**
   - Run configuration setup
   - Ensure at least one AI provider is configured

2. **"FFmpeg not found"**
   - Install FFmpeg and add to PATH
   - Restart terminal after installation

3. **"VAAPI/NVENC failed"**
   - Falls back to CPU encoding automatically
   - Check GPU drivers are installed

4. **Batch processing stuck**
   - Check job ID in console
   - Can take up to 24 hours
   - Program can be safely closed and restarted

### Configuration Reset

To reset all settings:
```bash
rm -rf ~/.frbv_pipeline
```

Then run the program to reconfigure.

## 🎥 Video Organization Tips

### Flat Structure
```
Videos/
├── video1.mp4
├── video2.mp4
└── video3.mp4
```

### Organized Structure (Recommended)
```
Videos/
├── Nature/
│   ├── forest.mp4
│   └── ocean.mp4
├── City/
│   ├── tokyo.mp4
│   └── nyc.mp4
└── Abstract/
    ├── particles.mp4
    └── fractals.mp4
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Reporting Issues

Please report bugs and issues on the GitHub repository with:
- Error messages
- Configuration details (without API keys)
- Steps to reproduce
- System information