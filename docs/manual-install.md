# Manual installation (no .exe)

Use this if you prefer not to run the installer. The result is identical.

1. Install the [Outer Wilds Mod Manager](https://outerwildsmods.com/mod-manager/).
2. In the Mod Manager, open **Get Mods** and install **Interplanetary Polyglot**.
3. Download `arabic.OWArabicTranslation.zip` from the [Releases page](https://github.com/Naif-aln/Outer-Wilds-Arabic-Translation/releases/latest) and compare its hash with `SHA256SUMS.txt` from the same release:

   ```powershell
   Get-FileHash .\arabic.OWArabicTranslation.zip -Algorithm SHA256
   ```

4. In the Mod Manager, open the menu in the top-right corner, choose **Install from zip**, and pick the file.
   Alternatively, extract the zip into
   `%APPDATA%\OuterWildsModManager\OWML\Mods\arabic.OWArabicTranslation\`
   so that `ArabicTranslation.dll` sits directly inside that folder.
5. Press **Run Game** in the Mod Manager. If the game does not start in Arabic, open **Options > Language** and choose **Arabic**.

To build the zip yourself instead of downloading it, see "Building from source" in the README.
