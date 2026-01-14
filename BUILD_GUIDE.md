# MurmurTone Build Guide

Complete guide to building MurmurTone installer with bundled model.

---

## Prerequisites

### Required Software
1. **Python 3.12** - https://www.python.org/downloads/
2. **PyInstaller** - Installed automatically by build script
3. **Inno Setup 6+** - https://jrsoftware.org/isdl.php (for installer)

### Optional (for code signing)
4. **Windows SDK** - For `signtool.exe` (included in Visual Studio)
5. **EV Code Signing Certificate** - See [CODE_SIGNING.md](CODE_SIGNING.md)

---

## Quick Start

### Option 1: Automated Build (Recommended)

```batch
REM One-command build (downloads model, builds EXE, creates installer)
build.bat
```

This will:
1. Download and prepare tiny.en model (~150MB)
2. Build MurmurTone.exe with PyInstaller
3. Create installer (if Inno Setup installed)

**Output:**
- `dist\MurmurTone\MurmurTone.exe` - Standalone application
- `installer_output\MurmurTone-1.0.0-Setup.exe` - Windows installer

---

## Step-by-Step Build Process

### Step 1: Prepare Model (Optional but Recommended)

Bundle the tiny.en model to avoid ~150MB download on first run:

```batch
python prepare_model.py
```

**What it does:**
- Downloads tiny.en from HuggingFace (if not cached)
- Copies model files to `models/tiny.en/`
- Takes 2-5 minutes depending on internet speed

**Output:**
```
✓ Model prepared for bundling!
  Location: models\tiny.en
  Files: 8
  Size: 151.2 MB
```

**Skip this step if:**
- You want users to download model on first run
- You're building a "lite" installer without bundled model

---

### Step 2: Build EXE with PyInstaller

```batch
REM Install PyInstaller if needed
python -m pip install pyinstaller

REM Build executable
pyinstaller murmurtone.spec --noconfirm
```

**What it does:**
- Packages Python app + dependencies into standalone EXE
- Includes bundled model (if prepared in Step 1)
- Creates folder: `dist\MurmurTone\`

**Output:**
```
dist\MurmurTone\
├── MurmurTone.exe       (main executable)
├── models\              (bundled model, if prepared)
│   └── tiny.en\
├── _internal\           (dependencies)
├── LICENSE
└── THIRD_PARTY_LICENSES.md
```

**Build time:** 2-5 minutes

---

### Step 3: Create Installer (Optional)

```batch
REM Install Inno Setup from https://jrsoftware.org/isdl.php
REM Add to PATH: C:\Program Files (x86)\Inno Setup 6

REM Build installer
iscc installer.iss
```

**What it does:**
- Packages `dist\MurmurTone\` into single-file installer
- Adds start menu shortcuts
- Adds uninstaller
- Optionally signs installer (if certificate configured)

**Output:**
```
installer_output\MurmurTone-1.0.0-Setup.exe
```

**Installer size:**
- Without bundled model: ~50MB
- With bundled model: ~200MB

---

## Code Signing (Recommended for Launch)

### Why Sign?
- Prevents Windows SmartScreen warnings
- Increases trust and conversion rates
- **Required for professional launch**

See [CODE_SIGNING.md](CODE_SIGNING.md) for complete guide.

### Quick Signing Setup

```batch
REM Set environment variables
set SIGN_TOOL_PATH=C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe
set SIGN_CERT_PATH=C:\path\to\certificate.pfx
set SIGN_CERT_PASS=your-password

REM Build and sign automatically
build.bat
```

Or sign manually after building:

```batch
signtool.exe sign ^
  /f "certificate.pfx" ^
  /p "password" ^
  /t http://timestamp.digicert.com ^
  /fd sha256 ^
  "installer_output\MurmurTone-1.0.0-Setup.exe"
