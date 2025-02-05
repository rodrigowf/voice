import logging
from pynput import keyboard
from ..config import Config

logger = logging.getLogger(__name__)

class KeyboardHandler:
    def __init__(self, on_start_recording=None, on_stop_recording=None):
        self.listener = None
        self.on_start_recording = on_start_recording
        self.on_stop_recording = on_stop_recording
        
    def start(self):
        """Start keyboard listener"""
        try:
            self.listener = keyboard.Listener(
                on_press=self._handle_press,
                on_release=self._handle_release
            )
            self.listener.start()
            logger.info("Keyboard listener started")
            return True
        except Exception as e:
            logger.error(f"Failed to start keyboard listener: {e}")
            return False
            
    def _handle_press(self, key):
        """Handle key press"""
        try:
            if key == keyboard.Key.f4 and self.on_start_recording:
                logger.info("Recording hotkey pressed")
                self.on_start_recording()
        except Exception as e:
            logger.error(f"Error handling key press: {e}")
            
    def _handle_release(self, key):
        """Handle key release"""
        try:
            if key == keyboard.Key.f4 and self.on_stop_recording:
                logger.info("Recording hotkey released")
                self.on_stop_recording()
        except Exception as e:
            logger.error(f"Error handling key release: {e}")
            
    def stop(self):
        """Stop keyboard listener"""
        if self.listener:
            try:
                self.listener.stop()
            except Exception as e:
                logger.error(f"Error stopping keyboard listener: {e}")
                
    def is_running(self):
        """Check if listener is running"""
        return self.listener and self.listener.running 