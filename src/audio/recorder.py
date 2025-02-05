import pyaudio
import numpy as np
import wave
from datetime import datetime
import logging
from pathlib import Path
from ..config import Config

logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(self):
        self.format = pyaudio.paFloat32
        self.channels = Config.CHANNELS
        self.rate = Config.RATE
        self.chunk = Config.CHUNK
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.audio = None
        self.device_index = None
        
        self._initialize_audio()
        
    def _initialize_audio(self):
        """Initialize PyAudio and find suitable input device"""
        try:
            self.audio = pyaudio.PyAudio()
            self.device_index = self._find_input_device()
            if self.device_index is None:
                raise RuntimeError("No suitable input device found")
        except Exception as e:
            logger.error(f"Failed to initialize PyAudio: {e}")
            raise
            
    def _find_input_device(self):
        """Find the first working input device"""
        logger.info("Searching for input devices...")
        
        try:
            # Try default input device first
            default_device = self.audio.get_default_input_device_info()
            logger.info(f"Testing default input device: {default_device['name']}")
            
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            stream.close()
            logger.info(f"Using default input device: {default_device['name']}")
            return default_device['index']
        except Exception as e:
            logger.warning(f"Default device test failed: {e}")
            
        # If default device failed, try all devices
        try:
            info = self.audio.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            
            for i in range(numdevices):
                try:
                    device_info = self.audio.get_device_info_by_index(i)
                    logger.info(f"Testing device {i}: {device_info['name']}")
                    
                    if device_info.get('maxInputChannels', 0) <= 0:
                        continue
                        
                    stream = self.audio.open(
                        format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        input_device_index=i,
                        frames_per_buffer=self.chunk
                    )
                    stream.close()
                    logger.info(f"Selected input device {i}: {device_info['name']}")
                    return i
                except Exception as e:
                    logger.warning(f"Device {i} test failed: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error enumerating devices: {e}")
            
        logger.error("No working input device found")
        return None
        
    def start(self):
        """Start audio recording"""
        if not self.device_index:
            logger.error("No input device available")
            return False
            
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
            logger.info("Recording started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            return False
            
    def record_chunk(self):
        """Record a single chunk of audio"""
        if not self.is_recording or not self.stream:
            return False
            
        try:
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.float32)
            
            # Only append if above silence threshold
            if np.max(np.abs(audio_data)) > Config.SILENCE_THRESHOLD:
                self.frames.append(data)
                
            # Check if we've exceeded maximum duration
            duration = len(self.frames) * self.chunk / self.rate
            if duration >= Config.MAX_AUDIO_LENGTH:
                logger.warning("Maximum recording duration reached")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error recording chunk: {e}")
            return False
            
    def stop(self):
        """Stop audio recording"""
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            except Exception as e:
                logger.error(f"Error stopping stream: {e}")
                
    def save_recording(self, output_path: Path) -> bool:
        """Save recorded audio to a WAV file"""
        if not self.frames:
            logger.warning("No audio frames to save")
            return False
            
        try:
            # Convert frames to numpy array
            audio_data = np.frombuffer(b''.join(self.frames), dtype=np.float32)
            
            # Check duration
            duration = len(audio_data) / self.rate
            if duration < Config.MIN_AUDIO_LENGTH:
                logger.warning(f"Audio too short ({duration:.2f}s)")
                return False
                
            # Normalize audio
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val
                
            # Convert to int16
            audio_data_int16 = (audio_data * 32767).astype(np.int16)
            
            # Save as WAV
            with wave.open(str(output_path), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 2 bytes for int16
                wf.setframerate(self.rate)
                wf.writeframes(audio_data_int16.tobytes())
                
            # Clear frames
            self.frames = []
            return True
            
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            return False
            
    def cleanup(self):
        """Clean up resources"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing stream: {e}")
                
        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
                
        # Clear memory
        self.frames = [] 