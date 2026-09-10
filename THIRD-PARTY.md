# Third-party components

| Component | Where it is used | License |
|---|---|---|
| [Noto Sans Arabic](https://fonts.google.com/noto/specimen/Noto+Sans+Arabic) | Packed inside `ArabicTranslation/arabicfont` (Unity asset bundle). See [docs/font.md](docs/font.md). | SIL Open Font License 1.1 |
| [Interplanetary Polyglot](https://github.com/xen-42/outer-wilds-localization-utility) (`xen.LocalizationUtility`) | Required at runtime. Not bundled; the installer downloads the latest release from GitHub. | MIT |
| [OWML](https://github.com/ow-mods/owml) | Required at runtime. Not bundled; the installer downloads the latest release from GitHub. | MIT |
| [Outer Wilds Mod Manager](https://github.com/ow-mods/ow-mod-man) | Required at runtime. Not bundled; the installer downloads the latest release from GitHub. | MIT |
| [PyInstaller](https://pyinstaller.org/) | Build time only. Packs `installer/installer.py` into the `.exe`. | GPL with bootloader exception, which does not affect the produced program |
| Outer Wilds name and logo | Shown in the installer window (`installer/assets/ow_logo.gif`). | Property of Mobius Digital. This is an unofficial fan translation, not affiliated with Mobius Digital or Annapurna Interactive. |
