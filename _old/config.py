import os
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Audio Settings
    CHANNELS = 1  # Mono audio
    RATE = 16000  # Sample rate that works well with Whisper
    CHUNK = 8192  # Larger buffer size for better stability
    FORMAT = 'FLOAT32'  # Audio format
    MIN_AUDIO_LENGTH = 0.5  # Minimum audio length in seconds
    MAX_AUDIO_LENGTH = 30.0  # Maximum audio length in seconds
    SILENCE_THRESHOLD = 0.02  # Lower threshold for silence detection
    
    # Application Settings
    HOTKEY = 'f4'
    ICON_SIZE = 24  # Smaller icon size for better visibility
    ICON_COLOR_IDLE = 'green'
    ICON_COLOR_RECORDING = 'red'
    
    # Paths
    TEMP_DIR = Path(os.getenv('TEMP', tempfile.gettempdir()))
    LOG_FILE = 'voice_to_text.log'
    
    # Whisper API Settings
    WHISPER_MODEL = "whisper-1"
    WHISPER_LANGUAGE = None  # Auto-detect language
    WHISPER_RESPONSE_FORMAT = "verbose_json"  # Use verbose JSON format for better response handling
    
    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        errors = []
        
        # Check for required API key
        if not cls.OPENAI_API_KEY or cls.OPENAI_API_KEY == 'your_openai_api_key_here':
            errors.append("OPENAI_API_KEY not found in .env file or is set to default value")
        
        # Validate audio settings
        if cls.CHANNELS not in [1, 2]:
            errors.append("CHANNELS must be 1 (mono) or 2 (stereo)")
        
        if not isinstance(cls.RATE, int) or cls.RATE <= 0:
            errors.append("RATE must be a positive integer")
            
        if not isinstance(cls.CHUNK, int) or cls.CHUNK <= 0:
            errors.append("CHUNK must be a positive integer")
            
        if cls.MIN_AUDIO_LENGTH <= 0 or cls.MAX_AUDIO_LENGTH <= cls.MIN_AUDIO_LENGTH:
            errors.append("Invalid audio length settings")
            
        # Ensure temp directory exists and is writable
        try:
            if not cls.TEMP_DIR.exists():
                cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
            test_file = cls.TEMP_DIR / '.write_test'
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            errors.append(f"Temporary directory error: {e}")
            
        # Check log file permissions
        try:
            with open(cls.LOG_FILE, 'a') as f:
                pass
        except Exception as e:
            errors.append(f"Log file error: {e}")
            
        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Configuration validation failed:\n{error_msg}") 