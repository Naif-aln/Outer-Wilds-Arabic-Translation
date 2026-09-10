import tkinter as tk
from tkinter import ttk, messagebox
import os, json, shutil, threading, urllib.request, zipfile, tempfile
import base64, io, subprocess, ctypes

MOD_FILES = {}

APPDATA         = os.environ.get("APPDATA", "")
LOCALAPPDATA    = os.environ.get("LOCALAPPDATA", "")

# Default OWML path - may be overridden if found elsewhere
OWML_ROOT       = os.path.join(APPDATA, "OuterWildsModManager", "OWML")
OWML_MODS       = os.path.join(OWML_ROOT, "Mods")
MOD_FOLDER      = os.path.join(OWML_MODS, "arabic.OWArabicTranslation")
POLYGLOT_FOLDER = os.path.join(OWML_MODS, "xen.LocalizationUtility")

# User-confirmed game path (set when user manually points to exe)
USER_GAME_PATH  = None

# Steam library root folders to search
STEAM_LIBRARY_ROOTS = [
    r"C:\Program Files (x86)\Steam",
    r"C:\Program Files\Steam",
    r"C:\Steam",
    r"C:\SteamLibrary",
    r"D:\Steam",
    r"D:\SteamLibrary",
    r"D:\Games",
    r"E:\Steam",
    r"E:\SteamLibrary",
    r"E:\Games",
]

def _ow_in_library(lib_root):
    """Check if Outer Wilds is installed in a Steam library root."""
    exe = os.path.join(lib_root, "steamapps", "common", "Outer Wilds", "OuterWilds.exe")
    return os.path.dirname(exe) if os.path.isfile(exe) else None

OWML_API     = "https://api.github.com/repos/ow-mods/owml/releases/latest"
POLYGLOT_API = "https://api.github.com/repos/xen-42/outer-wilds-localization-utility/releases/latest"
MOD_MAN_API  = "https://api.github.com/repos/ow-mods/ow-mod-man/releases/latest"

BG      = "#0d0d0f"
BG2     = "#13131a"
ORANGE  = "#e8a030"
ORANGE2 = "#c07818"
WHITE   = "#f0ead8"
GREY    = "#6a6a7a"
GREEN   = "#5cba6a"
RED     = "#c05050"
STAR    = "#d4c890"
WIN_W   = 700

_img_cache = {}

def resource(name):
    d = MOD_FILES.get(name, "")
    return base64.b64decode(d) if d else b""

def gif(name):
    if name in _img_cache:
        return _img_cache[name]
    raw = resource(name)
    if not raw: return None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".gif", delete=False)
        tmp.write(raw); tmp.close()
        img = tk.PhotoImage(file=tmp.name)
        _img_cache[name] = img
        try: os.unlink(tmp.name)
        except: pass
        return img
    except: return None

