# Voice Typer

A simple, local voice-to-text tool for Windows. Press a hotkey to record your voice, release to transcribe and automatically type the text into any application.

Powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for fast, accurate, offline speech recognition.

## Features

- **System tray app** - Runs quietly in the background
- **Customizable hotkey** - Set any key combination you want
- **Multiple models** - Choose between speed (tiny) and accuracy (medium)
- **Auto-language detection** - English or auto-detect
- **Settings GUI** - Easy configuration, no code editing required
- **Hot-reload** - Change models without restarting

## Installation

### Requirements

- Python 3.11 (recommended)
- Windows

### Setup

```bash
git clone https://github.com/tuckerandrew21/voice-typer.git
cd voice-typer
pip install -r requirements.txt
```

## Usage

1. Double-click `start.vbs` to launch
2. Look for the Voice Typer icon in the system tray
3. Press your hotkey (default: **Ctrl+Shift+Space**) to start recording
4. Release to stop recording and transcribe
5. Text is automatically typed into the active window

### System Tray Menu

Right-click the tray icon to access:

- **Settings** - Open the configuration window
- **Exit** - Close the application

## Configuration

Right-click the tray icon and select **Settings** to configure:

| Setting | Options | Description |
|---------|---------|-------------|
| Model Size | tiny.en, base.en, small.en, medium.en | Larger = more accurate but slower |
| Language | en, auto | English only or auto-detect |
| Sample Rate | 16000 (default) | Audio recording quality |
| Hotkey | Any combination | Click "Set Hotkey" and press your keys |

Settings are saved to `settings.json` and persist between sessions.

## Model Comparison

| Model | Speed | Accuracy | RAM Usage |
|-------|-------|----------|-----------|
| tiny.en | Fastest | Good | ~1 GB |
| base.en | Fast | Better | ~1.5 GB |
| small.en | Medium | Great | ~2.5 GB |
| medium.en | Slower | Best | ~5 GB |

## Dependencies

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Local Whisper speech recognition
- [pynput](https://github.com/moses-palmer/pynput) - Keyboard listening and simulation
- [pystray](https://github.com/moses-palmer/pystray) - System tray icon
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Audio recording
- numpy - Audio processing
- Pillow - Icon handling
- tkinter - Settings GUI (built into Python)

## License

MIT