```

---

## Build Configurations

### Production Build (Recommended)
```batch
REM Full build with bundled model and installer
python prepare_model.py
build.bat
```

**Result:**
- ✅ 200MB installer
- ✅ Works offline immediately
- ✅ Professional installation experience

### Lite Build (No Bundled Model)
```batch
REM Skip model preparation
pyinstaller murmurtone.spec --noconfirm
iscc installer.iss
```

**Result:**
- ✅ 50MB installer
- ⚠️ Downloads model on first run (~150MB)
- ⚠️ Requires internet connection for first use

### Development Build (Fastest)
```batch
REM Skip installer, just build EXE
pyinstaller murmurtone.spec --noconfirm
```

**Result:**
- ✅ Fast iteration (~2 min build time)
- ✅ Test in `dist\MurmurTone\`
- ⚠️ No installer

---

## Testing the Build

### Test Standalone EXE
```batch
REM Run directly from dist folder
cd dist\MurmurTone
MurmurTone.exe
```

**Check:**
- ✅ App appears in system tray
- ✅ Settings window opens
- ✅ Model loads without download (if bundled)
- ✅ Transcription works

### Test Installer
```batch
REM Install to test environment
installer_output\MurmurTone-1.0.0-Setup.exe
```

**Check:**
- ✅ No SmartScreen warnings (if signed)
- ✅ Start menu shortcuts created
- ✅ Uninstaller works
- ✅ App launches after install

### Test on Clean Windows VM
**Critical for production:**
1. Create fresh Windows 10/11 VM
2. Download installer from external source (email, cloud)
3. Run installer
4. Verify no warnings, proper installation

---

## Troubleshooting

### "Model not found" warning during build
**Solution:** Run `python prepare_model.py` first

### PyInstaller build fails
**Common causes:**
- Missing dependencies: `pip install -r requirements.txt`
- Antivirus blocking: Temporarily disable or add exception
- Disk space: Need ~500MB free for build

### Inno Setup not found
**Solution:**
1. Download from https://jrsoftware.org/isdl.php
2. Install (default location: `C:\Program Files (x86)\Inno Setup 6`)
3. Add to PATH or run `iscc` with full path

### Installer shows SmartScreen warning
**Expected for unsigned installers!**
- Sign with EV certificate (see [CODE_SIGNING.md](CODE_SIGNING.md))
- Or accept 20-30% user abandonment

### "Access denied" during build
**Solution:**
- Close MurmurTone if running
- Delete `dist\` and `build\` folders
- Re-run build script

---

## Build Automation (CI/CD)

### GitHub Actions Example

```yaml
name: Build Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Prepare model
        run: python prepare_model.py

      - name: Build EXE
        run: pyinstaller murmurtone.spec --noconfirm

      - name: Install Inno Setup
        run: choco install innosetup

      - name: Build Installer
        run: iscc installer.iss

      - name: Upload Release
        uses: actions/upload-artifact@v3
        with:
          name: installer
          path: installer_output/*.exe
```

---

## File Size Reference

| Item | Size | Notes |
|------|------|-------|
| Python source | ~5MB | Git repo |
| tiny.en model | ~151MB | Downloaded once |
| PyInstaller build | ~50MB | Without model |
| PyInstaller build | ~200MB | With bundled model |
| Installer (no model) | ~50MB | Compressed |
| Installer (with model) | ~200MB | Compressed |

---

## Release Checklist

Before creating public release:

- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Update version in `config.py`, `installer.iss`, `murmurtone.spec`
- [ ] Build with bundled model: `python prepare_model.py`
- [ ] Build signed installer: `build.bat` (with signing configured)
- [ ] Test on clean Windows 10 VM
- [ ] Test on clean Windows 11 VM
- [ ] Verify no SmartScreen warnings
- [ ] Test uninstaller
- [ ] Upload to release hosting (GitHub Releases, website, etc.)
- [ ] Update download links on website

---

## Support

For build issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review build logs in console output
3. Open issue at https://github.com/anthropics/murmurtone/issues

For code signing questions:
- See [CODE_SIGNING.md](CODE_SIGNING.md)

---

## Quick Reference

```batch
# Full production build
python prepare_model.py && build.bat

# Test standalone
dist\MurmurTone\MurmurTone.exe

# Manual installer build
iscc installer.iss

# Manual code signing
signtool sign /f cert.pfx /p password /t http://timestamp.digicert.com /fd sha256 installer_output\*.exe

# Verify signature
signtool verify /pa installer_output\*.exe
```