def fetch_zip_url(api_url):
    req = urllib.request.Request(api_url, headers={"User-Agent": "OWArabicInstaller"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    for a in data.get("assets", []):
        if a["name"].lower().endswith(".zip"):
            return a["browser_download_url"]
    return data.get("zipball_url")

def fetch_setup_url(api_url):
    """Get setup exe URL from GitHub releases."""
    req = urllib.request.Request(api_url, headers={"User-Agent": "OWArabicInstaller"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    for a in data.get("assets", []):
        name = a["name"].lower()
        if "setup" in name and name.endswith(".exe"):
            return a["browser_download_url"]
    return None

def download_and_extract(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "OWArabicInstaller"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(dest)

def _all_library_candidates():
    """Return every possible Steam library root to check, using every method available."""
    import re
    candidates = []

    # 1. Hardcoded common paths
    candidates.extend(STEAM_LIBRARY_ROOTS)

    # 2. Find Steam root via registry and add it + its libraries
    try:
        import winreg
        for hive, path, val in [
            (winreg.HKEY_CURRENT_USER,  r"Software\Valve\Steam",             "SteamPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam",             "InstallPath"),
        ]:
            try:
                k = winreg.OpenKey(hive, path)
                val_data, _ = winreg.QueryValueEx(k, val)
                winreg.CloseKey(k)
                # Normalize: forward slashes → backslashes, strip trailing slash
                steam_root = os.path.normpath(str(val_data))
                if os.path.isdir(steam_root):
                    candidates.append(steam_root)
                    # Read libraryfolders.vdf from both known locations
                    for vdf_rel in [r"steamapps\libraryfolders.vdf", r"config\libraryfolders.vdf"]:
                        vdf = os.path.join(steam_root, vdf_rel)
                        if not os.path.isfile(vdf):
                            continue
                        try:
                            text = open(vdf, encoding="utf-8", errors="ignore").read()
                            # New format: "path"  "D:\\SteamLibrary"
                            for m in re.finditer(r'"path"\s+"([^"]+)"', text):
                                candidates.append(os.path.normpath(m.group(1)))
                            # Old format: "1"  "D:\\path"
                            for m in re.finditer(r'"\d+"\s+"([A-Za-z]:[^"]+)"', text):
                                candidates.append(os.path.normpath(m.group(1)))
                        except: pass
                    break  # found Steam root, no need to check other registry keys
            except: pass
    except: pass

    # 3. Check every drive letter A-Z just in case (instant — only checks existence of one path)
    for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        for folder in ["Steam", "SteamLibrary", "Games", "Games\\Steam"]:
            candidates.append(os.path.join(f"{drive}:\\", folder))

    # Deduplicate preserving order
    seen = set()
    result = []
    for c in candidates:
        n = c.upper()
        if n not in seen:
            seen.add(n)
            result.append(c)
    return result


def find_game_exe():
    """Find Outer Wilds installation folder."""
    global USER_GAME_PATH
    import re

    # 1. User manually pointed to it
    if USER_GAME_PATH and os.path.isfile(os.path.join(USER_GAME_PATH, "OuterWilds.exe")):
        return USER_GAME_PATH

    # 2. Check every candidate library root
    for lib in _all_library_candidates():
        steamapps = os.path.join(lib, "steamapps")
        if not os.path.isdir(steamapps):
            continue
        # Best: use appmanifest to get exact install folder name
        acf = os.path.join(steamapps, "appmanifest_753640.acf")
        if os.path.isfile(acf):
            try:
                text = open(acf, encoding="utf-8", errors="ignore").read()
                m = re.search(r'"installdir"\s+"([^"]+)"', text)
                if m:
                    game_dir = os.path.join(steamapps, "common", m.group(1))
                    if os.path.isfile(os.path.join(game_dir, "OuterWilds.exe")):
                        return game_dir
            except: pass
        # Fallback: just check the expected folder name directly
        game_dir = os.path.join(steamapps, "common", "Outer Wilds")
        if os.path.isfile(os.path.join(game_dir, "OuterWilds.exe")):
            return game_dir

    return None


def find_owml_exe():
    """Search for OWML.Launcher.exe and return its folder, or None."""
    if os.path.isfile(os.path.join(OWML_ROOT, "OWML.Launcher.exe")):
        return OWML_ROOT
    for base in [APPDATA, LOCALAPPDATA,
                 os.environ.get("PROGRAMFILES",""),
                 os.environ.get("PROGRAMFILES(X86)","")]:
        for name in ["OuterWildsModManager\\OWML", "OWML"]:
            candidate = os.path.join(base, name)
            if os.path.isfile(os.path.join(candidate, "OWML.Launcher.exe")):
                return candidate
    return None

def check_game():
    return find_game_exe() is not None

def check_modman():
    candidates = [
        os.path.join(LOCALAPPDATA, "Programs", "outer-wilds-mod-manager", "Outer Wilds Mod Manager.exe"),
        os.path.join(LOCALAPPDATA, "Programs", "OWModManager", "Outer Wilds Mod Manager.exe"),
        os.path.join(APPDATA, "OuterWildsModManager", "OuterWildsModManager.exe"),
        r"C:\Program Files\Outer Wilds Mod Manager\Outer Wilds Mod Manager.exe",
        r"C:\Program Files (x86)\Outer Wilds Mod Manager\Outer Wilds Mod Manager.exe",
    ]
    for path in candidates:
        if os.path.isfile(path): return True
    for base in [os.environ.get("PROGRAMFILES",""), os.environ.get("PROGRAMFILES(X86)",""),
                 os.environ.get("LOCALAPPDATA",""), os.environ.get("APPDATA","")]:
        for name in ["Outer Wilds Mod Manager", "OuterWildsModManager", "ow-mod-man"]:
            if os.path.isfile(os.path.join(base, name, "Outer Wilds Mod Manager.exe")):
                return True
    return False

def check_owml():
    return find_owml_exe() is not None

def get_owml_mods_path():
    owml = find_owml_exe()
    return os.path.join(owml, "Mods") if owml else OWML_MODS

def check_polyglot():
    return os.path.isdir(os.path.join(get_owml_mods_path(), "xen.LocalizationUtility"))

def check_mod():
    return os.path.isfile(os.path.join(get_owml_mods_path(),
                          "arabic.OWArabicTranslation", "ArabicTranslation.dll"))



class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Outer Wilds - Arabic Translation")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._set_icon()
        self._build_ui()
        self.after(200, self._run_checks)

    def _set_icon(self):
        data = MOD_FILES.get("app_icon")
        if data:
            try:
                raw = base64.b64decode(data)
                tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
                tmp.write(raw); tmp.close()
                self.iconbitmap(tmp.name)
                self.after(3000, lambda: os.unlink(tmp.name))
            except: pass

    def _build_ui(self):
        logo_h = gif("ow_logo").height() if gif("ow_logo") else 0
        title_h = gif("txt_title").height() if gif("txt_title") else 0
        sub_h   = gif("txt_sub").height() if gif("txt_sub") else 0
        sec_h   = gif("txt_sec").height() if gif("txt_sec") else 0
        row_h   = max(gif("txt_game").height() if gif("txt_game") else 0, 30)

        PAD = 10; DIV = 14; BTN_H = 50; PROG = 46; FOOT = 46
        rows = [("game","txt_game"),("owml","txt_owml"),("polyglot","txt_polyglot"),("mod","txt_mod")]
        self._win_h = (PAD + logo_h + PAD + title_h + sub_h + PAD +
                       DIV + sec_h + len(rows)*(row_h+8) + DIV +
                       PAD + BTN_H + PROG + FOOT + 20)
        self.geometry(f"{WIN_W}x{self._win_h}")

        c = tk.Canvas(self, width=WIN_W, height=self._win_h, bg=BG, highlightthickness=0)
        c.place(x=0, y=0); self._canvas = c
        self._draw_stars()

        cx = WIN_W//2; y = PAD
        if gif("ow_logo"):
            c.create_image(cx, y, anchor="n", image=gif("ow_logo")); y += logo_h + PAD
        if gif("txt_title"):
            c.create_image(cx, y, anchor="n", image=gif("txt_title")); y += title_h + 2
        if gif("txt_sub"):
            c.create_image(cx, y, anchor="n", image=gif("txt_sub")); y += sub_h + PAD

        c.create_line(60, y, 640, y, fill=ORANGE2, width=1); y += DIV
        if gif("txt_sec"):
            c.create_image(640, y, anchor="ne", image=gif("txt_sec")); y += sec_h + 4

        self.status_vars = {}
        for key, txt_key in rows:
            if gif(txt_key): c.create_image(636, y, anchor="ne", image=gif(txt_key))
            var = tk.StringVar(value="⏳")
            self.status_vars[key] = var
            lbl = tk.Label(self, textvariable=var, bg=BG, font=("Segoe UI",10),
                           fg=GREY, anchor="w", justify="left", width=20)
            lbl.place(x=62, y=y+2)
            setattr(self, f"lbl_{key}", lbl)
            y += row_h + 8

        c.create_line(60, y, 640, y, fill=ORANGE2, width=1); y += DIV + PAD
        self.btn = tk.Button(self, text="تثبيت الترجمة",
            font=("Segoe UI",15,"bold"), fg=BG, bg=ORANGE,
            activebackground=ORANGE2, activeforeground=BG,
            relief="flat", cursor="hand2", bd=0, command=self._start_install)
        self.btn.place(x=cx, y=y, anchor="n", width=260, height=BTN_H); y += BTN_H + 10

        self.progress_var = tk.DoubleVar()
        s = ttk.Style(self); s.theme_use("clam")
        s.configure("OW.Horizontal.TProgressbar",
            troughcolor=BG2, background=ORANGE,
            bordercolor=BG2, lightcolor=ORANGE, darkcolor=ORANGE2)
        self.pb = ttk.Progressbar(self, variable=self.progress_var,
            style="OW.Horizontal.TProgressbar",
            orient="horizontal", length=580, mode="determinate")
        self.pb.place(x=60, y=y); y += 22

        self.status_text = tk.StringVar(value="")
        tk.Label(self, textvariable=self.status_text, bg=BG, fg=GREY,
            font=("Segoe UI",10), anchor="e", justify="right").place(
            x=638, y=y, anchor="ne", width=578)

        self._img_y = y + 24
        self.img_frame = tk.Frame(self, bg=BG)
        self.img_frame.place(x=0, y=self._img_y, width=WIN_W, height=0)

        footer_y = self._win_h - 28
        c.create_line(60, footer_y-12, 640, footer_y-12, fill=ORANGE2, width=1)
        c.create_text(cx, footer_y, anchor="center",
            text="IHB  ✦  Outer Wilds Arabic Translation",
            font=("Georgia",10,"italic"), fill=GREY)

    def _draw_stars(self):
        import random; random.seed(42)
        for _ in range(130):
            x = random.randint(0, WIN_W); y = random.randint(0, self._win_h)
            r = random.choice([0.5,0.5,0.5,1,1,1.5])
            c = random.choice([GREY,STAR,WHITE])
            self._canvas.create_oval(x-r,y-r,x+r,y+r,fill=c,outline="")

    def _run_checks(self):
        def do():
            checks = {
                "game":     check_game(),
                "owml":     check_owml(),
                "polyglot": check_polyglot(),
                "mod":      check_mod(),
            }
            self.after(0, lambda: self._update_checks(checks))
        threading.Thread(target=do, daemon=True).start()

    def _update_checks(self, checks):
        for key, ok in checks.items():
            lbl = getattr(self, f"lbl_{key}")
            if ok:
                self.status_vars[key].set("✔  مثبّت"); lbl.configure(fg=GREEN)
            else:
                self.status_vars[key].set("✘  غير مثبّت"); lbl.configure(fg=RED)

    def _start_install(self):
        global USER_GAME_PATH
        if not check_game():
            answer = messagebox.askyesno("اللعبة غير موجودة",
                "لم يتم العثور على Outer Wilds تلقائيا.\n\n"
                "هل لديك اللعبة مثبتة؟ (Epic, Steam, إلخ)")
            if answer:
                # Let user point to the exe
                from tkinter import filedialog
                path = filedialog.askopenfilename(
                    title="اختر Outer Wilds.exe",
                    filetypes=[("Outer Wilds", "OuterWilds.exe"), ("All", "*.*")])
                if path and os.path.isfile(path):
                    USER_GAME_PATH = os.path.dirname(path)
                    self._run_checks()  # refresh checks
                else:
                    messagebox.showinfo("تنبيه", "لم يتم تحديد اللعبة. يمكنك المتابعة لتثبيت باقي المتطلبات.")
            else:
                messagebox.showinfo("تنبيه",
                    "ثبّت اللعبة أولاً من Steam أو Epic:\n"
                    "store.steampowered.com/app/753640\n\n"
                    "ثم أعد تشغيل البرنامج.")
                return
        self.btn.configure(state="disabled", text="جاري التثبيت...")
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _set_status(self, msg, pct=None):
        self.after(0, lambda: self.status_text.set(msg))
        if pct is not None:
            self.after(0, lambda: self.progress_var.set(pct))

    def _install_worker(self):
        try:
            # Step 1: Mod Manager
            if not check_modman():
                self._set_status("⬇  جاري تنزيل Outer Wilds Mod Manager...", 3)
                setup_url = fetch_setup_url(MOD_MAN_API)
                if setup_url:
                    req = urllib.request.Request(setup_url, headers={"User-Agent":"OWArabicInstaller"})
                    with urllib.request.urlopen(req, timeout=120) as r:
                        setup_data = r.read()
                    tmp = tempfile.NamedTemporaryFile(suffix=".exe", delete=False)
                    tmp.write(setup_data); tmp.close()
                    self._set_status("⚙  جاري تثبيت Mod Manager...", 8)
                    # Run with elevation
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", tmp.name, "/S", None, 1)
                    import time
                    for _ in range(30):
                        time.sleep(2)
                        if check_modman(): break
                    try: os.unlink(tmp.name)
                    except: pass
                self._set_status("✔  Mod Manager", 12)
            else:
                self._set_status("✔  Mod Manager موجود", 12)

            # Step 2: OWML
            if not check_owml():
                self._set_status("⬇  جاري تنزيل OWML...", 15)
                url = fetch_zip_url(OWML_API)
                tmp = tempfile.mkdtemp()
                download_and_extract(url, tmp)
                owml_src = None
                for root, dirs, files in os.walk(tmp):
                    if "OWML.Launcher.exe" in files:
                        owml_src = root; break
                if owml_src:
                    if os.path.isdir(OWML_ROOT): shutil.rmtree(OWML_ROOT)
                    os.makedirs(OWML_ROOT)
                    for item in os.listdir(owml_src):
                        s = os.path.join(owml_src, item)
                        d = os.path.join(OWML_ROOT, item)
                        if os.path.isdir(s): shutil.copytree(s, d)
                        else: shutil.copy2(s, d)
                shutil.rmtree(tmp, ignore_errors=True)
                self._set_status("✔  تم تثبيت OWML", 35)
            else:
                self._set_status("✔  OWML موجود", 35)

            # Step 3: Polyglot
            if not check_polyglot():
                self._set_status("⬇  جاري تنزيل Interplanetary Polyglot...", 40)
                url = fetch_zip_url(POLYGLOT_API)
                tmp = tempfile.mkdtemp()
                download_and_extract(url, tmp)
                os.makedirs(POLYGLOT_FOLDER, exist_ok=True)
                for root, dirs, files in os.walk(tmp):
                    for f in files:
                        shutil.copy2(os.path.join(root, f),
                                     os.path.join(POLYGLOT_FOLDER, f))
                shutil.rmtree(tmp, ignore_errors=True)
                self._set_status("✔  تم تثبيت Polyglot", 65)
            else:
                self._set_status("✔  Polyglot موجود", 65)

            # Step 4: Mod files (always overwrite for updates)
            self._set_status("📦  جاري نسخ ملفات الترجمة...", 70)
            mods_path = get_owml_mods_path()
            mod_dest  = os.path.join(mods_path, "arabic.OWArabicTranslation")
            poly_dest = os.path.join(mods_path, "xen.LocalizationUtility")
            os.makedirs(mod_dest, exist_ok=True)
            skip = {k for k in MOD_FILES if k.startswith("txt_") or
                    k in {"step1_img","step2_img","app_icon","ow_logo"}}
            for fname, b64data in MOD_FILES.items():
                if fname in skip: continue
                dest = os.path.join(mod_dest, fname)
                with open(dest, "wb") as f:
                    f.write(base64.b64decode(b64data))

            self._set_status("🎉  اكتمل التثبيت!", 100)
            self.after(0, self._show_success)

        except Exception as e:
            self._set_status(f"خطأ: {e}")
            self.after(0, lambda: messagebox.showerror("خطأ", f"فشل التثبيت:\n{e}"))
            self.after(0, lambda: self.btn.configure(
                state="normal", text="إعادة المحاولة"))

    def _show_success(self):
        self._run_checks()
        self.btn.configure(state="normal", text="✔  تم التثبيت", bg=GREEN)
        self.after(600, self._open_instructions)
        extra = 60
        new_h = self._win_h + extra
        self.geometry(f"{WIN_W}x{new_h}")
        self.canvas_update_height(new_h)
        self.img_frame.place_configure(height=extra)
        tk.Label(self.img_frame,
            text="اكتملت الترجمة! ستفتح نافذة التعليمات الآن — يمكنك إغلاق هذه النافذة",
            font=("Segoe UI",10), fg=GREEN, bg=BG,
            justify="center", wraplength=580).pack(pady=18)

    def canvas_update_height(self, new_h):
        self._canvas.configure(height=new_h)
        footer_y = new_h - 28
        self._canvas.create_line(60, footer_y-12, 640, footer_y-12, fill=ORANGE2, width=1)
        self._canvas.create_text(WIN_W//2, footer_y, anchor="center",
            text="IHB  ✦  Outer Wilds Arabic Translation",
            font=("Georgia",10,"italic"), fill=GREY)

    def _open_instructions(self):
        win = tk.Toplevel(self)
        win.title("Outer Wilds - كيفية التشغيل")
        win.configure(bg=BG); win.resizable(False, False)
        data = MOD_FILES.get("app_icon")
        if data:
            try:
                raw = base64.b64decode(data)
                tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
                tmp.write(raw); tmp.close()
                win.iconbitmap(tmp.name)
                win.after(3000, lambda: os.unlink(tmp.name))
            except: pass

        how_h   = gif("txt_how").height()   if gif("txt_how")   else 0
        s1_h    = gif("txt_step1").height() if gif("txt_step1") else 0
        s2_h    = gif("txt_step2").height() if gif("txt_step2") else 0
        img1_h  = gif("step1_img").height() if gif("step1_img") else 0
        img2_h  = gif("step2_img").height() if gif("step2_img") else 0

        total_h = 20 + how_h + 16 + 16 + s1_h + 8 + img1_h + 16 + 16 + s2_h + 8 + img2_h + 20 + 36
        win.geometry(f"{WIN_W}x{total_h}")
        c = tk.Canvas(win, width=WIN_W, height=total_h, bg=BG, highlightthickness=0)
        c.pack()

        import random; random.seed(77)
        for _ in range(80):
            x = random.randint(0,WIN_W); y = random.randint(0,total_h)
            r = random.choice([0.5,0.5,1])
            col = random.choice([GREY,STAR,WHITE])
            c.create_oval(x-r,y-r,x+r,y+r,fill=col,outline="")

        cx = WIN_W//2; y = 20
        if gif("txt_how"):
            c.create_image(cx, y, anchor="n", image=gif("txt_how")); y += how_h + 16
        c.create_line(60, y, 640, y, fill=ORANGE2, width=1); y += 16
        if gif("txt_step1"):
            c.create_image(cx, y, anchor="n", image=gif("txt_step1")); y += s1_h + 8
        if gif("step1_img"):
            c.create_image(cx, y, anchor="n", image=gif("step1_img")); y += img1_h + 16
        c.create_line(60, y, 640, y, fill=ORANGE2, width=1); y += 16
        if gif("txt_step2"):
            c.create_image(cx, y, anchor="n", image=gif("txt_step2")); y += s2_h + 8
        if gif("step2_img"):
            c.create_image(cx, y, anchor="n", image=gif("step2_img")); y += img2_h + 20
        c.create_line(60, y, 640, y, fill=ORANGE2, width=1); y += 12
        c.create_text(cx, y, anchor="n",
            text="IHB  ✦  Outer Wilds Arabic Translation",
            font=("Georgia",10,"italic"), fill=GREY)
        win.lift(); win.focus_force()


if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
