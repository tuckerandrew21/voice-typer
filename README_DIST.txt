================================================================================
                         MurmurTone v1.0.0
              Private, Local Voice-to-Text for Windows
================================================================================

QUICK START
-----------
1. Open the MurmurTone folder
2. Double-click MurmurTone.exe
3. Look for the MurmurTone icon in your system tray (bottom-right, near clock)

That's it! Press Ctrl+Shift+Space to start recording, speak, then release to type.


WINDOWS SMARTSCREEN WARNING
---------------------------
When you first run MurmurTone, Windows may show a warning:

   "Windows protected your PC"
   "Microsoft Defender SmartScreen prevented an unrecognized app from starting"

This is normal for new software that isn't signed with an expensive code
certificate. MurmurTone is safe to run.

To proceed:
1. Click "More info" (small text link)
2. Click "Run anyway"

You only need to do this once.


BASIC USAGE
-----------
- Press Ctrl+Shift+Space (default) to start recording
- Speak clearly into your microphone
- Release the keys to transcribe and type into any application

The system tray icon shows the current status:
- Gray: Ready (not recording)
- Green: Recording in progress
- Yellow: Processing/Transcribing

Right-click the tray icon for:
- Settings: Change hotkey, model size, recording mode
- Exit: Close MurmurTone


SETTINGS
--------
Model Size:
- tiny.en (default): Fastest, included in download
- base.en, small.en, medium.en: More accurate but slower (downloads on first use)

Recording Mode:
- Push-to-Talk: Hold hotkey while speaking, release to transcribe
- Auto-Stop: Press hotkey to start, stops automatically after silence

Audio Feedback: Plays sounds when recording starts/stops


PRIVACY & SECURITY
------------------
MurmurTone processes all audio locally on your computer. No audio, text, or
personal data is ever sent to external servers.

- All speech recognition happens on YOUR machine using the Whisper model
- No internet connection required (except to download larger models)
- No accounts, no tracking, no telemetry
- Settings are stored locally in %APPDATA%\MurmurTone\


UNINSTALL
---------
1. Right-click tray icon and select "Exit"
2. Delete the MurmurTone folder
3. (Optional) Delete settings: %APPDATA%\MurmurTone\


TROUBLESHOOTING
---------------

"App won't start"
  - Make sure you're running MurmurTone.exe from inside the MurmurTone folder
  - Don't move just the .exe file - it needs the other files in the folder

"Antivirus blocks the app"
  - Some antivirus software flags keyboard-listening apps
  - MurmurTone only listens for your configured hotkey, nothing else
  - Add the MurmurTone folder to your antivirus exceptions

"No text appears"
  - Check your microphone is working (test in Windows Settings > Sound)
  - Make sure a text field is focused when you speak
  - Try speaking closer to the microphone

"First launch is slow"
  - Normal - the speech recognition model takes 5-10 seconds to load
  - Subsequent recordings are instant


SYSTEM REQUIREMENTS
-------------------
- Windows 10 or Windows 11 (64-bit)
- Microphone
- ~400 MB disk space


SUPPORT
-------
For help or to report issues:
Email: support@murmurtone.com

Website: murmurtone.com


LICENSE
-------
MIT License - See LICENSE.txt for details

MurmurTone uses the following open-source components:
- faster-whisper (MIT License)
- OpenAI Whisper (MIT License)
- And others - see THIRD_PARTY_LICENSES.md for full details


================================================================================
                    Thank you for using MurmurTone!
================================================================================
