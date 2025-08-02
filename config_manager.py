"""
config_manager.py
Configuration management system for the pipeline.
Handles first-time setup, persistent storage, and configuration updates.
"""
import os
import json
import getpass
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration file location (in user's home directory for cross-platform compatibility)
CONFIG_DIR = Path.home() / ".frbv_pipeline"
CONFIG_FILE = CONFIG_DIR / "config.json"
SECRETS_FILE = CONFIG_DIR / "secrets.json"  # Separate file for sensitive data

class ConfigManager:
    def __init__(self):
        self.config = {}
        self.secrets = {}
        self._ensure_config_dir()
        
    def _ensure_config_dir(self):
        """Create configuration directory if it doesn't exist."""
        CONFIG_DIR.mkdir(exist_ok=True)
        # Set restrictive permissions on secrets file location
        if os.name != 'nt':  # Unix-like systems
            os.chmod(CONFIG_DIR, 0o700)
    
    def is_first_run(self) -> bool:
        """Check if this is the first run (no config exists)."""
        return not CONFIG_FILE.exists() or not SECRETS_FILE.exists()
    
    def load_config(self) -> Dict[str, Any]:
        """Load existing configuration."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
        
        if SECRETS_FILE.exists():
            with open(SECRETS_FILE, 'r') as f:
                self.secrets = json.load(f)
        
        return {**self.config, **self.secrets}
    
    def save_config(self):
        """Save configuration to files."""
        # Save non-sensitive config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        # Save sensitive data separately with restricted permissions
        with open(SECRETS_FILE, 'w') as f:
            json.dump(self.secrets, f, indent=2)
        
        if os.name != 'nt':  # Unix-like systems
            os.chmod(SECRETS_FILE, 0o600)  # Read/write for owner only
    
    def setup_wizard(self):
        """Interactive setup wizard for first-time configuration."""
        print("\n" + "="*60)
        print("🎬 FRBV Pipeline Configuration Setup")
        print("="*60)
        print("\nWelcome! Let's set up your configuration for the first time.")
        print("Your settings will be saved for future runs.\n")
        
        # Paths configuration
        print("📁 PATH CONFIGURATION")
        print("-" * 40)
        
        # Videos folder
        default_videos = os.path.join(os.getcwd(), "Videos")
        videos_path = input(f"Path to background videos folder [{default_videos}]: ").strip()
        self.config['videos_path'] = videos_path or default_videos
        
        # Output folder
        default_output = os.path.join(os.path.expanduser("~"), "DaVinci Vids")
        output_path = input(f"Path to output folder [{default_output}]: ").strip()
        self.config['output_path'] = output_path or default_output
        
        # System prompts
        print("\n📝 SYSTEM PROMPTS")
        print("-" * 40)
        
        default_title_prompt = "System_Title_Prompt.txt"
        title_prompt = input(f"Path to title prompt file [{default_title_prompt}]: ").strip()
        self.config['title_prompt_path'] = title_prompt or default_title_prompt
        
        default_story_prompt = "Story_System_Prompt.txt"
        story_prompt = input(f"Path to story prompt file [{default_story_prompt}]: ").strip()
        self.config['story_prompt_path'] = story_prompt or default_story_prompt
        
        # Audio reference files
        print("\n🎵 AUDIO CONFIGURATION")
        print("-" * 40)
        
        default_ref_audio = "ref_audio.mp3"
        ref_audio = input(f"Path to reference audio file [{default_ref_audio}]: ").strip()
        self.config['ref_audio_path'] = ref_audio or default_ref_audio
        
        default_ref_text = "ref_txt.txt"
        ref_text = input(f"Path to reference text file [{default_ref_text}]: ").strip()
        self.config['ref_text_path'] = ref_text or default_ref_text
        
        # Fonts directory (optional)
        print("\n🎨 FONTS CONFIGURATION (Optional)")
        print("-" * 40)
        print("Leave blank to use default system fonts")
        
        fonts_dir = input("Path to custom fonts directory: ").strip()
        if fonts_dir:
            self.config['fonts_dir'] = fonts_dir
        
        # API Configuration
        print("\n🔑 API CONFIGURATION")
        print("-" * 40)
        
        # OpenAI
        print("\n1. OpenAI API (Primary)")
        openai_key = getpass.getpass("OpenAI API Key (hidden): ").strip()
        if openai_key:
            self.secrets['FINE_TUNED_FOR_STORIES'] = openai_key
            
            model_id = input("OpenAI Fine-tuned Model ID [gpt-4o-mini]: ").strip()
            self.config['openai_model_id'] = model_id or "gpt-4o-mini"
        
        # DeepSeek
        print("\n2. DeepSeek API (Secondary)")
        deepseek_key = getpass.getpass("DeepSeek API Key (hidden): ").strip()
        if deepseek_key:
            self.secrets['DEEPSEEK_API_KEY'] = deepseek_key
            
            model_id = input("DeepSeek Model Name [deepseek-chat]: ").strip()
            self.config['deepseek_model_name'] = model_id or "deepseek-chat"
        
        # LMStudio
        print("\n3. LMStudio (Fallback)")
        lmstudio_model = input("LMStudio Model Name: ").strip()
        if lmstudio_model:
            self.config['lmstudio_model_name'] = lmstudio_model
        
        # Save configuration
        self.save_config()
        
        print("\n✅ Configuration saved successfully!")
        print(f"   Config location: {CONFIG_FILE}")
        print(f"   Secrets location: {SECRETS_FILE}")
        
    def update_wizard(self):
        """Interactive wizard to update existing configuration."""
        print("\n" + "="*60)
        print("🔧 Update Configuration")
        print("="*60)
        
        options = [
            ("1", "Update folder paths (videos, output)"),
            ("2", "Update prompt file locations"),
            ("3", "Update API keys"),
            ("4", "Update model settings"),
            ("5", "Update audio/font settings"),
            ("6", "Remove API keys/models"),
            ("7", "View current configuration"),
            ("8", "Reset all settings"),
            ("0", "Continue with current settings")
        ]
        
        for key, desc in options:
            print(f"{key}. {desc}")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            self._update_folder_paths()
        elif choice == "2":
            self._update_prompt_files()
        elif choice == "3":
            self._update_api_keys()
        elif choice == "4":
            self._update_models()
        elif choice == "5":
            self._update_audio_fonts()
        elif choice == "6":
            self._remove_api_configs()
        elif choice == "7":
            self._view_config()
        elif choice == "8":
            if input("Are you sure you want to reset all settings? (y/n): ").lower() == 'y':
                self.setup_wizard()
        
        return choice != "0"  # Return True if user wants to update more
    
    def _update_folder_paths(self):
        """Update folder path configurations."""
        print("\n📁 Update Folder Paths (press Enter to keep current value)")
        
        current = self.config.get('videos_path', 'Not set')
        new_val = input(f"Videos path [{current}]: ").strip()
        if new_val:
            self.config['videos_path'] = new_val
        
        current = self.config.get('output_path', 'Not set')
        new_val = input(f"Output path [{current}]: ").strip()
        if new_val:
            self.config['output_path'] = new_val
        
        self.save_config()
        print("✅ Folder paths updated!")
    
    def _update_prompt_files(self):
        """Update prompt file locations."""
        print("\n📝 Update Prompt File Locations (press Enter to keep current value)")
        
        current = self.config.get('title_prompt_path', 'Not set')
        new_val = input(f"Title prompt file [{current}]: ").strip()
        if new_val:
            self.config['title_prompt_path'] = new_val
        
        current = self.config.get('story_prompt_path', 'Not set')
        new_val = input(f"Story prompt file [{current}]: ").strip()
        if new_val:
            self.config['story_prompt_path'] = new_val
        
        self.save_config()
        print("✅ Prompt file locations updated!")
    
    def _update_api_keys(self):
        """Update API keys."""
        print("\n🔑 Update API Keys (press Enter to keep current)")
        
        new_key = getpass.getpass("OpenAI API Key (hidden): ").strip()
        if new_key:
            self.secrets['FINE_TUNED_FOR_STORIES'] = new_key
        
        new_key = getpass.getpass("DeepSeek API Key (hidden): ").strip()
        if new_key:
            self.secrets['DEEPSEEK_API_KEY'] = new_key
        
        self.save_config()
        print("✅ API keys updated!")
    
    def _update_models(self):
        """Update model settings."""
        print("\n🤖 Update Model Settings (press Enter to keep current)")
        
        current = self.config.get('openai_model_id', 'Not set')
        new_val = input(f"OpenAI Model ID [{current}]: ").strip()
        if new_val:
            self.config['openai_model_id'] = new_val
        
        current = self.config.get('deepseek_model_name', 'Not set')
        new_val = input(f"DeepSeek Model Name [{current}]: ").strip()
        if new_val:
            self.config['deepseek_model_name'] = new_val
        
        current = self.config.get('lmstudio_model_name', 'Not set')
        new_val = input(f"LMStudio Model [{current}]: ").strip()
        if new_val:
            self.config['lmstudio_model_name'] = new_val
        
        self.save_config()
        print("✅ Model settings updated!")
    
    def _remove_api_configs(self):
        """Remove API keys and model configurations."""
        print("\n🗑️ Remove API Configurations")
        print("-" * 40)
        
        # Show current configurations
        providers = []
        if self.secrets.get('FINE_TUNED_FOR_STORIES'):
            providers.append(('1', 'OpenAI', 'FINE_TUNED_FOR_STORIES', 'openai_model_id'))
        if self.secrets.get('DEEPSEEK_API_KEY'):
            providers.append(('2', 'DeepSeek', 'DEEPSEEK_API_KEY', 'deepseek_model_name'))
        if self.config.get('lmstudio_model_name'):
            providers.append(('3', 'LMStudio', None, 'lmstudio_model_name'))
        
        if not providers:
            print("No API configurations to remove.")
            input("\nPress Enter to continue...")
            return
        
        print("Current configurations:")
        for num, name, _, _ in providers:
            print(f"{num}. {name}")
        print("0. Cancel")
        
        choice = input("\nSelect configuration to remove: ").strip()
        
        if choice == '0':
            return
        
        # Find selected provider
        selected = None
        for num, name, key, model in providers:
            if num == choice:
                selected = (name, key, model)
                break
        
        if not selected:
            print("Invalid selection.")
            return
        
        name, key, model = selected
        
        # Confirm removal
        if input(f"\nRemove {name} configuration? (y/n): ").lower() != 'y':
            return
        
        # Remove configuration
        if key:
            self.secrets.pop(key, None)
        if model:
            self.config.pop(model, None)
        
        # Save changes
        self.save_config()
        print(f"✅ {name} configuration removed!")
        
        # Check if at least one AI remains
        remaining = self.get_available_ai_providers()
        if not remaining:
            print("\n⚠️ WARNING: No AI providers configured!")
            print("You must configure at least one AI provider.")
            input("\nPress Enter to set up an AI provider...")
            self._quick_ai_setup()
    
    def _quick_ai_setup(self):
        """Quick setup for at least one AI provider."""
        print("\n🤖 Quick AI Provider Setup")
        print("1. OpenAI")
        print("2. DeepSeek") 
        print("3. LMStudio")
        
        choice = input("\nSelect AI provider to configure: ").strip()
        
        if choice == '1':
            key = getpass.getpass("OpenAI API Key: ").strip()
            if key:
                self.secrets['FINE_TUNED_FOR_STORIES'] = key
                model = input("Model ID [gpt-4o-mini]: ").strip()
                self.config['openai_model_id'] = model or "gpt-4o-mini"
        elif choice == '2':
            key = getpass.getpass("DeepSeek API Key: ").strip()
            if key:
                self.secrets['DEEPSEEK_API_KEY'] = key
                model = input("Model Name [deepseek-chat]: ").strip()
                self.config['deepseek_model_name'] = model or "deepseek-chat"
        elif choice == '3':
            model = input("LMStudio Model Name: ").strip()
            if model:
                self.config['lmstudio_model_name'] = model
        
        self.save_config()
        print("✅ AI provider configured!")
        """Update audio and font settings."""
        print("\n🎵 Update Audio/Font Settings (press Enter to keep current)")
        
        # Reference audio files
        print("\n📢 Reference Audio Files:")
        current = self.config.get('ref_audio_path', 'Not set')
        new_val = input(f"Reference audio file [{current}]: ").strip()
        if new_val:
            self.config['ref_audio_path'] = new_val
        
        current = self.config.get('ref_text_path', 'Not set')
        new_val = input(f"Reference text file [{current}]: ").strip()
        if new_val:
            self.config['ref_text_path'] = new_val
        
        # Fonts directory
        print("\n🎨 Font Settings:")
        current = self.config.get('fonts_dir', 'System default')
        new_val = input(f"Fonts directory [{current}]: ").strip()
        if new_val:
            self.config['fonts_dir'] = new_val
        
        self.save_config()
        print("✅ Audio/Font settings updated!")
    
    def _view_config(self):
        """Display current configuration (hiding sensitive data)."""
        print("\n📋 Current Configuration")
        print("="*50)
        
        # Organize settings by category
        print("\n📁 Paths:")
        print(f"  Videos folder: {self.config.get('videos_path', 'Not set')}")
        print(f"  Output folder: {self.config.get('output_path', 'Not set')}")
        
        print("\n📝 Prompt Files:")
        print(f"  Title prompt: {self.config.get('title_prompt_path', 'Not set')}")
        print(f"  Story prompt: {self.config.get('story_prompt_path', 'Not set')}")
        
        print("\n🎵 Audio Settings:")
        print(f"  Reference audio: {self.config.get('ref_audio_path', 'Not set')}")
        print(f"  Reference text: {self.config.get('ref_text_path', 'Not set')}")
        
        print("\n🎨 Font Settings:")
        print(f"  Fonts directory: {self.config.get('fonts_dir', 'System default')}")
        
        print("\n🤖 Model Settings:")
        print(f"  OpenAI model: {self.config.get('openai_model_id', 'Not set')}")
        print(f"  DeepSeek model: {self.config.get('deepseek_model_name', 'Not set')}")
        print(f"  LMStudio model: {self.config.get('lmstudio_model_name', 'Not set')}")
        
        print("\n🔑 API Keys:")
        for key in ['FINE_TUNED_FOR_STORIES', 'DEEPSEEK_API_KEY']:
            if key in self.secrets and self.secrets[key]:
                print(f"  {key}: [SET]")
            else:
                print(f"  {key}: [NOT SET]")
        
        input("\nPress Enter to continue...")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        # Check secrets first, then config
        return self.secrets.get(key, self.config.get(key, default))
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate that all required configuration is present."""
        missing = []
        
        # Required paths
        required_paths = {
            'videos_path': 'Videos folder path',
            'output_path': 'Output directory path', 
            'title_prompt_path': 'Title prompt file',
            'story_prompt_path': 'Story prompt file',
            'ref_audio_path': 'Reference audio file',
            'ref_text_path': 'Reference text file'
        }
        
        for path_key, description in required_paths.items():
            if not self.config.get(path_key):
                missing.append(description)
        
        # Check API configurations
        ai_configs = []
        
        # OpenAI
        if self.secrets.get('FINE_TUNED_FOR_STORIES'):
            if not self.config.get('openai_model_id'):
                missing.append("OpenAI model ID (required when API key is set)")
            else:
                ai_configs.append('openai')
        
        # DeepSeek
        if self.secrets.get('DEEPSEEK_API_KEY'):
            if not self.config.get('deepseek_model_name'):
                missing.append("DeepSeek model name (required when API key is set)")
            else:
                ai_configs.append('deepseek')
        
        # LMStudio
        if self.config.get('lmstudio_model_name'):
            ai_configs.append('lmstudio')
        
        # At least one AI must be configured
        if not ai_configs:
            missing.append("At least one AI configuration (OpenAI, DeepSeek, or LMStudio)")
        
        return len(missing) == 0, missing
    
    def get_available_ai_providers(self) -> list[str]:
        """Get list of configured AI providers."""
        providers = []
        
        if self.secrets.get('FINE_TUNED_FOR_STORIES') and self.config.get('openai_model_id'):
            providers.append('openai')
        
        if self.secrets.get('DEEPSEEK_API_KEY') and self.config.get('deepseek_model_name'):
            providers.append('deepseek')
            
        if self.config.get('lmstudio_model_name'):
            providers.append('lmstudio')
            
        return providers
    
    def select_ai_provider(self) -> tuple[str, bool]:
        """
        Let user select which AI provider to use.
        Returns: (provider_name, use_batch_api)
        """
        providers = self.get_available_ai_providers()
        
        if not providers:
            raise ValueError("No AI providers configured")
        
        if len(providers) == 1:
            # Only one provider, use it
            provider = providers[0]
            use_batch = False
            
            if provider == 'openai':
                print("\n🤖 Using OpenAI API")
                batch_choice = input("Use batch processing? (can take up to 24 hours but more cost-effective) (y/n): ").lower()
                use_batch = batch_choice == 'y'
                
            return provider, use_batch
        
        # Multiple providers available
        print("\n🤖 Multiple AI providers available:")
        provider_names = {
            'openai': 'OpenAI API',
            'deepseek': 'DeepSeek API',
            'lmstudio': 'LMStudio (Local)'
        }
        
        for i, provider in enumerate(providers, 1):
            print(f"{i}. {provider_names.get(provider, provider)}")
        
        while True:
            try:
                choice = int(input("\nSelect AI provider (number): "))
                if 1 <= choice <= len(providers):
                    provider = providers[choice - 1]
                    use_batch = False
                    
                    if provider == 'openai':
                        print("\n📋 OpenAI Processing Options:")
                        print("1. Sequential API calls (faster for small batches)")
                        print("2. Batch API calls (cost-effective but can take up to 24 hours)")
                        
                        api_choice = input("\nChoose processing method (1 or 2): ").strip()
                        if api_choice == '2':
                            use_batch = True
                            print("\n⚠️ WARNING: Batch processing can take up to 24 HOURS!")
                            print("   Results will be saved when complete.")
                    
                    return provider, use_batch
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a number.")


# Singleton instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get the singleton ConfigManager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def initialize_config() -> Dict[str, Any]:
    """Initialize configuration on program start."""
    manager = get_config_manager()
    
    if manager.is_first_run():
        manager.setup_wizard()
    else:
        # Load existing config
        manager.load_config()
        
        # Check if user wants to update
        print("\n🎬 FRBV Pipeline")
        print("Configuration loaded from previous run.")
        
        update = input("\nWould you like to update settings? (y/n) [n]: ").strip().lower()
        if update == 'y':
            while manager.update_wizard():
                pass  # Keep updating until user chooses to continue
    
    # Validate configuration
    valid, missing = manager.validate_config()
    if not valid:
        print(f"\n⚠️ Missing required configuration: {', '.join(missing)}")
        print("Please complete the setup.")
        manager.setup_wizard()
    
    return manager.load_config()

# Convenience function to get config values
def get_config(key: str, default: Any = None) -> Any:
    """Get a configuration value."""
    return get_config_manager().get(key, default)