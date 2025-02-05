import sys
import logging
from src import VoiceToTextApp

def main():
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            raise RuntimeError("Python 3.7 or higher is required")
            
        # Initialize logging with more verbose output
        logging.basicConfig(
            level=logging.DEBUG,  # Changed to DEBUG level
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('voice_to_text.log'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        
        # Log system information
        logger.debug(f"Python version: {sys.version}")
        logger.debug(f"Platform: {sys.platform}")
        
        # Initialize and run the application
        logger.info("Starting Voice-to-Text application")
        app = VoiceToTextApp()
        
        # Log initialization status
        logger.debug("Application initialized, starting main loop")
        app.run()
        
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        logger.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)  # Added exc_info
        print(f"\nError: {e}")
        print("Check voice_to_text.log for more details")
        sys.exit(1)

if __name__ == "__main__":
    main() 