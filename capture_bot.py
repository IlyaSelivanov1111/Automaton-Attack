import tkinter as tk
from tkinter import ttk
import threading
import time
import queue
import warnings
import json
import os
import re
import difflib

import mss
import numpy as np
import cv2
import pytesseract
import keyboard

warnings.filterwarnings("ignore", category=DeprecationWarning, module="mss")

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

OCR_CONFIG = "--oem 1 --psm 11"

CONF_THRESHOLD = 35
COOLDOWN_SEC = 0.7
START_HOTKEY = "f8"
STOP_HOTKEY = "f9"
SELECT_REGION_HOTKEY = "ctrl+shift+r"
MAX_LOG_LINES = 200

MAX_SCALE = 2.0
MIN_SCALE = 1.0
SCALE_STEP = 0.25
TARGET_MAX_MS = 130
TARGET_MIN_MS = 55

BRIGHTNESS_THRESH = 90

GREY_V_MAX = 150
GREY_S_MAX = 60
YELLOW_H_MIN = 18
YELLOW_H_MAX = 40
YELLOW_S_MIN = 90

MIN_PHRASE_LEN = 3

FUZZY_MATCH_CUTOFF = 0.75
MIN_CONFIDENCE_NEW_WORD = 65
LEARNED_TRUST_MIN = 3
MAX_TRAILING_GAP = 3
WORDS_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "learned_words.json")
DB_SAVE_INTERVAL = 3.0

ONLY_LATIN_RE = re.compile(r"^[a-z][a-z ]*$")

SEED_TERMS = [
    "abaddon", "alchemist", "axe", "anti mage", "arc warden", "bane",
    "batrider", "beastmaster", "bloodseeker", "bounty hunter", "brewmaster",
    "bristleback", "broodmother", "centaur warrunner", "chaos knight",
    "chen", "clinkz", "clockwerk", "crystal maiden", "dark seer",
    "dark willow", "dawnbreaker", "dazzle", "death prophet", "disruptor",
    "doom", "dragon knight", "drow ranger", "earth spirit", "earthshaker",
    "elder titan", "ember spirit", "enchantress", "enigma", "faceless void",
    "grimstroke", "gyrocopter", "hoodwink", "huskar", "invoker", "io",
    "jakiro", "juggernaut", "keeper of the light", "kunkka", "legion commander",
    "leshrac", "lich", "lifestealer", "lina", "lion", "lone druid",
    "luna", "lycan", "magnus", "marci", "mars", "medusa", "meepo",
    "mirana", "monkey king", "morphling", "muerta", "naga siren",
    "natures prophet", "necrophos", "night stalker", "nyx assassin",
    "ogre magi", "omniknight", "oracle", "outworld destroyer", "pangolier",
    "phantom assassin", "phantom lancer", "phoenix", "primal beast",
    "puck", "pudge", "pugna", "queen of pain", "razor", "riki", "rubick",
    "sand king", "shadow demon", "shadow fiend", "shadow shaman",
    "silencer", "skywrath mage", "slardar", "slark", "snapfire", "sniper",
    "spectre", "spirit breaker", "storm spirit", "sven", "techies",
    "templar assassin", "terrorblade", "tidehunter", "timbersaw", "tinker",
    "tiny", "treant protector", "troll warlord", "tusk", "underlord",
    "undying", "ursa", "vengeful spirit", "venomancer", "viper", "visage",
    "void spirit", "warlock", "weaver", "windranger", "winter wyvern",
    "witch doctor", "wraith king", "zeus",
    "abyssal blade", "aeon disk", "aether lens", "aghanims scepter",
    "aghanims shard", "arcane boots", "armlet", "assault cuirass",
    "bfury", "basher", "basilius", "belt of strength", "black king bar",
    "blade mail", "blade of alacrity", "blight stone", "blink dagger",
    "blitz knuckles", "blood grenade", "bloodthorn", "boots of speed",
    "bottle", "bracer", "branch", "broadsword", "buckler", "butterfly",
    "cape", "chainmail", "cheese", "circlet", "cloak", "crimson guard",
    "cuirass", "daedalus", "dagon", "desolator", "diadem", "diffusal blade",
    "divine rapier", "dragon lance", "eaglesong", "echo sabre",
    "essence ring", "eternal shroud", "eul", "eye of skadi", "faerie fire",
    "falcon blade", "force staff", "gauntlets of strength", "ghost scepter",
    "giants ring", "gleipnir", "glimmer cape", "gloves of haste",
    "guardian greaves", "hand of midas", "harpoon", "headdress",
    "healing salve", "heart of tarrasque", "helm of iron will",
    "helm of the dominator", "helm of the overlord", "hood of defiance",
    "hurricane pike", "hyperstone", "infused raindrop", "iron branch",
    "javelin", "kaya", "khanda", "lesser crit", "linkens sphere",
    "lotus orb", "maelstrom", "magic stick", "magic wand", "mango",
    "manta style", "mask of madness", "meteor hammer", "mjollnir",
    "moon shard", "morbid mask", "necronomicon", "null talisman",
    "nullifier", "oblivion staff", "octarine core", "ogre axe",
    "orb of corrosion", "orb of venom", "overwhelming blink",
    "pavise", "perseverance", "phase boots", "phylactery",
    "pipe of insight", "platemail", "point booster", "power treads",
    "quarterstaff", "quelling blade", "radiance", "ring of aquila",
    "ring of basilius", "ring of health", "ring of protection",
    "ring of regen", "robe of the magi", "rod of atos", "sacred relic",
    "sages mask", "sange", "satanic", "sentry ward", "shadow amulet",
    "shadow blade", "silver edge", "skull basher", "smoke of deceit",
    "solar crest", "soul booster", "soul ring", "spirit vessel",
    "stout shield", "tango", "talisman of evasion", "tango single",
    "tarrasque", "tome of knowledge", "tranquil boots", "travel boots",
    "ultimate orb", "urn of shadows", "vanguard", "veil of discord",
    "vitality booster", "void stone", "voodoo mask", "wind lace",
    "wraith band", "yasha", "aghanims blessing", "refresher orb",
    "refresher shard", "moonshard", "iron talon",
]


