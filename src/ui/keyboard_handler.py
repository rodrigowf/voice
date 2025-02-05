import logging
from pynput import keyboard
import subprocess
import re
from ..config import Config

logger = logging.getLogger(__name__)

class VolumeController:
    def __init__(self, target_volume):
        self.target_volume = target_volume
        self.original_volume = None
        logger.debug(f"VolumeController initialized with target volume: {self.target_volume}%")
        self._test_volume_control()
    
    def _test_volume_control(self):
        """Test volume control at initialization"""
        try:
            current_volume = self.get_current_volume()
            logger.info(f"Initial volume check: {current_volume}%")
            if current_volume is None:
                logger.error("Volume control may not be working properly")
        except Exception as e:
            logger.error(f"Error during initial volume check: {str(e)}", exc_info=True)
    
    def get_current_volume(self):
        """Get current system volume percentage"""
        try:
            logger.debug("Attempting to get current volume...")
            result = subprocess.run(
                ['amixer', 'sget', 'Master'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"amixer output: {result.stdout}")
            
            match = re.search(r'\[(\d+)%\].*\[(on|off)\]', result.stdout)
            if match:
                volume = int(match.group(1))
                is_muted = match.group(2) == 'off'
                logger.debug(f"Current volume: {volume}%, Muted: {is_muted}")
                return 0 if is_muted else volume
            
            logger.warning(f"Could not parse volume information from amixer output")
            return None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"amixer command failed: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Failed to get current volume: {str(e)}", exc_info=True)
            return None
    
    def set_volume(self, volume_percentage):
        """Set system volume percentage"""
        try:
            logger.debug(f"Attempting to set volume to {volume_percentage}%")
            
            # First unmute
            unmute_cmd = ['amixer', '-q', 'set', 'Master', 'unmute']
            subprocess.run(unmute_cmd, check=True)
            
            # Then set volume
            set_cmd = ['amixer', '-q', 'set', 'Master', f'{volume_percentage}%']
            subprocess.run(set_cmd, check=True)
            
            # Verify the change
            new_volume = self.get_current_volume()
            if new_volume is not None:
                logger.info(f"Volume change result - Target: {volume_percentage}%, Actual: {new_volume}%")
                if abs(new_volume - volume_percentage) <= 5:  # Allow small difference
                    logger.info("Volume set successfully")
                    return True
                else:
                    logger.warning(f"Volume not set correctly. Difference: {abs(new_volume - volume_percentage)}%")
                    return False
            logger.error("Could not verify volume change")
            return False
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set volume: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error setting volume: {str(e)}", exc_info=True)
            return False
    
    def store_current_volume(self):
        """Store current volume if higher than target"""
        if self.original_volume is None:
            logger.debug("Getting current volume for adjustment")
            current_volume = self.get_current_volume()
            if current_volume is not None:
                logger.debug(f"Current volume: {current_volume}%, Target: {self.target_volume}%")
                if current_volume > self.target_volume:
                    self.original_volume = current_volume
                    logger.info(f"Storing original volume: {self.original_volume}%")
                    if self.set_volume(self.target_volume):
                        logger.info(f"Successfully lowered volume to {self.target_volume}%")
                        return True
                    else:
                        logger.error("Failed to lower volume")
                else:
                    logger.info(f"Current volume ({current_volume}%) is already below target ({self.target_volume}%)")
            else:
                logger.warning("Could not get current volume")
        else:
            logger.debug(f"Original volume already stored: {self.original_volume}%")
        return False
    
    def restore_volume(self):
        """Restore original volume if it was changed"""
        if self.original_volume is not None:
            logger.debug(f"Restoring volume to original level: {self.original_volume}%")
            if self.set_volume(self.original_volume):
                logger.info(f"Successfully restored volume to {self.original_volume}%")
                self.original_volume = None
                return True
            else:
                logger.error("Failed to restore volume")
        return False

class KeyboardHandler:
    def __init__(self, on_start_recording=None, on_stop_recording=None, enable_volume_control=Config.SHOULD_ADJUST_VOLUME):
        self.listener = None
        self.on_start_recording = on_start_recording
        self.on_stop_recording = on_stop_recording
        self.volume_controller = VolumeController(Config.RECORDING_VOLUME) if enable_volume_control else None
        
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
            if key == keyboard.Key.f4:
                logger.info("Recording hotkey pressed")
                if self.volume_controller and Config.SHOULD_ADJUST_VOLUME:
                    self.volume_controller.store_current_volume()
                
                if self.on_start_recording:
                    self.on_start_recording()
                    
        except Exception as e:
            logger.error(f"Error handling key press: {str(e)}", exc_info=True)
            
    def _handle_release(self, key):
        """Handle key release"""
        try:
            if key == keyboard.Key.f4:
                logger.info("Recording hotkey released")
                if self.volume_controller and Config.SHOULD_ADJUST_VOLUME:
                    self.volume_controller.restore_volume()
                
                if self.on_stop_recording:
                    self.on_stop_recording()
                    
        except Exception as e:
            logger.error(f"Error handling key release: {str(e)}", exc_info=True)
            
    def stop(self):
        """Stop keyboard listener"""
        if self.listener:
            try:
                # Restore volume if it was changed
                if self.volume_controller:
                    self.volume_controller.restore_volume()
                
                self.listener.stop()
                logger.info("Keyboard listener stopped")
            except Exception as e:
                logger.error(f"Error stopping keyboard listener: {e}", exc_info=True)
                
    def is_running(self):
        """Check if listener is running"""
        return self.listener and self.listener.running 