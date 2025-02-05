import logging
from pathlib import Path
from openai import OpenAI
from ..config import Config

logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
    def transcribe(self, audio_file_path: Path) -> str:
        """Transcribe audio file using Whisper API"""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=Config.WHISPER_MODEL,
                    file=audio_file,
                    response_format=Config.WHISPER_RESPONSE_FORMAT,
                    language=Config.CURRENT_LANGUAGE,
                    prompt="Hello, please transcribe carefully."
                )
                
                # Extract text from response based on format
                if transcript and hasattr(transcript, 'text'):
                    text = transcript.text
                elif isinstance(transcript, dict) and 'text' in transcript:
                    text = transcript['text']
                elif isinstance(transcript, str):
                    text = transcript
                else:
                    logger.warning("Unexpected response format from Whisper API")
                    return ""
                    
                if text.strip():
                    logger.info(f"Transcription received: {text[:50]}...")
                    return text
                else:
                    logger.warning("Empty transcription received from Whisper API")
                    return ""
                    
        except Exception as e:
            logger.error(f"Whisper API error: {e}")
            logger.error(f"Response type: {type(transcript) if 'transcript' in locals() else 'N/A'}")
            logger.error(f"Response content: {transcript if 'transcript' in locals() else 'N/A'}")
            return "" 