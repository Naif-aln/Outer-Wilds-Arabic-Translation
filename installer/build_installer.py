import base64
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALLER_DIR = ROOT / "installer"
MOD_DIR = ROOT / "ArabicTranslation"
ASSETS_DIR = INSTALLER_DIR / "assets"
BUILD_DIR = INSTALLER_DIR / "build"
DIST_DIR = INSTALLER_DIR / "dist"
EXE_NAME = "OWArabicTranslation_Installer"
MOD_ZIP_NAME = "arabic.OWArabicTranslation.zip"

MOD_FILE_NAMES = [
    "manifest.json",
    "default-config.json",
    "Translation_Arabic.xml",
    "arabicfont",
]


def find_dll():
    for candidate in [
        MOD_DIR / "bin" / "Release" / "ArabicTranslation.dll",
        MOD_DIR / "bin" / "Debug" / "ArabicTranslation.dll",
    ]:
        if candidate.is_file():
            return candidate
    sys.exit("ArabicTranslation.dll not found. Run: dotnet build ArabicTranslation.sln -c Release")


def collect_mod_files():
    files = {"ArabicTranslation.dll": find_dll().read_bytes()}
    for name in MOD_FILE_NAMES:
        files[name] = (MOD_DIR / name).read_bytes()
    return files


def collect_assets():
    assets = {}
    for path in sorted(ASSETS_DIR.iterdir()):
        if path.suffix in {".gif", ".ico"}:
            assets[path.stem] = path.read_bytes()
    return assets


def bundle(files):
    source = (INSTALLER_DIR / "installer.py").read_text(encoding="utf-8")
    encoded = {name: base64.b64encode(data).decode("ascii") for name, data in files.items()}
    literal = "MOD_FILES = " + json.dumps(encoded, indent=4)
    patched, count = re.subn(r"^MOD_FILES = \{\}$", lambda _: literal, source, flags=re.M)
    if count != 1:
        sys.exit("installer.py must contain exactly one line reading MOD_FILES = {}")
    BUILD_DIR.mkdir(exist_ok=True)
    out = BUILD_DIR / "installer_bundled.py"
    out.write_text(patched, encoding="utf-8")
    return out


def run_pyinstaller(script):
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--onefile", "--windowed", "--clean", "--noconfirm",
            "--name", EXE_NAME,
            "--icon", str(INSTALLER_DIR / "ow_icon.ico"),
            "--distpath", str(DIST_DIR),
            "--workpath", str(BUILD_DIR / "pyinstaller"),
            "--specpath", str(BUILD_DIR),
            str(script),
        ],
        check=True,
    )


def write_mod_zip(mod_files):
    DIST_DIR.mkdir(exist_ok=True)
    with zipfile.ZipFile(DIST_DIR / MOD_ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in mod_files.items():
            zf.writestr(name, data)


def write_checksums():
    lines = []
    for path in sorted(DIST_DIR.iterdir()):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (DIST_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    mod_files = collect_mod_files()
    assets = collect_assets()
    for name, data in {**mod_files, **assets}.items():
        print(f"  {name}: {len(data):,} bytes")
    script = bundle({**mod_files, **assets})
    run_pyinstaller(script)
    write_mod_zip(mod_files)
    write_checksums()
    print(f"\nOutput in {DIST_DIR}")


if __name__ == "__main__":
    main()
