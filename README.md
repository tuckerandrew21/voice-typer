# MurmurTone

Your voice, locally. A private, lightweight voice-to-text tool for Windows that respects your privacy by running entirely offline.

Press your hotkey to record, release to transcribe, and your words appear instantly—no cloud, no tracking, no delays.

Powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for fast, accurate, local speech recognition.

## Features

- **System tray app** - Runs quietly in the background
- **Customizable hotkey** - Set any key combination you want
- **Multiple models** - Choose between speed (tiny) and accuracy (medium)
- **GPU acceleration** - Optional CUDA support for faster transcription
- **Noise gate** - Filter out background noise automatically
- **Audio feedback** - Distinct sounds for recording, processing, success, and error states
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

### GPU Acceleration (Optional)

For faster transcription with NVIDIA GPUs:

```bash
pip install -r requirements-gpu.txt
```

**Requirements:**
- NVIDIA GPU with CUDA support
- CUDA 12.x compatible drivers

The app will automatically detect and use your GPU. You can also manually configure the device in Settings.

## Usage

1. Double-click `start.vbs` to launch
2. Look for the MurmurTone icon in the system tray
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
| Device | auto, cpu, cuda | Use GPU if available, or force CPU/GPU |
| Compute Type | int8, float16, float32 | float16/32 require GPU |
| Language | en, auto | English only or auto-detect |
| Noise Gate | On/Off, -60 to -20 dB | Filter out background noise |
| Audio Feedback | Processing, Success, Error | Individual sound toggles |
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
