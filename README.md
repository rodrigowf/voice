# Voice-to-Text Transcription Tool

A lightweight, system-tray based application that provides real-time voice-to-text transcription using OpenAI's Whisper API. Simply hold F4, speak, and release to have your speech transcribed directly to your cursor position.

![Status](https://img.shields.io/badge/status-stable-green.svg)
![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

- 🎙️ Real-time voice recording with automatic silence detection
- 🔄 Instant transcription using OpenAI's Whisper API
- 🌐 Support for multiple languages (English and Portuguese)
- 🖥️ System tray integration for easy access
- ⌨️ Hotkey support (F4) for quick recording
- 📝 Direct text insertion at cursor position
- 🎯 Minimal CPU usage when idle

## Requirements

- Python 3.7 or higher
- Linux with GTK3 support
- ALSA/PulseAudio for audio capture
- OpenAI API key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/voice-to-text.git
   cd voice-to-text
   ```

2. Create a `.env` file with your OpenAI API key:
   ```bash
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

3. Run the installation script:
   ```bash
   sudo ./install.sh
   ```

The installation script will:
- Install required system dependencies
- Set up a Python virtual environment
- Install Python package dependencies
- Configure audio settings
- Create a desktop entry for easy access

## Usage

1. Start the application:
   ```bash
   ./run.sh
   ```
   Or launch it from your applications menu.

2. Look for the green icon in your system tray.

3. To transcribe:
   - Hold F4
   - Speak clearly
   - Release F4
   - The transcribed text will appear at your cursor position

4. Additional features:
   - Right-click the tray icon for options
   - Switch between languages from the tray menu
   - Click "About" for version information
   - Use "Exit" to close the application

## Configuration

The application can be configured by modifying `src/voice_to_text/config.py`:

- Audio settings (sample rate, channels, chunk size)
- Recording thresholds and durations
- Language preferences
- UI customization

## Architecture

The application is structured into several key components:

```
src/voice_to_text/
├── audio/
│   ├── recorder.py    # Audio capture and processing
│   └── transcriber.py # Whisper API integration
├── ui/
│   ├── tray_icon.py   # System tray interface
│   ├── text_output.py # Text insertion handling
│   └── keyboard_handler.py # Hotkey management
└── config.py          # Application configuration
```

## Troubleshooting

### Common Issues

1. **No audio input detected**
   - Check your microphone permissions
   - Verify ALSA/PulseAudio configuration
   - Run `alsamixer` to check input levels

2. **Transcription not appearing**
   - Ensure your OpenAI API key is valid
   - Check internet connectivity
   - Verify cursor is in a text-editable area

3. **System tray icon not showing**
   - Ensure GTK3 is properly installed
   - Check if your desktop environment supports system trays

### Logs

Application logs are stored in `voice_to_text.log`. Enable debug logging by modifying the logging level in `run.py`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAI Whisper](https://openai.com/research/whisper) for the transcription API
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) for audio handling
- [pystray](https://github.com/moses-palmer/pystray) for system tray integration

## Support

If you encounter any issues or have questions, please:
1. Check the [Troubleshooting](#troubleshooting) section
2. Look through existing [Issues](https://github.com/yourusername/voice-to-text/issues)
3. Create a new issue if needed

---

Made with ❤️ by Rodrigo Werneck @rodrigowf ou rodrigowf.github.io in partnership with CursorIDE powered by Claude-3.5-sonnet