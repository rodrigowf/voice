import logging
import threading
import pystray
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from PIL import Image, ImageDraw
from ..config import Config

logger = logging.getLogger(__name__)

class TrayIcon:
    def __init__(self, on_exit=None):
        logger.debug("Initializing TrayIcon")
        self.icon = None
        self.on_exit = on_exit
        self.menu_items = None
        
    def create_icon(self, color):
        """Create a round icon with specified color"""
        logger.debug(f"Creating icon with color: {color}")
        try:
            # Create base image at 2x the desired size for better quality
            size = Config.ICON_SIZE * 2
            image = Image.new('RGB', (size, size), color='black')
            dc = ImageDraw.Draw(image)
            dc.ellipse([4, 4, size-4, size-4], fill=color)
            
            # Use Resampling.LANCZOS for better quality
            image = image.resize((Config.ICON_SIZE, Config.ICON_SIZE), 
                               resample=Image.Resampling.LANCZOS)
            logger.debug("Icon created successfully")
            return image
        except Exception as e:
            logger.error(f"Failed to create icon: {e}", exc_info=True)
            return None
            
    def _handle_exit(self):
        """Handle exit menu item click"""
        logger.debug("Exit menu item clicked")
        if self.icon:
            logger.debug("Stopping icon")
            self.icon.stop()
        if self.on_exit:
            logger.debug("Calling exit handler")
            self.on_exit()
            
    def _handle_about(self):
        """Show about information"""
        logger.debug("About menu item clicked")
        try:
            dialog = Gtk.MessageDialog(
                None,
                0,
                Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK,
                "Voice to Text"
            )
            dialog.format_secondary_text(
                "Voice-to-Text Transcription Application\n"
                "Hold F4 to record, release to transcribe.\n"
                "Version: 1.0.0"
            )
            logger.debug("Showing about dialog")
            dialog.run()
            dialog.destroy()
            logger.debug("About dialog closed")
        except Exception as e:
            logger.error(f"Error showing about dialog: {e}", exc_info=True)
        
    def _handle_language_select(self, lang_code):
        """Handle language selection"""
        logger.debug(f"Language selected: {lang_code}")
        Config.CURRENT_LANGUAGE = lang_code
        logger.info(f"Language changed to: {lang_code}")
        
    def _create_menu(self):
        """Create the tray icon menu"""
        logger.debug("Creating tray icon menu")
        try:
            # Create language submenu items
            language_items = []
            for lang_name, lang_code in Config.SUPPORTED_LANGUAGES.items():
                language_items.append(
                    pystray.MenuItem(
                        lang_name,
                        self._create_language_handler(lang_code),
                        checked=lambda item, code=lang_code: Config.CURRENT_LANGUAGE == code,
                        radio=True
                    )
                )

            menu = pystray.Menu(
                pystray.MenuItem(
                    "Voice to Text",
                    None,
                    enabled=False
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Language",
                    pystray.Menu(*language_items)
                ),
                pystray.MenuItem(
                    "About",
                    self._handle_about
                ),
                pystray.MenuItem(
                    "Exit",
                    self._handle_exit
                )
            )
            logger.debug("Menu created successfully")
            return menu
        except Exception as e:
            logger.error(f"Error creating menu: {e}", exc_info=True)
            return None

    def _create_language_handler(self, lang_code):
        """Create a handler function for language selection"""
        def handler(icon, item):
            self._handle_language_select(lang_code)
        return handler
            
    def setup(self):
        """Initialize system tray icon"""
        logger.debug("Setting up tray icon")
        try:
            menu = self._create_menu()
            if not menu:
                raise RuntimeError("Failed to create menu")
                
            self.icon = pystray.Icon(
                "VoiceToText",
                self.create_icon(Config.ICON_COLOR_IDLE),
                "Voice to Text (Hold F4)",
                menu=menu
            )
            
            # Start the icon in a separate thread
            logger.debug("Starting icon thread")
            icon_thread = threading.Thread(target=self._run_icon, daemon=True)
            icon_thread.start()
            
            logger.info("System tray icon initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to setup system tray icon: {e}", exc_info=True)
            return False
            
    def _run_icon(self):
        """Run the icon in a separate thread with proper GTK initialization"""
        try:
            logger.debug("Initializing GTK")
            Gtk.init()
            logger.debug("Starting icon main loop")
            self.icon.run()
            logger.debug("Icon main loop ended")
        except Exception as e:
            logger.error(f"Error running tray icon: {e}", exc_info=True)
            
    def set_recording_state(self, is_recording):
        """Update icon color based on recording state"""
        if self.icon:
            try:
                logger.debug(f"Setting recording state: {is_recording}")
                color = Config.ICON_COLOR_RECORDING if is_recording else Config.ICON_COLOR_IDLE
                self.icon.icon = self.create_icon(color)
                # Update tooltip
                self.icon.title = "Recording..." if is_recording else "Voice to Text (Hold F4)"
            except Exception as e:
                logger.error(f"Failed to update icon state: {e}", exc_info=True)
                
    def set_processing_state(self, is_processing):
        """Update icon color based on processing state"""
        if self.icon:
            try:
                logger.debug(f"Setting processing state: {is_processing}")
                color = Config.ICON_COLOR_PROCESSING if is_processing else Config.ICON_COLOR_IDLE
                self.icon.icon = self.create_icon(color)
                # Update tooltip
                self.icon.title = "Processing..." if is_processing else "Voice to Text (Hold F4)"
            except Exception as e:
                logger.error(f"Failed to update processing state: {e}", exc_info=True)
                
    def cleanup(self):
        """Clean up resources"""
        logger.debug("Cleaning up tray icon")
        if self.icon:
            try:
                self.icon.stop()
                logger.debug("Tray icon stopped")
            except Exception as e:
                logger.error(f"Error removing system tray icon: {e}", exc_info=True)
                
    def is_running(self):
        """Check if icon is running"""
        running = self.icon and self.icon.visible
        logger.debug(f"Tray icon running state: {running}")
        return running 