def _clean_learned(raw):
    cleaned = {}
    for k, v in (raw or {}).items():
        key = k.strip().lower()
        if ONLY_LATIN_RE.match(key) and len(key.replace(" ", "")) >= MIN_PHRASE_LEN:
            cleaned[key] = max(cleaned.get(key, 0), int(v) if isinstance(v, (int, float)) else 1)
    return cleaned


def load_dictionary():
    learned = {}
    if os.path.exists(WORDS_DB_PATH):
        try:
            with open(WORDS_DB_PATH, "r", encoding="utf-8") as f:
                learned = _clean_learned(json.load(f))
        except Exception:
            learned = {}
    return learned


def save_dictionary(d):
    try:
        with open(WORDS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception:
        pass


class RegionSelector:
    def __init__(self, parent):
        self.region = None

        win = tk.Toplevel(parent)
        win.attributes("-fullscreen", True)
        win.attributes("-alpha", 0.25)
        win.attributes("-topmost", True)
        win.configure(bg="black")
        win.config(cursor="cross")
        win.grab_set()
        win.focus_force()

        canvas = tk.Canvas(win, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self.start_x = self.start_y = 0
        self.rect_id = None

        def on_press(event):
            self.start_x, self.start_y = event.x_root, event.y_root
            self.rect_id = canvas.create_rectangle(
                event.x, event.y, event.x, event.y, outline="#34d399", width=2
            )

        def on_drag(event):
            canvas.coords(
                self.rect_id,
                self.start_x - win.winfo_rootx(), self.start_y - win.winfo_rooty(),
                event.x, event.y,
            )

        def on_release(event):
            end_x, end_y = event.x_root, event.y_root
            x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
            x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
            self.region = {
                "left": int(x1), "top": int(y1),
                "width": int(x2 - x1), "height": int(y2 - y1),
            }
            win.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        win.bind("<Escape>", lambda e: win.destroy())

        parent.wait_window(win)


class CaptureBot:
    def __init__(self, region, log_queue, learned_db):
        self.region = region
        self.log_queue = log_queue
        self.running = False

        self.capture_thread = None
        self.ocr_thread = None

        self.frame_lock = threading.Lock()
        self.latest_frame = None
        self.latest_frame_id = 0
        self.last_processed_id = -1

        self.learned_db = learned_db
        self.db_dirty = False
        self.typed_recent = {}

        self.current_scale = MAX_SCALE
        self.ocr_ms_ema = None

        self.capture_count = 0
        self.ocr_count = 0
        self.last_metric_time = time.time()

    def _trusted_words(self):
        trusted = set(SEED_TERMS)
        for w, c in self.learned_db.items():
            if c >= LEARNED_TRUST_MIN:
                trusted.add(w)
        return trusted

    def start(self):
        if self.running:
            return
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.ocr_thread = threading.Thread(target=self._ocr_loop, daemon=True)
        self.capture_thread.start()
        self.ocr_thread.start()

    def stop(self):
        self.running = False
        if self.db_dirty:
            save_dictionary(self.learned_db)
            self.db_dirty = False

    def _log(self, msg, tag="info"):
        print(msg)
        try:
            self.log_queue.put_nowait((msg, tag))
        except queue.Full:
            pass

    def _capture_loop(self):
        with mss.MSS() as sct:
            while self.running:
                frame = np.array(sct.grab(self.region))
                with self.frame_lock:
                    self.latest_frame = frame
                    self.latest_frame_id += 1
                self.capture_count += 1
                self._maybe_report_fps()

    def _preprocess(self, frame_bgra, scale):
        bgr = frame_bgra[:, :, :3]
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        v = hsv[:, :, 2]

        if scale != 1:
            v = cv2.resize(v, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        _, mask = cv2.threshold(v, BRIGHTNESS_THRESH, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)

        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(mask_inv, cv2.MORPH_CLOSE, kernel)
        return cleaned

    def _get_phrases(self, img):
        data = pytesseract.image_to_data(
            img, output_type=pytesseract.Output.DICT, config=OCR_CONFIG
        )
        lines = {}
        n = len(data["text"])
        for i in range(n):
            text = data["text"][i].strip()
            if not text:
                continue
            try:
                conf = float(data["conf"][i])
            except ValueError:
                conf = -1
            if conf < CONF_THRESHOLD:
                continue
            if not all(ch.isalpha() for ch in text):
                continue

            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            lines.setdefault(key, []).append({
                "text": text.lower(),
                "conf": conf,
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
            })

        phrases = []
        for toks in lines.values():
            toks.sort(key=lambda t: t["left"])
            phrase_text = " ".join(t["text"] for t in toks)
            if len(phrase_text.replace(" ", "")) < MIN_PHRASE_LEN:
                continue
            avg_conf = sum(t["conf"] for t in toks) / len(toks)
            top_y = min(t["top"] for t in toks)

            rx1 = min(t["left"] for t in toks)
            ry1 = min(t["top"] for t in toks)
            rx2 = max(t["left"] + t["width"] for t in toks)
            ry2 = max(t["top"] + t["height"] for t in toks)

            phrases.append({
                "text": phrase_text,
                "conf": avg_conf,
                "y": top_y,
                "rect": (rx1, ry1, rx2 - rx1, ry2 - ry1),
            })

        return phrases

    def _char_state(self, h, s, v):
        if v < GREY_V_MAX and s < GREY_S_MAX:
            return "typed"
        if YELLOW_H_MIN <= h <= YELLOW_H_MAX and s >= YELLOW_S_MIN:
            return "current"
        return "pending"

    def _progress_offset(self, frame_bgra, mask, rect, scale, expected_len):
        x, y, w, h = rect
        if w <= 0 or h <= 0:
            return 0

        crop_mask = mask[y:y + h, x:x + w]
        if crop_mask.size == 0:
            return 0

        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(crop_mask, connectivity=8)
        letters = []
        for i in range(1, num_labels):
            lx, ly, lw, lh, area = stats[i]
            if area < 3:
                continue
            letters.append((lx, ly, lw, lh))
        letters.sort(key=lambda b: b[0])

        if len(letters) != expected_len:
            return 0

        bgr = frame_bgra[:, :, :3]
        hsv_full = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        max_y_px, max_x_px = hsv_full.shape[0], hsv_full.shape[1]

        first_not_typed = 0
        found = False
        for idx, (lx, ly, lw, lh) in enumerate(letters):
            ox = int((x + lx + lw / 2) / scale)
            oy = int((y + ly + lh / 2) / scale)
            ox = min(max(ox, 0), max_x_px - 1)
            oy = min(max(oy, 0), max_y_px - 1)
            hh, ss, vv = hsv_full[oy, ox]
            state = self._char_state(int(hh), int(ss), int(vv))
            if state != "typed":
                first_not_typed = idx
                found = True
                break

        if not found:
            first_not_typed = len(letters)

        return first_not_typed

    def _complete_if_truncated(self, raw_text, trusted):
        best = None
        best_gap = None
        for word in trusted:
            if word == raw_text:
                continue
            if word.startswith(raw_text):
                gap = len(word) - len(raw_text)
                if 0 < gap <= MAX_TRAILING_GAP:
                    if best_gap is None or gap < best_gap:
                        best, best_gap = word, gap
        return best

    def _resolve_phrase(self, raw_text, conf):
        trusted = self._trusted_words()

        if raw_text in trusted:
            return raw_text, "точное совпадение (доверенное)", True

        completed = self._complete_if_truncated(raw_text, trusted)
        if completed:
            return completed, f"дополнено ({raw_text} -> {completed})", True

        candidates = difflib.get_close_matches(raw_text, trusted, n=1, cutoff=FUZZY_MATCH_CUTOFF)
        if candidates:
            return candidates[0], f"исправлено ({raw_text} -> {candidates[0]})", True

        if conf >= MIN_CONFIDENCE_NEW_WORD and ONLY_LATIN_RE.match(raw_text):
            return raw_text, "новая фраза, добавлена в черновой словарь", True

        return raw_text, "неуверенно, ввёл как есть", False

    def _ocr_loop(self):
        last_clean = time.time()
        while self.running:
            with self.frame_lock:
                frame = self.latest_frame
                frame_id = self.latest_frame_id

            if frame is None or frame_id == self.last_processed_id:
                time.sleep(0.001)
                continue

            self.last_processed_id = frame_id
            t0 = time.time()

            processed = self._preprocess(frame, self.current_scale)
            phrases = self._get_phrases(processed)

            ocr_ms = (time.time() - t0) * 1000
            self._adapt_scale(ocr_ms)

            phrases.sort(key=lambda p: -p["y"])

            now = time.time()
            for ph in phrases:
                final_text, status, should_learn = self._resolve_phrase(ph["text"], ph["conf"])

                last_typed = self.typed_recent.get(final_text, 0)
                if now - last_typed < COOLDOWN_SEC:
                    continue

                letters_only = ph["text"].replace(" ", "")
                offset = self._progress_offset(
                    frame, processed, ph["rect"], self.current_scale, len(letters_only)
                )

                final_letters_only = final_text.replace(" ", "")
                if final_letters_only != letters_only:
                    offset = 0

                if offset >= len(letters_only) and final_letters_only == letters_only:
                    self.typed_recent[final_text] = now
                    continue

                to_type = final_text if offset == 0 else final_letters_only[offset:]

                keyboard.write(to_type)
                self.typed_recent[final_text] = now

                if should_learn and final_text not in SEED_TERMS:
                    self.learned_db[final_text] = self.learned_db.get(final_text, 0) + 1
                    self.db_dirty = True

                extra = "" if offset == 0 else f" | остаток с буквы {offset + 1}"
                self._log(
                    f"'{to_type}' (фраза: '{final_text}') | {status} | conf {ph['conf']:.0f}%{extra}",
                    tag="input",
                )

            if now - last_clean > DB_SAVE_INTERVAL:
                cutoff = now - COOLDOWN_SEC * 3
                self.typed_recent = {k: v for k, v in self.typed_recent.items() if v > cutoff}
                if self.db_dirty:
                    save_dictionary(self.learned_db)
                    self.db_dirty = False
                last_clean = now

            self.ocr_count += 1

    def _adapt_scale(self, ocr_ms):
        self.ocr_ms_ema = ocr_ms if self.ocr_ms_ema is None else 0.3 * ocr_ms + 0.7 * self.ocr_ms_ema

        if self.ocr_ms_ema > TARGET_MAX_MS and self.current_scale > MIN_SCALE:
            old = self.current_scale
            self.current_scale = max(MIN_SCALE, round(self.current_scale - SCALE_STEP, 2))
            if self.current_scale != old:
                self._log(f"нагрузка высокая -> масштаб {old} -> {self.current_scale}", tag="adapt")
        elif self.ocr_ms_ema < TARGET_MIN_MS and self.current_scale < MAX_SCALE:
            old = self.current_scale
            self.current_scale = min(MAX_SCALE, round(self.current_scale + SCALE_STEP, 2))
            if self.current_scale != old:
                self._log(f"нагрузка спала -> масштаб {old} -> {self.current_scale}", tag="adapt")

    def _maybe_report_fps(self):
        now = time.time()
        if now - self.last_metric_time >= 1.0:
            cap_fps = self.capture_count / (now - self.last_metric_time)
            ocr_fps = self.ocr_count / (now - self.last_metric_time)
            self._log(
                f"захват {cap_fps:.1f} fps | распознавание {ocr_fps:.1f} fps | масштаб {self.current_scale}",
                tag="metric",
            )
            self.capture_count = 0
            self.ocr_count = 0
            self.last_metric_time = now


COLOR_BG = "#12141c"
COLOR_PANEL = "#1a1d29"
COLOR_PANEL_ALT = "#212537"
COLOR_TEXT = "#e6e8f0"
COLOR_SUBTEXT = "#8a8fa3"
COLOR_ACCENT = "#34d399"
COLOR_ACCENT_DARK = "#1f9d73"
COLOR_DANGER = "#f2545b"
COLOR_DANGER_DARK = "#c23941"
COLOR_GOLD = "#f2c14e"
COLOR_BORDER = "#2a2e3f"


class ControlPanel:
    def __init__(self):
        self.bot = None
        self.region = None
        self.log_queue = queue.Queue(maxsize=1000)
        self.learned_db = load_dictionary()
        self.running = False

        self.root = tk.Tk()
        self.root.title("Word Capture Bot")
        self.root.attributes("-topmost", True)
        self.root.geometry("520x560")
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(460, 480)

        self._setup_style()
        self._build_ui()

        keyboard.add_hotkey(START_HOTKEY, self._hotkey_start)
        keyboard.add_hotkey(STOP_HOTKEY, self._hotkey_stop)
        keyboard.add_hotkey(SELECT_REGION_HOTKEY, self.select_region)

        self._poll_log_queue()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _setup_style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("TFrame", background=COLOR_BG)
        style.configure("Panel.TFrame", background=COLOR_PANEL)

        style.configure(
            "TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=("Segoe UI", 10)
        )
        style.configure(
            "Panel.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT, font=("Segoe UI", 10)
        )
        style.configure(
            "Sub.TLabel", background=COLOR_BG, foreground=COLOR_SUBTEXT, font=("Segoe UI", 9)
        )
        style.configure(
            "SubPanel.TLabel", background=COLOR_PANEL, foreground=COLOR_SUBTEXT, font=("Segoe UI", 9)
        )
        style.configure(
            "Title.TLabel",
            background=COLOR_BG, foreground=COLOR_TEXT, font=("Segoe UI Semibold", 16),
        )
        style.configure(
            "Status.TLabel", background=COLOR_BG, foreground=COLOR_ACCENT, font=("Segoe UI", 11, "bold")
        )

        for name, base, active, fg in [
            ("Accent.TButton", COLOR_ACCENT, COLOR_ACCENT_DARK, "#08130d"),
            ("Danger.TButton", COLOR_DANGER, COLOR_DANGER_DARK, "#2a0b0d"),
            ("Neutral.TButton", COLOR_PANEL_ALT, COLOR_BORDER, COLOR_TEXT),
        ]:
            style.configure(
                name, background=base, foreground=fg, font=("Segoe UI Semibold", 10),
                borderwidth=0, focusthickness=0, padding=(10, 8),
            )
            style.map(name, background=[("active", active), ("disabled", "#3a3d4a")],
                      foreground=[("disabled", "#7a7d8a")])

    def _build_ui(self):
        root = self.root

        header = ttk.Frame(root, style="TFrame")
        header.pack(fill="x", padx=18, pady=(16, 8))

        ttk.Label(header, text="Word Capture Bot", style="Title.TLabel").pack(side="left")

        status_wrap = ttk.Frame(header, style="TFrame")
        status_wrap.pack(side="right")

        self.status_canvas = tk.Canvas(status_wrap, width=10, height=10, bg=COLOR_BG, highlightthickness=0)
        self.status_dot = self.status_canvas.create_oval(1, 1, 9, 9, fill=COLOR_SUBTEXT, outline="")
        self.status_canvas.pack(side="left", padx=(0, 6))

        self.status_var = tk.StringVar(value="Остановлено")
        ttk.Label(status_wrap, textvariable=self.status_var, style="Status.TLabel").pack(side="left")

        region_wrap = ttk.Frame(root, style="TFrame")
        region_wrap.pack(fill="x", padx=18, pady=(0, 12))
        self.region_var = tk.StringVar(value="Область не выбрана")
        ttk.Label(region_wrap, textvariable=self.region_var, style="Sub.TLabel", wraplength=480).pack(anchor="w")

        btn_panel = ttk.Frame(root, style="Panel.TFrame")
        btn_panel.pack(fill="x", padx=18, pady=(0, 14))
        inner = ttk.Frame(btn_panel, style="Panel.TFrame")
        inner.pack(fill="x", padx=12, pady=12)

        ttk.Button(
            inner, text="Выбрать область   (Ctrl+Shift+R)", style="Neutral.TButton",
            command=self.select_region,
        ).pack(fill="x", pady=(0, 8))

        btn_row = ttk.Frame(inner, style="Panel.TFrame")
        btn_row.pack(fill="x")
        self.start_btn = ttk.Button(
            btn_row, text="▶  Старт  (F8)", style="Accent.TButton", command=self.start, state="disabled"
        )
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.stop_btn = ttk.Button(
            btn_row, text="■  Стоп  (F9)", style="Danger.TButton", command=self.stop, state="disabled"
        )
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=(6, 0))

        dict_panel = ttk.Frame(root, style="Panel.TFrame")
        dict_panel.pack(fill="x", padx=18, pady=(0, 14))
        dict_inner = ttk.Frame(dict_panel, style="Panel.TFrame")
        dict_inner.pack(fill="x", padx=12, pady=10)

        self.dict_stats_var = tk.StringVar()
        self._refresh_dict_stats()
        ttk.Label(dict_inner, textvariable=self.dict_stats_var, style="SubPanel.TLabel").pack(
            side="left", anchor="w"
        )
        ttk.Button(
            dict_inner, text="Очистить обученное", style="Neutral.TButton",
            command=self.clear_learned,
        ).pack(side="right")

        ttk.Label(root, text="Отладка", style="Sub.TLabel").pack(anchor="w", padx=18)

        log_frame = tk.Frame(root, bg=COLOR_PANEL, highlightbackground=COLOR_BORDER, highlightthickness=1)
        log_frame.pack(fill="both", expand=True, padx=18, pady=(6, 16))

        self.log_text = tk.Text(
            log_frame, wrap="none", state="disabled", font=("Consolas", 9),
            bg=COLOR_PANEL, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
            relief="flat", padx=10, pady=8, borderwidth=0,
        )
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.log_text.tag_configure("input", foreground=COLOR_ACCENT)
        self.log_text.tag_configure("adapt", foreground=COLOR_GOLD)
        self.log_text.tag_configure("metric", foreground=COLOR_SUBTEXT)
        self.log_text.tag_configure("info", foreground=COLOR_TEXT)

    def _refresh_dict_stats(self):
        trusted_learned = sum(1 for c in self.learned_db.values() if c >= LEARNED_TRUST_MIN)
        draft = len(self.learned_db) - trusted_learned
        self.dict_stats_var.set(
            f"Словарь: {len(SEED_TERMS)} встроенных · {trusted_learned} обученных (доверенных) · {draft} черновых"
        )

    def clear_learned(self):
        self.learned_db.clear()
        save_dictionary(self.learned_db)
        self._refresh_dict_stats()
        self._append_log("Обученный словарь очищен", "info")

    def _append_log(self, msg, tag="info"):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n", tag)
        line_count = int(self.log_text.index("end-1c").split(".")[0])
        if line_count > MAX_LOG_LINES:
            self.log_text.delete("1.0", f"{line_count - MAX_LOG_LINES}.0")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _poll_log_queue(self):
        while True:
            try:
                msg, tag = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self._append_log(msg, tag)
        if self.running:
            self._refresh_dict_stats()
        self.root.after(50, self._poll_log_queue)

    def select_region(self):
        selector = RegionSelector(self.root)
        if selector.region and selector.region["width"] > 5 and selector.region["height"] > 5:
            self.region = selector.region
            r = self.region
            self.region_var.set(f"Область: {r['width']}x{r['height']} @ ({r['left']}, {r['top']})")
            self.start_btn.config(state="normal")
        else:
            self.region_var.set("Выбор отменён")

    def _hotkey_start(self):
        self.root.after(0, self.start)

    def _hotkey_stop(self):
        self.root.after(0, self.stop)

    def start(self):
        if self.running or not self.region:
            return
        self.bot = CaptureBot(self.region, self.log_queue, self.learned_db)
        self.bot.start()
        self.running = True
        self.status_var.set("Работает")
        self.status_canvas.itemconfig(self.status_dot, fill=COLOR_ACCENT)
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

    def stop(self):
        if not self.running:
            return
        if self.bot:
            self.bot.stop()
        self.running = False
        self.status_var.set("Остановлено")
        self.status_canvas.itemconfig(self.status_dot, fill=COLOR_SUBTEXT)
        self.start_btn.config(state="normal" if self.region else "disabled")
        self.stop_btn.config(state="disabled")
        self._refresh_dict_stats()

    def _on_close(self):
        self.stop()
        self.root.destroy()


if __name__ == "__main__":
    ControlPanel()
