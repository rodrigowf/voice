import logging
import pyautogui
import time

logger = logging.getLogger(__name__)

class TextOutput:
    @staticmethod
    def write_text(text: str):
        """Write text to current cursor position"""
        try:
            if not text or not text.strip():
                logger.warning("Empty text received, nothing to write")
                return False
                
            # Add a small delay to ensure the system is ready
            time.sleep(0.1)
            
            # Write text with error handling
            try:
                logger.debug(f"Writing text: {text[:50]}...")
                pyautogui.write(text)
                logger.info("Text written successfully")
                return True
            except pyautogui.FailSafeException:
                logger.error("FailSafe triggered while writing text")
                return False
                
        except Exception as e:
            logger.error(f"Failed to write text: {e}")
            return False 