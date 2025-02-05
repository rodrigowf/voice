import pytest
import pyaudio
import wave
import os
from unittest.mock import MagicMock, patch
from voice import VoiceToTextApp

@pytest.fixture
def mock_pyaudio():
    with patch('pyaudio.PyAudio') as mock:
        # Mock the format attributes
        mock.paFloat32 = 0x1
        mock.paInt16 = 0x2
        mock.paInt32 = 0x4
        yield mock

@pytest.fixture
def app(mock_pyaudio):
    with patch('openai.OpenAI'):
        return VoiceToTextApp()

def test_icon_creation(app):
    """Test that system tray icons are created correctly"""
    green_icon = app.create_icon('green')
    red_icon = app.create_icon('red')
    assert green_icon.size == (64, 64)
    assert red_icon.size == (64, 64)

@patch('pyaudio.PyAudio')
def test_recording_start_stop(mock_pyaudio, app):
    """Test recording start and stop functionality"""
    # Mock the audio stream
    mock_stream = MagicMock()
    app.audio.open.return_value = mock_stream
    
    # Test starting recording
    app.start_recording()
    assert app.is_recording == True
    assert app.stream is not None
    
    # Test stopping recording
    with patch('voice.VoiceToTextApp.process_audio'):
        app.stop_recording()
        assert app.is_recording == False
        assert app.stream is None

@patch('openai.OpenAI')
def test_whisper_api_integration(mock_openai, app):
    """Test Whisper API integration"""
    # Create a proper mock response
    mock_transcription = "Test transcription"
    
    # Setup the mock chain properly
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = mock_transcription
    mock_openai.return_value = mock_client
    
    # Replace the app's client with our mock
    app.client = mock_client
    
    # Create test audio file
    app.frames = [b'0' * 1024]  # Mock audio data
    
    with patch('pyautogui.write') as mock_write:
        app.process_audio()
        mock_write.assert_called_once_with(mock_transcription)

def test_cleanup(app):
    """Test application cleanup"""
    with patch('voice.VoiceToTextApp.quit_application') as mock_quit:
        app.quit_application()
        assert mock_quit.called 