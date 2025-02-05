import os
import time
import logging
import threading
from pathlib import Path
from datetime import datetime
from .audio.recorder import AudioRecorder
from .audio.transcriber import Transcriber
from .ui.tray_icon import TrayIcon
from .ui.keyboard_handler import KeyboardHandler
from .ui.text_output import TextOutput
from .config import Config

logger = logging.getLogger(__name__)

class VoiceToTextApp:
    def __init__(self):
        """Initialize the Voice to Text application"""
        try:
            # Validate configuration
            Config.validate()
            
            # Initialize components
            self.recorder = AudioRecorder()
            self.transcriber = Transcriber()
            self.tray_icon = TrayIcon(on_exit=self.quit_application)
            self.keyboard_handler = KeyboardHandler(
                on_start_recording=self.start_recording,
                on_stop_recording=self.stop_recording
            )
            
            # Initialize state
            self.is_recording = False
            self.recording_thread = None
            
            logger.info("Application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise
            
    def start_recording(self):
        """Start audio recording"""
        if self.is_recording:
            return
            
        try:
            if self.recorder.start():
                self.is_recording = True
                self.tray_icon.set_recording_state(True)
                self.recording_thread = threading.Thread(target=self._record_audio)
                self.recording_thread.daemon = True
                self.recording_thread.start()
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            
    def stop_recording(self):
        """Stop audio recording and process the audio"""
        if not self.is_recording:
            return
            
        try:
            self.is_recording = False
            self.recorder.stop()
            self.tray_icon.set_recording_state(False)
            
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=1.0)
                
            self._process_recording()
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            
    def _record_audio(self):
        """Record audio in a separate thread"""
        while self.is_recording:
            try:
                if not self.recorder.record_chunk():
                    break
            except Exception as e:
                logger.error(f"Error during recording: {e}")
                break
                
    def _process_recording(self):
        """Process recorded audio and output transcription"""
        try:
            # Create temporary file
            temp_file = Config.TEMP_DIR / f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            
            # Save recording
            if self.recorder.save_recording(temp_file):
                # Transcribe audio
                text = self.transcriber.transcribe(temp_file)
                if text:
                    # Output text
                    TextOutput.write_text(text)
                    
            # Clean up
            if temp_file.exists():
                temp_file.unlink()
                
        except Exception as e:
            logger.error(f"Failed to process recording: {e}")
            
    def run(self):
        """Run the application"""
        try:
            # Setup UI components
            if not self.tray_icon.setup():
                raise RuntimeError("Failed to setup system tray icon")
                
            if not self.keyboard_handler.start():
                raise RuntimeError("Failed to start keyboard handler")
                
            logger.info("\nVoice-to-Text application started")
            logger.info("Hold F4 to record, release to transcribe")
            logger.info("Check the system tray for the application icon")
            logger.info("Press Ctrl+C to exit\n")
            
            # Keep the main thread running
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.quit_application()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.quit_application()
            
    def quit_application(self):
        """Clean up and quit the application"""
        logger.info("Shutting down application...")
        
        # Stop recording if active
        if self.is_recording:
            self.stop_recording()
            
        # Clean up components
        self.recorder.cleanup()
        self.keyboard_handler.stop()
        self.tray_icon.cleanup()
        
        logger.info("Application shutdown complete")
        os._exit(0)  # Force exit to clean up all threads 