import os
import threading
import tempfile
import wave
from datetime import datetime
import pyaudio
from pynput import keyboard
import pystray
from PIL import Image, ImageDraw, ImageFilter
import openai
from pathlib import Path
import pyautogui
import time
import logging
from config import Config
import numpy as np
import warnings
from openai import OpenAI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_to_text.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress ALSA errors
warnings.filterwarnings("ignore", category=RuntimeWarning)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

class VoiceToTextApp:
    def __init__(self):
        try:
            # Validate configuration
            Config.validate()
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("Initializing Voice-to-Text Application")
            
            # Initialize variables
            self.is_recording = False
            self.frames = []
            self.stream = None
            self.recording_thread = None
            self.icon = None
            
            # Set audio format first
            self.format = pyaudio.paFloat32
            self.channels = Config.CHANNELS
            self.rate = Config.RATE
            self.chunk = Config.CHUNK
            
            # Initialize audio with error handling
            try:
                self.audio = pyaudio.PyAudio()
                # Find the correct input device
                self.device_index = self.find_input_device()
                if self.device_index is None:
                    raise RuntimeError("No suitable input device found")
            except Exception as e:
                self.logger.error(f"Failed to initialize PyAudio: {e}")
                raise
            
            # Initialize OpenAI client
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
            
            # Create system tray icon
            self.setup_system_tray()
            self.logger.info("Application initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            raise

    def find_input_device(self):
        """Find the first working input device"""
        self.logger.info("Searching for input devices...")
        
        try:
            # Try default input device first
            default_device = self.audio.get_default_input_device_info()
            self.logger.info(f"Testing default input device: {default_device['name']}")
            
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            stream.close()
            self.logger.info(f"Using default input device: {default_device['name']}")
            return default_device['index']
        except Exception as e:
            self.logger.warning(f"Default device test failed: {e}")
        
        # If default device failed, try all devices
        try:
            # List all available devices
            info = self.audio.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            
            for i in range(numdevices):
                try:
                    device_info = self.audio.get_device_info_by_index(i)
                    self.logger.info(f"Testing device {i}: {device_info['name']}")
                    
                    if device_info.get('maxInputChannels', 0) <= 0:
                        continue
                        
                    # Test if device works with our settings
                    stream = self.audio.open(
                        format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        input_device_index=i,
                        frames_per_buffer=self.chunk
                    )
                    stream.close()
                    self.logger.info(f"Selected input device {i}: {device_info['name']}")
                    return i
                except Exception as e:
                    self.logger.warning(f"Device {i} test failed: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"Error enumerating devices: {e}")
        
        self.logger.error("No working input device found")
        return None

    def create_icon(self, color):
        """Create a round icon with specified color"""
        try:
            # Create base image at 2x the desired size for better quality
            size = Config.ICON_SIZE * 2
            image = Image.new('RGB', (size, size), color='black')
            dc = ImageDraw.Draw(image)
            dc.ellipse([4, 4, size-4, size-4], fill=color)
            
            # Use Resampling.LANCZOS instead of deprecated ANTIALIAS
            image = image.resize((Config.ICON_SIZE, Config.ICON_SIZE), 
                               resample=Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            self.logger.error(f"Failed to create icon: {e}")
            return None
        
    def setup_system_tray(self):
        """Initialize system tray icon"""
        try:
            self.icon = pystray.Icon(
                "VoiceToText",
                self.create_icon(Config.ICON_COLOR_IDLE),
                "Voice to Text (Hold F4)",
                menu=pystray.Menu(
                    pystray.MenuItem("Exit", self.quit_application)
                )
            )
            # Start the icon in a separate thread
            threading.Thread(target=self.icon.run, daemon=True).start()
            self.logger.info("System tray icon initialized")
        except Exception as e:
            self.logger.error(f"Failed to setup system tray icon: {e}")
            raise

    def start_recording(self):
        """Start audio recording"""
        if not self.device_index:
            self.logger.error("No input device available")
            return
        
        self.is_recording = True
        self.frames = []
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk
            )
            self.icon.icon = self.create_icon(Config.ICON_COLOR_RECORDING)
            self.logger.info("Recording started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            raise
        
    def stop_recording(self):
        """Stop audio recording and process the audio"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            except Exception as e:
                self.logger.error(f"Error stopping stream: {e}")
        
        self.icon.icon = self.create_icon(Config.ICON_COLOR_IDLE)
        
        if self.frames:
            self.process_audio()
        else:
            self.logger.warning("No audio frames recorded")
        
    def record_audio(self):
        """Record audio while F4 is held"""
        while self.is_recording:
            try:
                if self.stream and not self.stream.is_stopped():
                    try:
                        data = self.stream.read(self.chunk, exception_on_overflow=False)
                        # Check if audio is not silence
                        audio_data = np.frombuffer(data, dtype=np.float32)
                        if np.max(np.abs(audio_data)) > Config.SILENCE_THRESHOLD:
                            self.frames.append(data)
                            
                            # Check if we've exceeded maximum audio length
                            if len(self.frames) * self.chunk / self.rate > Config.MAX_AUDIO_LENGTH:
                                self.logger.warning("Maximum audio length reached, stopping recording")
                                self.is_recording = False
                                break
                            
                    except OSError as e:
                        if e.errno == -9999:  # Unanticipated host error
                            self.logger.warning("Audio buffer overflow, continuing...")
                            continue
                        else:
                            raise
            except Exception as e:
                self.logger.error(f"Error during recording: {e}")
                self.is_recording = False
                break
        
    def process_audio(self):
        """Process recorded audio and send to Whisper API"""
        if not self.frames:
            self.logger.warning("No audio frames to process")
            return
            
        temp_file = Config.TEMP_DIR / f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        
        try:
            # Process audio in chunks to avoid memory issues
            frames_array = []
            chunk_size = 1000  # Process 1000 frames at a time
            
            for i in range(0, len(self.frames), chunk_size):
                chunk = self.frames[i:i + chunk_size]
                chunk_data = np.frombuffer(b''.join(chunk), dtype=np.float32)
                frames_array.append(chunk_data)
            
            # Concatenate all chunks
            audio_data = np.concatenate(frames_array) if frames_array else np.array([], dtype=np.float32)
            
            # Check if audio is too short
            duration = len(audio_data) / self.rate
            if duration < Config.MIN_AUDIO_LENGTH:
                self.logger.warning(f"Audio too short ({duration:.2f}s), ignoring")
                return
            
            # Normalize audio safely
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val
            
            # Convert to int16 safely
            audio_data_int16 = (audio_data * 32767).astype(np.int16)
            
            # Save as WAV
            with wave.open(str(temp_file), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 2 bytes for int16
                wf.setframerate(self.rate)
                wf.writeframes(audio_data_int16.tobytes())
            
            self.logger.info("Audio file saved, sending to Whisper API")
            
            # Clear frames to free memory
            self.frames = []
            
            with open(temp_file, 'rb') as audio_file:
                try:
                    transcript = self.client.audio.transcriptions.create(
                        model=Config.WHISPER_MODEL,
                        file=audio_file,
                        response_format=Config.WHISPER_RESPONSE_FORMAT,
                        language=Config.WHISPER_LANGUAGE
                    )
                    
                    if transcript and hasattr(transcript, 'text'):
                        text = transcript.text
                    elif isinstance(transcript, dict) and 'text' in transcript:
                        text = transcript['text']
                    elif isinstance(transcript, str):
                        text = transcript
                    else:
                        self.logger.warning("Unexpected response format from Whisper API")
                        return
                        
                    if text.strip():
                        self.logger.info(f"Transcription received: {text[:50]}...")
                        pyautogui.write(text)
                    else:
                        self.logger.warning("Empty transcription received from Whisper API")
                except Exception as e:
                    self.logger.error(f"Whisper API error: {e}")
                    self.logger.error(f"Response type: {type(transcript)}")
                    self.logger.error(f"Response content: {transcript}")
                
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
        finally:
            # Clean up
            self.frames = []
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception as e:
                    self.logger.error(f"Error deleting temporary file: {e}")
            
    def quit_application(self, icon=None, item=None):
        """Clean up and quit the application"""
        self.logger.info("Shutting down application...")
        
        # Stop recording if active
        if self.is_recording:
            self.stop_recording()
        
        # Clean up audio resources
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                self.logger.error(f"Error closing audio stream: {e}")
        
        if hasattr(self, 'audio') and self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                self.logger.error(f"Error terminating PyAudio: {e}")
        
        # Stop keyboard listener
        if hasattr(self, 'keyboard_listener'):
            try:
                self.keyboard_listener.stop()
            except Exception as e:
                self.logger.error(f"Error stopping keyboard listener: {e}")
        
        # Remove system tray icon
        if self.icon:
            try:
                self.icon.stop()
            except Exception as e:
                self.logger.error(f"Error removing system tray icon: {e}")
        
        self.logger.info("Application shutdown complete")
        os._exit(0)  # Force exit to clean up all threads

    def run(self):
        """Run the application"""
        try:
            # Setup keyboard listener
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            )
            self.keyboard_listener.start()
            self.logger.info("Keyboard listener started")
            
            # Keep the main thread running
            while True:
                time.sleep(0.1)
            
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
            self.quit_application()
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            self.quit_application()

    def on_press(self, key):
        """Handle key press"""
        try:
            if key == keyboard.Key.f4 and not self.is_recording:
                self.logger.info("Starting recording")
                self.start_recording()
                self.recording_thread = threading.Thread(target=self.record_audio)
                self.recording_thread.daemon = True  # Make thread daemon so it exits with main thread
                self.recording_thread.start()
        except Exception as e:
            self.logger.error(f"Error handling key press: {e}")

    def on_release(self, key):
        """Handle key release"""
        try:
            if key == keyboard.Key.f4 and self.is_recording:
                self.logger.info("Stopping recording")
                self.stop_recording()
                if self.recording_thread and self.recording_thread.is_alive():
                    self.recording_thread.join(timeout=1.0)  # Wait for thread to finish with timeout
        except Exception as e:
            self.logger.error(f"Error handling key release: {e}")

if __name__ == "__main__":
    app = VoiceToTextApp()
    app.run()
