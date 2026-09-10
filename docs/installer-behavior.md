# What the installer does, step by step

This page describes exactly what `OWArabicTranslation_Installer.exe` does on your machine. Everything here can be checked against [`installer/installer.py`](../installer/installer.py). The `.exe` is that script packed with PyInstaller, plus the files listed in the last section.

## Network access

The installer contacts only these addresses, and only when a component is missing:

| Request | Purpose |
|---|---|
| `https://api.github.com/repos/ow-mods/ow-mod-man/releases/latest` | Find the latest Outer Wilds Mod Manager setup `.exe` |
| `https://api.github.com/repos/ow-mods/owml/releases/latest` | Find the latest OWML `.zip` |
| `https://api.github.com/repos/xen-42/outer-wilds-localization-utility/releases/latest` | Find the latest Interplanetary Polyglot `.zip` |
| `https://github.com/.../releases/download/...` | Download the asset found above |

There is no telemetry, no analytics, no update check for the translation itself, and nothing is uploaded anywhere.

## Steps

1. **Find the game.** Reads the Steam path from the registry (`HKCU\Software\Valve\Steam` and `HKLM\SOFTWARE\WOW6432Node\Valve\Steam`), parses `libraryfolders.vdf`, and also checks common folder names on every drive letter. If `OuterWilds.exe` is not found you are asked to point to it. Nothing is written in this step.
2. **Mod Manager.** If `Outer Wilds Mod Manager.exe` is not found, the latest setup is downloaded to `%TEMP%` and run with the `/S` (silent) flag. Windows shows a UAC prompt because the Mod Manager setup itself requires elevation. The temporary file is deleted afterwards.
3. **OWML.** If `OWML.Launcher.exe` is not found, the latest OWML zip is downloaded and extracted to `%APPDATA%\OuterWildsModManager\OWML`. If that folder already exists without a launcher it is deleted and recreated.
4. **Interplanetary Polyglot.** If `Mods\xen.LocalizationUtility` does not exist, the latest release zip is downloaded and extracted there.
5. **The translation.** These five files are written to `%APPDATA%\OuterWildsModManager\OWML\Mods\arabic.OWArabicTranslation`, overwriting older copies:
   - `ArabicTranslation.dll`
   - `manifest.json`
   - `default-config.json`
   - `Translation_Arabic.xml`
   - `arabicfont`

That is all. The installer never touches the game folder, never modifies game files, adds no startup entries, and writes no registry keys.

## Files packed inside the .exe

Besides the five mod files above, the `.exe` contains the images from `installer/assets/`: the Outer Wilds logo, pre-rendered Arabic labels for the window, two screenshots for the instructions window, and the window icon. Arabic labels are shipped as images because Tkinter cannot shape Arabic text.

## Why Windows may warn about the file

The `.exe` is a PyInstaller bundle and is not code-signed, so SmartScreen may show "Windows protected your PC", and some antivirus engines flag PyInstaller bundles generically. If you would rather not run it, follow the [manual installation](manual-install.md). It gives the same result without running any executable from this project.
