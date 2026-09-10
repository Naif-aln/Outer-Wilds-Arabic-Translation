# Changelog

## Unreleased

- Repository restructured as a complete open-source project: mod source, installer source, UI assets, build script and CI.
- The `.exe` is no longer committed to the repository. Releases are built by GitHub Actions from the source in this repository and published on the Releases page together with `SHA256SUMS.txt`.
- Releases now also include `arabic.OWArabicTranslation.zip` for manual installation through the Outer Wilds Mod Manager.

## 1.0.0 - 2026-03-29

- First public release, distributed as `OWArabicTranslation_Installer.exe` committed directly to the repository.
- SHA-256 of that original file: `6ed16478cdedfc969dac91f694fa5a1f4b6285a3088d8edcec811b928c92c1a3`
- Contents: 2424 translated dialogue entries, Arabic letter shaping and right-to-left line handling in `ArabicTranslation.dll`, Noto Sans Arabic font bundle.
