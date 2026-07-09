"""
IT-Grundlagen Quiz – A modern desktop quiz application.
Built with customtkinter for a premium dark-mode UI.
Questions are persisted in questions.json next to the script.
"""

import json
import random
import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError:
    print("customtkinter nicht gefunden. Installiere es mit:  pip install customtkinter")
    sys.exit(1)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
STATS_FILE = BASE_DIR / "stats.json"

# ── Colour palette ───────────────────────────────────────────────────────────
BG_DARK       = "#0f0f1a"
CARD_BG       = "#1a1a2e"
CARD_HOVER    = "#25253d"
ACCENT        = "#6c63ff"
ACCENT_HOVER  = "#5a52e0"
SUCCESS       = "#2ecc71"
ERROR         = "#e74c3c"
WARN          = "#f39c12"
TEXT_PRIMARY   = "#e8e8f0"
TEXT_SECONDARY = "#9090a8"
TEXT_MUTED     = "#60607a"
BORDER         = "#2a2a45"
INPUT_BG       = "#12122a"

# ── Difficulty colours ───────────────────────────────────────────────────────
DIFFICULTY_COLORS = {
    "Leicht": SUCCESS,
    "Mittel": WARN,
    "Schwer": ERROR,
}
DIFFICULTY_LEVELS = ["Leicht", "Mittel", "Schwer"]

# ── Quiz modes ───────────────────────────────────────────────────────────────
MODE_STANDARD  = "Standard"
MODE_LEARN     = "Lernmodus"
MODE_EXAM      = "Prüfungsmodus"
MODE_TIMED     = "Zeitlimit"
QUIZ_MODES = [MODE_STANDARD, MODE_LEARN, MODE_EXAM, MODE_TIMED]
MODE_DESCRIPTIONS = {
    MODE_STANDARD: "Klassisches Quiz mit sofortigem Feedback.",
    MODE_LEARN:    "Erklärung nach jeder Frage, warum die Antwort richtig ist.",
    MODE_EXAM:     "Kein Feedback – Auswertung erst am Ende.",
    MODE_TIMED:    "Countdown pro Frage – antworte bevor die Zeit abläuft!",
}
DEFAULT_TIMER_SECONDS = 30

# ── Appearance ───────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ═════════════════════════════════════════════════════════════════════════════
# Data helpers
# ═════════════════════════════════════════════════════════════════════════════
def load_questions() -> list[dict]:
    """Load questions from the JSON file, returning an empty list on error."""
    if not QUESTIONS_FILE.exists():
        return []
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return []


def save_questions(questions: list[dict]) -> None:
    """Persist the question list to disk."""
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as fh:
        json.dump(questions, fh, ensure_ascii=False, indent=2)


def load_stats() -> dict:
    """Load statistics from stats.json."""
    if not STATS_FILE.exists():
        return {"history": [], "per_question": {}}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            data.setdefault("history", [])
            data.setdefault("per_question", {})
            return data
    except (json.JSONDecodeError, OSError):
        return {"history": [], "per_question": {}}


def save_stats(stats: dict) -> None:
    """Persist statistics to disk."""
    with open(STATS_FILE, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)


def question_key(q: dict) -> str:
    """Create a stable hash key for a question."""
    raw = q["question"] + "|".join(q["options"])
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def get_weak_questions(questions: list[dict], stats: dict, min_seen: int = 1) -> list[dict]:
    """Return questions sorted by error rate (worst first)."""
    pq = stats.get("per_question", {})
    scored = []
    for q in questions:
        key = question_key(q)
        info = pq.get(key, {})
        seen = info.get("seen", 0)
        correct = info.get("correct", 0)
        if seen >= min_seen:
            error_rate = 1.0 - (correct / seen)
            scored.append((error_rate, seen, q))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return [q for _, _, q in scored if _ > 0]  # only include questions with errors


# ═════════════════════════════════════════════════════════════════════════════
# Reusable UI widgets
# ═════════════════════════════════════════════════════════════════════════════
class Card(ctk.CTkFrame):
    """A rounded card container with a subtle border."""

    def __init__(self, master, **kw):
        kw.setdefault("fg_color", CARD_BG)
        kw.setdefault("corner_radius", 16)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", BORDER)
        super().__init__(master, **kw)


class AccentButton(ctk.CTkButton):
    """Prominent call-to-action button."""

    def __init__(self, master, **kw):
        kw.setdefault("fg_color", ACCENT)
        kw.setdefault("hover_color", ACCENT_HOVER)
        kw.setdefault("corner_radius", 12)
        kw.setdefault("height", 44)
        kw.setdefault("font", ctk.CTkFont(size=14, weight="bold"))
        super().__init__(master, **kw)


class GhostButton(ctk.CTkButton):
    """Subtle secondary button."""

    def __init__(self, master, **kw):
        kw.setdefault("fg_color", "transparent")
        kw.setdefault("hover_color", CARD_HOVER)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", BORDER)
        kw.setdefault("corner_radius", 12)
        kw.setdefault("height", 44)
        kw.setdefault("text_color", TEXT_PRIMARY)
        kw.setdefault("font", ctk.CTkFont(size=14))
        super().__init__(master, **kw)


# ═════════════════════════════════════════════════════════════════════════════
# Main Application
# ═════════════════════════════════════════════════════════════════════════════
class QuizApp(ctk.CTk):
    WIDTH = 900
    HEIGHT = 680

    def __init__(self):
        super().__init__()
        self.title("IT-Grundlagen Quiz")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(800, 600)
        self.configure(fg_color=BG_DARK)

        # ── State ────────────────────────────────────────────────────────
        self.questions: list[dict] = load_questions()
        self.stats: dict = load_stats()
        self.quiz_pool: list[dict] = []
        self.current_index: int = 0
        self.score: int = 0
        self.selected_answer: int | None = None
        self.answered: bool = False
        self.option_buttons: list[ctk.CTkButton] = []
        self.quiz_mode: str = MODE_STANDARD
        self.timer_seconds: int = DEFAULT_TIMER_SECONDS
        self.timer_remaining: int = 0
        self.timer_id: str | None = None
        self.exam_answers: list[int | None] = []

        # ── Container that holds all "pages" ─────────────────────────────
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        # Show the home screen
        self._show_home()

    # ─────────────────────────────────────────────────────────────────────
    # Navigation helpers
    # ─────────────────────────────────────────────────────────────────────
    def _clear(self):
        """Destroy all children in the container."""
        for w in self.container.winfo_children():
            w.destroy()

    # =====================================================================
    # PAGE: Home
    # =====================================================================
    def _show_home(self):
        self._clear()

        # Centre wrapper
        wrapper = ctk.CTkFrame(self.container, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        # Logo / title
        ctk.CTkLabel(
            wrapper, text="💻", font=ctk.CTkFont(size=56)
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            wrapper,
            text="IT-Grundlagen Quiz",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            wrapper,
            text="Teste dein Wissen in IT-Grundlagen",
            font=ctk.CTkFont(size=15),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(0, 30))

        # Stats card
        stats = Card(wrapper)
        stats.pack(fill="x", padx=40, pady=(0, 30))
        n = len(self.questions)
        cats = len({q.get("category", "Allgemein") for q in self.questions})
        row = ctk.CTkFrame(stats, fg_color="transparent")
        row.pack(pady=18, padx=24)
        for value, label in [(str(n), "Fragen"), (str(cats), "Kategorien")]:
            cell = ctk.CTkFrame(row, fg_color="transparent")
            cell.pack(side="left", padx=28)
            ctk.CTkLabel(
                cell, text=value,
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=ACCENT,
            ).pack()
            ctk.CTkLabel(
                cell, text=label,
                font=ctk.CTkFont(size=13),
                text_color=TEXT_MUTED,
            ).pack()

        # Buttons
        btn_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
        btn_frame.pack()

        AccentButton(
            btn_frame, text="▶  Quiz starten", width=220,
            command=self._start_quiz,
        ).pack(pady=6)

        GhostButton(
            btn_frame, text="＋  Frage hinzufügen", width=220,
            command=self._show_add_question,
        ).pack(pady=6)

        GhostButton(
            btn_frame, text="📋  Fragen verwalten", width=220,
            command=self._show_manage_questions,
        ).pack(pady=6)

        GhostButton(
            btn_frame, text="📊  Statistiken", width=220,
            command=self._show_stats,
        ).pack(pady=6)

    # =====================================================================
    # PAGE: Quiz Settings
    # =====================================================================
    def _start_quiz(self):
        if not self.questions:
            self._show_message("Keine Fragen vorhanden", "Füge zuerst Fragen hinzu!")
            return
        self._show_quiz_settings()

    def _show_quiz_settings(self):
        self._clear()

        scroll = ctk.CTkScrollableFrame(
            self.container, fg_color="transparent",
            scrollbar_button_color=BORDER,
        )
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        # Header
        top = ctk.CTkFrame(scroll, fg_color="transparent")
        top.pack(fill="x")
        GhostButton(
            top, text="←  Zurück", width=110, height=36,
            command=self._show_home,
        ).pack(side="left")
        ctk.CTkLabel(
            top, text="Quiz konfigurieren",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left", padx=16)

        # ── Category filter ──────────────────────────────────────────────
        cat_card = Card(scroll)
        cat_card.pack(fill="x", pady=(20, 10))
        cat_inner = ctk.CTkFrame(cat_card, fg_color="transparent")
        cat_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            cat_inner, text="📁  Kategorien",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            cat_inner, text="Wähle die Kategorien, die abgefragt werden sollen.",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 12))

        categories = sorted({q.get("category", "Allgemein") for q in self.questions})
        self.cat_vars: dict[str, ctk.BooleanVar] = {}
        cat_grid = ctk.CTkFrame(cat_inner, fg_color="transparent")
        cat_grid.pack(anchor="w")

        for i, cat in enumerate(categories):
            var = ctk.BooleanVar(value=True)
            self.cat_vars[cat] = var
            count = sum(1 for q in self.questions if q.get("category", "Allgemein") == cat)
            cb = ctk.CTkCheckBox(
                cat_grid, text=f"{cat}  ({count})",
                variable=var,
                font=ctk.CTkFont(size=14),
                fg_color=ACCENT, hover_color=ACCENT_HOVER,
                border_color=BORDER, text_color=TEXT_PRIMARY,
                checkmark_color="#ffffff",
            )
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 30), pady=4)

        # Select all / none buttons
        sel_row = ctk.CTkFrame(cat_inner, fg_color="transparent")
        sel_row.pack(anchor="w", pady=(8, 0))
        ctk.CTkButton(
            sel_row, text="Alle auswählen", width=120, height=30,
            fg_color="transparent", hover_color=CARD_HOVER,
            text_color=ACCENT, font=ctk.CTkFont(size=12),
            command=lambda: [v.set(True) for v in self.cat_vars.values()],
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            sel_row, text="Keine auswählen", width=120, height=30,
            fg_color="transparent", hover_color=CARD_HOVER,
            text_color=TEXT_MUTED, font=ctk.CTkFont(size=12),
            command=lambda: [v.set(False) for v in self.cat_vars.values()],
        ).pack(side="left")

        # ── Difficulty filter ────────────────────────────────────────────
        diff_card = Card(scroll)
        diff_card.pack(fill="x", pady=10)
        diff_inner = ctk.CTkFrame(diff_card, fg_color="transparent")
        diff_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            diff_inner, text="📊  Schwierigkeitsgrad",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            diff_inner, text="Filtere nach Schwierigkeitsgrad.",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 12))

        self.diff_vars: dict[str, ctk.BooleanVar] = {}
        diff_row = ctk.CTkFrame(diff_inner, fg_color="transparent")
        diff_row.pack(anchor="w")

        for level in DIFFICULTY_LEVELS:
            var = ctk.BooleanVar(value=True)
            self.diff_vars[level] = var
            color = DIFFICULTY_COLORS[level]
            count = sum(1 for q in self.questions if q.get("difficulty", "Mittel") == level)
            cb = ctk.CTkCheckBox(
                diff_row, text=f"{level}  ({count})",
                variable=var,
                font=ctk.CTkFont(size=14),
                fg_color=color, hover_color=color,
                border_color=BORDER, text_color=TEXT_PRIMARY,
                checkmark_color="#ffffff",
            )
            cb.pack(side="left", padx=(0, 24), pady=4)

        # ── Quiz length ──────────────────────────────────────────────────
        len_card = Card(scroll)
        len_card.pack(fill="x", pady=10)
        len_inner = ctk.CTkFrame(len_card, fg_color="transparent")
        len_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            len_inner, text="🔢  Fragenanzahl",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            len_inner, text="Wie viele Fragen soll das Quiz haben?",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 12))

        self.quiz_length_var = ctk.StringVar(value="10")
        seg_btn = ctk.CTkSegmentedButton(
            len_inner,
            values=["5", "10", "15", "Alle"],
            variable=self.quiz_length_var,
            font=ctk.CTkFont(size=14),
            fg_color=INPUT_BG,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=CARD_BG,
            unselected_hover_color=CARD_HOVER,
            text_color=TEXT_PRIMARY,
        )
        seg_btn.pack(anchor="w")

        # ── Quiz mode ────────────────────────────────────────────────────
        mode_card = Card(scroll)
        mode_card.pack(fill="x", pady=10)
        mode_inner = ctk.CTkFrame(mode_card, fg_color="transparent")
        mode_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            mode_inner, text="🎮  Quiz-Modus",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            mode_inner, text="Wähle einen Spielmodus.",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 12))

        self.mode_var = ctk.StringVar(value=MODE_STANDARD)
        self.mode_desc_label = ctk.CTkLabel(
            mode_inner, text=MODE_DESCRIPTIONS[MODE_STANDARD],
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=TEXT_MUTED,
            wraplength=500,
        )

        for mode in QUIZ_MODES:
            ctk.CTkRadioButton(
                mode_inner, text=mode, variable=self.mode_var,
                value=mode, font=ctk.CTkFont(size=14),
                fg_color=ACCENT, hover_color=ACCENT_HOVER,
                border_color=BORDER, text_color=TEXT_PRIMARY,
                command=self._update_mode_description,
            ).pack(anchor="w", pady=3)

        self.mode_desc_label.pack(anchor="w", pady=(8, 0))

        # ── Timer duration (shown only for Zeitlimit) ────────────────────
        self.timer_frame = ctk.CTkFrame(mode_inner, fg_color="transparent")
        self.timer_seconds_var = ctk.StringVar(value="30")
        ctk.CTkLabel(
            self.timer_frame, text="Sekunden pro Frage:",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkSegmentedButton(
            self.timer_frame,
            values=["15", "30", "45", "60"],
            variable=self.timer_seconds_var,
            font=ctk.CTkFont(size=13),
            fg_color=INPUT_BG,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=CARD_BG,
            unselected_hover_color=CARD_HOVER,
            text_color=TEXT_PRIMARY,
        ).pack(side="left")
        # Initially hidden
        self._update_mode_description()

        # ── Feedback label for validation ────────────────────────────────
        self.settings_feedback = ctk.CTkLabel(
            scroll, text="", font=ctk.CTkFont(size=13),
            text_color=ERROR,
        )
        self.settings_feedback.pack(pady=(10, 0))

        # ── Start button ─────────────────────────────────────────────────
        AccentButton(
            scroll, text="▶  Quiz starten", width=240,
            command=self._launch_quiz,
        ).pack(pady=(6, 20))

    def _update_mode_description(self):
        """Update the mode description text and show/hide timer options."""
        mode = self.mode_var.get()
        self.mode_desc_label.configure(text=MODE_DESCRIPTIONS.get(mode, ""))
        if mode == MODE_TIMED:
            self.timer_frame.pack(anchor="w", pady=(10, 0))
        else:
            self.timer_frame.pack_forget()

    def _launch_quiz(self):
        """Filter questions by selected categories & difficulty, then start."""
        selected_cats = {cat for cat, var in self.cat_vars.items() if var.get()}
        selected_diffs = {d for d, var in self.diff_vars.items() if var.get()}

        if not selected_cats:
            self.settings_feedback.configure(text="⚠ Bitte mindestens eine Kategorie auswählen.")
            return
        if not selected_diffs:
            self.settings_feedback.configure(text="⚠ Bitte mindestens einen Schwierigkeitsgrad auswählen.")
            return

        pool = [
            q for q in self.questions
            if q.get("category", "Allgemein") in selected_cats
            and q.get("difficulty", "Mittel") in selected_diffs
        ]

        if not pool:
            self.settings_feedback.configure(text="⚠ Keine Fragen mit diesen Filtern gefunden.")
            return

        # Determine quiz length
        length_str = self.quiz_length_var.get()
        if length_str == "Alle":
            count = len(pool)
        else:
            count = min(int(length_str), len(pool))

        self.quiz_pool = random.sample(pool, count)
        self.current_index = 0
        self.score = 0
        self.quiz_mode = self.mode_var.get()
        self.exam_answers = [None] * len(self.quiz_pool)
        if self.quiz_mode == MODE_TIMED:
            self.timer_seconds = int(self.timer_seconds_var.get())
        self._show_question()

    # =====================================================================
    # PAGE: Quiz
    # =====================================================================

    def _cancel_timer(self):
        """Cancel any pending timer callback."""
        if self.timer_id is not None:
            self.after_cancel(self.timer_id)
            self.timer_id = None

    def _abort_quiz(self):
        """Cancel timer and go home."""
        self._cancel_timer()
        self._show_home()

    def _show_question(self):
        self._cancel_timer()
        self._clear()
        self.selected_answer = None
        self.answered = False
        self.option_buttons.clear()

        q = self.quiz_pool[self.current_index]
        total = len(self.quiz_pool)

        # Top bar
        top = ctk.CTkFrame(self.container, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(20, 0))

        GhostButton(
            top, text="✕  Abbrechen", width=130, height=36,
            command=self._abort_quiz,
        ).pack(side="left")

        ctk.CTkLabel(
            top,
            text=f"Frage {self.current_index + 1} / {total}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", expand=True)

        # Score (hidden in exam mode)
        if self.quiz_mode != MODE_EXAM:
            ctk.CTkLabel(
                top,
                text=f"⭐ {self.score}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=ACCENT,
            ).pack(side="right", padx=(0, 8))

        # Timer display (Zeitlimit mode)
        if self.quiz_mode == MODE_TIMED:
            self.timer_remaining = self.timer_seconds
            self.timer_label = ctk.CTkLabel(
                top,
                text=f"⏱ {self.timer_remaining}s",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=WARN,
            )
            self.timer_label.pack(side="right", padx=(0, 16))

        # Progress bar
        progress = ctk.CTkProgressBar(
            self.container, width=400, height=6,
            progress_color=ACCENT, fg_color=BORDER,
            corner_radius=3,
        )
        progress.set((self.current_index) / total)
        progress.pack(pady=(14, 0))

        # Category + mode badge
        cat = q.get("category", "Allgemein")
        badge_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        badge_frame.pack(pady=(22, 6))
        ctk.CTkLabel(
            badge_frame,
            text=f"  {cat}  ",
            font=ctk.CTkFont(size=12),
            text_color=ACCENT,
            fg_color=CARD_BG,
            corner_radius=8,
        ).pack(side="left", padx=4)
        if self.quiz_mode != MODE_STANDARD:
            mode_color = {MODE_LEARN: SUCCESS, MODE_EXAM: TEXT_SECONDARY, MODE_TIMED: WARN}.get(self.quiz_mode, TEXT_MUTED)
            ctk.CTkLabel(
                badge_frame,
                text=f"  {self.quiz_mode}  ",
                font=ctk.CTkFont(size=11),
                text_color=mode_color,
                fg_color=CARD_BG,
                corner_radius=8,
            ).pack(side="left", padx=4)

        # Question text
        ctk.CTkLabel(
            self.container,
            text=q["question"],
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
            wraplength=650,
            justify="center",
        ).pack(pady=(4, 24), padx=40)

        # Answer options
        options_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        options_frame.pack()

        letters = "ABCD"
        for idx, option_text in enumerate(q["options"]):
            btn = ctk.CTkButton(
                options_frame,
                text=f"  {letters[idx]}   {option_text}",
                font=ctk.CTkFont(size=15),
                fg_color=CARD_BG,
                hover_color=CARD_HOVER,
                border_width=1,
                border_color=BORDER,
                corner_radius=12,
                height=52,
                width=560,
                anchor="w",
                text_color=TEXT_PRIMARY,
                command=lambda i=idx: self._select_answer(i),
            )
            btn.pack(pady=5)
            self.option_buttons.append(btn)

        # Confirm / Next button (hidden until answer chosen)
        btn_text = "Bestätigen" if self.quiz_mode != MODE_EXAM else "Weiter  →"
        self.action_btn = AccentButton(
            self.container, text=btn_text, width=200,
            command=self._confirm_answer,
        )
        # Not packed yet – shown after selection

        # Placeholder for explanation (Lernmodus)
        self.explanation_label = None

        # Start timer if timed mode
        if self.quiz_mode == MODE_TIMED:
            self._tick_timer()

    def _tick_timer(self):
        """Decrement the countdown and auto-submit when time runs out."""
        if self.answered:
            return
        self.timer_remaining -= 1
        if self.timer_remaining <= 0:
            # Time's up – auto-confirm with whatever is selected (or None)
            self.timer_label.configure(text="⏱ 0s", text_color=ERROR)
            if self.selected_answer is None:
                self.selected_answer = -1  # sentinel for "no answer"
            self._confirm_answer()
            return
        # Update display
        color = WARN if self.timer_remaining > 10 else ERROR
        self.timer_label.configure(text=f"⏱ {self.timer_remaining}s", text_color=color)
        self.timer_id = self.after(1000, self._tick_timer)

    def _select_answer(self, idx: int):
        if self.answered:
            return
        self.selected_answer = idx
        # Highlight selected, reset others
        for i, btn in enumerate(self.option_buttons):
            if i == idx:
                btn.configure(border_color=ACCENT, fg_color=CARD_HOVER)
            else:
                btn.configure(border_color=BORDER, fg_color=CARD_BG)
        self.action_btn.pack(pady=(20, 10))

    def _confirm_answer(self):
        if self.answered:
            return
        # In exam mode, allow skipping (no answer = None stored)
        if self.selected_answer is None and self.quiz_mode != MODE_EXAM:
            return
        self.answered = True
        self._cancel_timer()

        q = self.quiz_pool[self.current_index]
        correct = q["correct"]
        is_correct = self.selected_answer == correct

        # Store answer for exam review
        self.exam_answers[self.current_index] = self.selected_answer

        # Track per-question stats
        key = question_key(q)
        pq = self.stats.setdefault("per_question", {})
        pq.setdefault(key, {"seen": 0, "correct": 0})
        pq[key]["seen"] += 1
        if is_correct:
            pq[key]["correct"] += 1

        if self.quiz_mode == MODE_EXAM:
            # No feedback – just move on
            if is_correct:
                self.score += 1
            self._next_question()
            return

        # ── Standard / Lernmodus / Zeitlimit: show feedback ──────────────
        for i, btn in enumerate(self.option_buttons):
            if i == correct:
                btn.configure(fg_color=SUCCESS, border_color=SUCCESS, text_color="#ffffff")
            elif i == self.selected_answer and i != correct:
                btn.configure(fg_color=ERROR, border_color=ERROR, text_color="#ffffff")
            btn.configure(state="disabled")

        if is_correct:
            self.score += 1

        # Show explanation in Lernmodus
        if self.quiz_mode == MODE_LEARN:
            explanation = q.get("explanation", "")
            if explanation:
                expl_card = Card(self.container, border_color=SUCCESS)
                expl_card.pack(padx=60, pady=(12, 0))
                expl_inner = ctk.CTkFrame(expl_card, fg_color="transparent")
                expl_inner.pack(padx=16, pady=12)
                ctk.CTkLabel(
                    expl_inner, text="💡 Erklärung",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=SUCCESS,
                ).pack(anchor="w")
                ctk.CTkLabel(
                    expl_inner, text=explanation,
                    font=ctk.CTkFont(size=13),
                    text_color=TEXT_SECONDARY,
                    wraplength=480,
                    justify="left",
                ).pack(anchor="w", pady=(4, 0))
            elif not is_correct:
                letters = "ABCD"
                ctk.CTkLabel(
                    self.container,
                    text=f"💡 Die richtige Antwort ist {letters[correct]}: {q['options'][correct]}",
                    font=ctk.CTkFont(size=13),
                    text_color=TEXT_SECONDARY,
                    wraplength=500,
                ).pack(pady=(10, 0))

        # Switch action button to "Next"
        is_last = self.current_index == len(self.quiz_pool) - 1
        self.action_btn.configure(
            text="Ergebnis anzeigen" if is_last else "Nächste Frage  →",
            command=self._next_question,
        )

    def _next_question(self):
        self.current_index += 1
        if self.current_index >= len(self.quiz_pool):
            if self.quiz_mode == MODE_EXAM:
                self._show_exam_review()
            else:
                self._show_result()
        else:
            self._show_question()

    # =====================================================================
    # PAGE: Result
    # =====================================================================
    def _show_result(self):
        self._cancel_timer()
        self._record_history()
        self._clear()
        total = len(self.quiz_pool)
        pct = self.score / total * 100 if total else 0

        wrapper = ctk.CTkFrame(self.container, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        # Emoji based on score
        if pct >= 80:
            emoji, comment = "🏆", "Ausgezeichnet!"
        elif pct >= 60:
            emoji, comment = "👍", "Gut gemacht!"
        elif pct >= 40:
            emoji, comment = "📚", "Weiter üben!"
        else:
            emoji, comment = "💪", "Nicht aufgeben!"

        ctk.CTkLabel(wrapper, text=emoji, font=ctk.CTkFont(size=64)).pack(pady=(0, 6))
        ctk.CTkLabel(
            wrapper, text=comment,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(pady=(0, 4))

        # Score card
        score_card = Card(wrapper)
        score_card.pack(padx=40, pady=20)
        inner = ctk.CTkFrame(score_card, fg_color="transparent")
        inner.pack(padx=40, pady=24)

        ctk.CTkLabel(
            inner,
            text=f"{self.score} / {total}",
            font=ctk.CTkFont(size=44, weight="bold"),
            text_color=ACCENT,
        ).pack()
        ctk.CTkLabel(
            inner,
            text=f"{pct:.0f} % richtig",
            font=ctk.CTkFont(size=16),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(2, 0))

        btn_row = ctk.CTkFrame(wrapper, fg_color="transparent")
        btn_row.pack(pady=10)
        AccentButton(
            btn_row, text="🔄  Nochmal spielen", width=200,
            command=self._start_quiz,
        ).pack(side="left", padx=6)
        GhostButton(
            btn_row, text="🏠  Startseite", width=200,
            command=self._show_home,
        ).pack(side="left", padx=6)

    def _record_history(self):
        """Save a quiz result entry to the stats history."""
        cats = list({q.get("category", "Allgemein") for q in self.quiz_pool})
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "score": self.score,
            "total": len(self.quiz_pool),
            "mode": self.quiz_mode,
            "categories": cats,
        }
        self.stats.setdefault("history", []).append(entry)
        save_stats(self.stats)

    # =====================================================================
    # PAGE: Exam Review (Prüfungsmodus)
    # =====================================================================
    def _show_exam_review(self):
        self._record_history()
        self._clear()
        total = len(self.quiz_pool)
        pct = self.score / total * 100 if total else 0

        scroll = ctk.CTkScrollableFrame(
            self.container, fg_color="transparent",
            scrollbar_button_color=BORDER,
        )
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        # Header with score
        if pct >= 80:
            emoji, comment = "🏆", "Ausgezeichnet!"
        elif pct >= 60:
            emoji, comment = "👍", "Gut gemacht!"
        elif pct >= 40:
            emoji, comment = "📚", "Weiter üben!"
        else:
            emoji, comment = "💪", "Nicht aufgeben!"

        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(pady=(0, 10))
        ctk.CTkLabel(
            header, text=f"{emoji}  {comment}  —  {self.score}/{total} ({pct:.0f} %)",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack()
        ctk.CTkLabel(
            header, text="Prüfungsmodus – Auswertung",
            font=ctk.CTkFont(size=14),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(2, 0))

        # Review each question
        letters = "ABCD"
        for idx, q in enumerate(self.quiz_pool):
            user_ans = self.exam_answers[idx]
            correct = q["correct"]
            is_correct = user_ans == correct

            border_col = SUCCESS if is_correct else ERROR
            card = Card(scroll, border_color=border_col)
            card.pack(fill="x", pady=6)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=20, pady=14)

            # Question number + status
            status_text = "✓ Richtig" if is_correct else "✗ Falsch"
            status_color = SUCCESS if is_correct else ERROR
            q_header = ctk.CTkFrame(inner, fg_color="transparent")
            q_header.pack(fill="x")
            ctk.CTkLabel(
                q_header,
                text=f"Frage {idx + 1}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=TEXT_MUTED,
            ).pack(side="left")
            ctk.CTkLabel(
                q_header,
                text=status_text,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=status_color,
            ).pack(side="right")

            # Question text
            ctk.CTkLabel(
                inner,
                text=q["question"],
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=TEXT_PRIMARY,
                wraplength=560,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(6, 8))

            # Show answers
            for opt_idx, opt_text in enumerate(q["options"]):
                if opt_idx == correct:
                    prefix = "✓"
                    color = SUCCESS
                elif opt_idx == user_ans and opt_idx != correct:
                    prefix = "✗"
                    color = ERROR
                else:
                    prefix = " "
                    color = TEXT_MUTED
                ctk.CTkLabel(
                    inner,
                    text=f"  {prefix}  {letters[opt_idx]}   {opt_text}",
                    font=ctk.CTkFont(size=13),
                    text_color=color,
                    anchor="w",
                ).pack(anchor="w", pady=1)

            if user_ans is None or user_ans == -1:
                ctk.CTkLabel(
                    inner,
                    text="  (Nicht beantwortet)",
                    font=ctk.CTkFont(size=12, slant="italic"),
                    text_color=TEXT_MUTED,
                ).pack(anchor="w", pady=(4, 0))

        # Bottom buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(pady=16)
        AccentButton(
            btn_row, text="🔄  Nochmal spielen", width=200,
            command=self._start_quiz,
        ).pack(side="left", padx=6)
        GhostButton(
            btn_row, text="🏠  Startseite", width=200,
            command=self._show_home,
        ).pack(side="left", padx=6)

    # =====================================================================
    # PAGE: Statistics
    # =====================================================================
    def _show_stats(self):
        self._clear()

        scroll = ctk.CTkScrollableFrame(
            self.container, fg_color="transparent",
            scrollbar_button_color=BORDER,
        )
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        # Header
        top = ctk.CTkFrame(scroll, fg_color="transparent")
        top.pack(fill="x")
        GhostButton(
            top, text="←  Zurück", width=110, height=36,
            command=self._show_home,
        ).pack(side="left")
        ctk.CTkLabel(
            top, text="📊  Statistiken",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left", padx=16)

        history = self.stats.get("history", [])
        pq = self.stats.get("per_question", {})

        if not history:
            ctk.CTkLabel(
                scroll,
                text="Noch keine Quiz-Ergebnisse vorhanden.\nSpiele ein Quiz, um deine Statistiken zu sehen!",
                font=ctk.CTkFont(size=15),
                text_color=TEXT_SECONDARY,
                justify="center",
            ).pack(expand=True, pady=60)
            return

        # ── Overall stats card ───────────────────────────────────────────
        overview_card = Card(scroll)
        overview_card.pack(fill="x", pady=(20, 10))
        overview_inner = ctk.CTkFrame(overview_card, fg_color="transparent")
        overview_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            overview_inner, text="🏅  Gesamtübersicht",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 12))

        total_quizzes = len(history)
        total_correct = sum(h["score"] for h in history)
        total_questions = sum(h["total"] for h in history)
        avg_pct = (total_correct / total_questions * 100) if total_questions else 0
        best_pct = max((h["score"] / h["total"] * 100) for h in history) if history else 0

        stats_row = ctk.CTkFrame(overview_inner, fg_color="transparent")
        stats_row.pack(fill="x")
        for value, label in [
            (str(total_quizzes), "Quiz gespielt"),
            (f"{avg_pct:.0f} %", "Ø Ergebnis"),
            (f"{best_pct:.0f} %", "Bestes Ergebnis"),
            (str(total_correct), "Richtig gesamt"),
        ]:
            cell = ctk.CTkFrame(stats_row, fg_color="transparent")
            cell.pack(side="left", expand=True)
            ctk.CTkLabel(
                cell, text=value,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=ACCENT,
            ).pack()
            ctk.CTkLabel(
                cell, text=label,
                font=ctk.CTkFont(size=12),
                text_color=TEXT_MUTED,
            ).pack()

        # ── Progress chart (last 10 quizzes) ─────────────────────────────
        chart_card = Card(scroll)
        chart_card.pack(fill="x", pady=10)
        chart_inner = ctk.CTkFrame(chart_card, fg_color="transparent")
        chart_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            chart_inner, text="📈  Verlauf (letzte 10 Quiz)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 12))

        recent = history[-10:]
        chart_frame = ctk.CTkFrame(chart_inner, fg_color="transparent")
        chart_frame.pack(fill="x")

        # Bar chart using progress bars
        BAR_HEIGHT = 120
        for i, entry in enumerate(recent):
            pct = entry["score"] / entry["total"] * 100 if entry["total"] else 0
            col = ctk.CTkFrame(chart_frame, fg_color="transparent")
            col.pack(side="left", expand=True, fill="both", padx=2)

            # Percentage label on top
            ctk.CTkLabel(
                col, text=f"{pct:.0f}%",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=TEXT_PRIMARY if pct >= 60 else ERROR,
            ).pack()

            # Bar container
            bar_outer = ctk.CTkFrame(col, fg_color=INPUT_BG, corner_radius=6, height=BAR_HEIGHT, width=28)
            bar_outer.pack(pady=2)
            bar_outer.pack_propagate(False)

            # Filled bar from bottom
            fill_height = max(4, int(BAR_HEIGHT * pct / 100))
            if pct >= 80:
                bar_color = SUCCESS
            elif pct >= 60:
                bar_color = ACCENT
            elif pct >= 40:
                bar_color = WARN
            else:
                bar_color = ERROR

            spacer = ctk.CTkFrame(bar_outer, fg_color="transparent", height=BAR_HEIGHT - fill_height)
            spacer.pack(fill="x")
            bar_fill = ctk.CTkFrame(bar_outer, fg_color=bar_color, corner_radius=4, height=fill_height)
            bar_fill.pack(fill="x", expand=True)

            # Date label below
            date_short = entry.get("date", "")[-5:]  # "HH:MM" or "MM-DD"
            ctk.CTkLabel(
                col, text=date_short,
                font=ctk.CTkFont(size=10),
                text_color=TEXT_MUTED,
            ).pack()

        # ── Category breakdown ───────────────────────────────────────────
        cat_card = Card(scroll)
        cat_card.pack(fill="x", pady=10)
        cat_inner = ctk.CTkFrame(cat_card, fg_color="transparent")
        cat_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            cat_inner, text="📁  Leistung nach Kategorie",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 12))

        # Aggregate per-question stats by category
        cat_stats: dict[str, dict] = {}
        for q in self.questions:
            key = question_key(q)
            info = pq.get(key, {})
            seen = info.get("seen", 0)
            correct = info.get("correct", 0)
            if seen > 0:
                cat = q.get("category", "Allgemein")
                cat_stats.setdefault(cat, {"seen": 0, "correct": 0})
                cat_stats[cat]["seen"] += seen
                cat_stats[cat]["correct"] += correct

        if cat_stats:
            for cat_name, data in sorted(cat_stats.items()):
                cat_pct = data["correct"] / data["seen"] * 100 if data["seen"] else 0
                row = ctk.CTkFrame(cat_inner, fg_color="transparent")
                row.pack(fill="x", pady=3)

                ctk.CTkLabel(
                    row, text=cat_name, width=120,
                    font=ctk.CTkFont(size=13),
                    text_color=TEXT_PRIMARY, anchor="w",
                ).pack(side="left")

                bar_bg = ctk.CTkFrame(row, fg_color=INPUT_BG, corner_radius=4, height=14)
                bar_bg.pack(side="left", fill="x", expand=True, padx=(8, 8))
                bar_bg.pack_propagate(False)

                if cat_pct >= 80:
                    bar_col = SUCCESS
                elif cat_pct >= 60:
                    bar_col = ACCENT
                elif cat_pct >= 40:
                    bar_col = WARN
                else:
                    bar_col = ERROR

                if cat_pct > 0:
                    bar_fill = ctk.CTkFrame(bar_bg, fg_color=bar_col, corner_radius=4)
                    bar_fill.place(relx=0, rely=0, relwidth=cat_pct / 100, relheight=1.0)

                ctk.CTkLabel(
                    row, text=f"{cat_pct:.0f} %", width=50,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=bar_col, anchor="e",
                ).pack(side="right")
        else:
            ctk.CTkLabel(
                cat_inner, text="Noch keine Daten verfügbar.",
                font=ctk.CTkFont(size=13), text_color=TEXT_MUTED,
            ).pack(anchor="w")

        # ── Weak questions ───────────────────────────────────────────────
        weak_qs = get_weak_questions(self.questions, self.stats)

        weak_card = Card(scroll)
        weak_card.pack(fill="x", pady=10)
        weak_inner = ctk.CTkFrame(weak_card, fg_color="transparent")
        weak_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            weak_inner, text="⚠️  Schwächen",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            weak_inner, text="Fragen, die du am häufigsten falsch beantwortest.",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 12))

        if weak_qs:
            for q in weak_qs[:8]:
                key = question_key(q)
                info = pq.get(key, {})
                seen = info.get("seen", 0)
                correct_count = info.get("correct", 0)
                err_rate = (1 - correct_count / seen) * 100 if seen else 0

                wq_row = ctk.CTkFrame(weak_inner, fg_color=INPUT_BG, corner_radius=10)
                wq_row.pack(fill="x", pady=3)
                wq_inner = ctk.CTkFrame(wq_row, fg_color="transparent")
                wq_inner.pack(fill="x", padx=14, pady=8)

                ctk.CTkLabel(
                    wq_inner,
                    text=q["question"][:70] + ("…" if len(q["question"]) > 70 else ""),
                    font=ctk.CTkFont(size=13),
                    text_color=TEXT_PRIMARY,
                    anchor="w",
                ).pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    wq_inner,
                    text=f"{err_rate:.0f} % falsch  ({correct_count}/{seen})",
                    font=ctk.CTkFont(size=12),
                    text_color=ERROR,
                ).pack(side="right")

            # Schwächen üben button
            AccentButton(
                weak_inner, text="🎯  Schwächen üben", width=220,
                command=self._start_weakness_quiz,
            ).pack(pady=(14, 0))
        else:
            ctk.CTkLabel(
                weak_inner,
                text="🎉 Keine Schwächen erkannt! Alle Fragen wurden korrekt beantwortet.",
                font=ctk.CTkFont(size=13),
                text_color=SUCCESS,
            ).pack(anchor="w")

        # ── Recent history table ─────────────────────────────────────────
        hist_card = Card(scroll)
        hist_card.pack(fill="x", pady=10)
        hist_inner = ctk.CTkFrame(hist_card, fg_color="transparent")
        hist_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            hist_inner, text="🕒  Letzte Ergebnisse",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 12))

        # Table header
        hdr = ctk.CTkFrame(hist_inner, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 4))
        for text, w in [("Datum", 140), ("Modus", 130), ("Ergebnis", 100), ("Quote", 80)]:
            ctk.CTkLabel(
                hdr, text=text, width=w,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_MUTED, anchor="w",
            ).pack(side="left")

        for entry in reversed(history[-15:]):
            row = ctk.CTkFrame(hist_inner, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ep = entry["score"] / entry["total"] * 100 if entry["total"] else 0
            ep_color = SUCCESS if ep >= 60 else (WARN if ep >= 40 else ERROR)

            ctk.CTkLabel(row, text=entry.get("date", "?"), width=140,
                          font=ctk.CTkFont(size=13), text_color=TEXT_PRIMARY, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=entry.get("mode", "?"), width=130,
                          font=ctk.CTkFont(size=13), text_color=TEXT_SECONDARY, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{entry['score']}/{entry['total']}", width=100,
                          font=ctk.CTkFont(size=13), text_color=TEXT_PRIMARY, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{ep:.0f} %", width=80,
                          font=ctk.CTkFont(size=13, weight="bold"), text_color=ep_color, anchor="w").pack(side="left")

        # ── Reset button ─────────────────────────────────────────────────
        ctk.CTkButton(
            scroll, text="🗑  Statistiken zurücksetzen",
            fg_color="transparent", hover_color=ERROR,
            text_color=TEXT_MUTED, font=ctk.CTkFont(size=12),
            height=30, width=200,
            command=self._reset_stats,
        ).pack(pady=(16, 10))

    def _start_weakness_quiz(self):
        """Start a quiz with the user's weakest questions."""
        weak = get_weak_questions(self.questions, self.stats)
        if not weak:
            self._show_message("Keine Schwächen", "Du hast alle Fragen richtig beantwortet!")
            return
        count = min(len(weak), 10)
        self.quiz_pool = weak[:count]
        random.shuffle(self.quiz_pool)
        self.current_index = 0
        self.score = 0
        self.quiz_mode = MODE_STANDARD
        self.exam_answers = [None] * len(self.quiz_pool)
        self._show_question()

    def _reset_stats(self):
        """Clear all statistics after confirmation."""
        self.stats = {"history": [], "per_question": {}}
        save_stats(self.stats)
        self._show_stats()

    # =====================================================================
    # PAGE: Add Question
    # =====================================================================
    def _show_add_question(self):
        self._clear()

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(
            self.container, fg_color="transparent",
            scrollbar_button_color=BORDER,
        )
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        # Header
        top = ctk.CTkFrame(scroll, fg_color="transparent")
        top.pack(fill="x")
        GhostButton(
            top, text="←  Zurück", width=110, height=36,
            command=self._show_home,
        ).pack(side="left")
        ctk.CTkLabel(
            top, text="Neue Frage hinzufügen",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left", padx=16)

        card = Card(scroll)
        card.pack(fill="x", pady=20)
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=28, pady=24)

        # Category
        ctk.CTkLabel(form, text="Kategorie", text_color=TEXT_SECONDARY,
                      font=ctk.CTkFont(size=13)).pack(anchor="w")
        self.add_category = ctk.CTkEntry(
            form, placeholder_text="z.B. Netzwerk, Hardware, Sicherheit …",
            fg_color=INPUT_BG, border_color=BORDER, height=40, corner_radius=10,
            text_color=TEXT_PRIMARY,
        )
        self.add_category.pack(fill="x", pady=(2, 14))

        # Question
        ctk.CTkLabel(form, text="Frage", text_color=TEXT_SECONDARY,
                      font=ctk.CTkFont(size=13)).pack(anchor="w")
        self.add_question = ctk.CTkTextbox(
            form, height=80, fg_color=INPUT_BG, border_color=BORDER,
            border_width=1, corner_radius=10, text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=14),
        )
        self.add_question.pack(fill="x", pady=(2, 14))

        # Options A-D
        self.add_options: list[ctk.CTkEntry] = []
        letters = "ABCD"
        for i in range(4):
            ctk.CTkLabel(form, text=f"Antwort {letters[i]}",
                          text_color=TEXT_SECONDARY,
                          font=ctk.CTkFont(size=13)).pack(anchor="w")
            entry = ctk.CTkEntry(
                form, placeholder_text=f"Option {letters[i]}",
                fg_color=INPUT_BG, border_color=BORDER, height=40,
                corner_radius=10, text_color=TEXT_PRIMARY,
            )
            entry.pack(fill="x", pady=(2, 10))
            self.add_options.append(entry)

        # Correct answer selector
        ctk.CTkLabel(form, text="Richtige Antwort",
                      text_color=TEXT_SECONDARY,
                      font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(4, 2))
        self.correct_var = ctk.StringVar(value="A")
        radio_row = ctk.CTkFrame(form, fg_color="transparent")
        radio_row.pack(anchor="w", pady=(0, 16))
        for i, letter in enumerate(letters):
            ctk.CTkRadioButton(
                radio_row, text=letter, variable=self.correct_var,
                value=letter, font=ctk.CTkFont(size=14),
                fg_color=ACCENT, hover_color=ACCENT_HOVER,
                border_color=BORDER, text_color=TEXT_PRIMARY,
            ).pack(side="left", padx=(0, 20))

        # Difficulty selector
        ctk.CTkLabel(form, text="Schwierigkeitsgrad",
                      text_color=TEXT_SECONDARY,
                      font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(4, 2))
        self.difficulty_var = ctk.StringVar(value="Mittel")
        diff_row = ctk.CTkFrame(form, fg_color="transparent")
        diff_row.pack(anchor="w", pady=(0, 16))
        for level in DIFFICULTY_LEVELS:
            ctk.CTkRadioButton(
                diff_row, text=level, variable=self.difficulty_var,
                value=level, font=ctk.CTkFont(size=14),
                fg_color=DIFFICULTY_COLORS[level],
                hover_color=DIFFICULTY_COLORS[level],
                border_color=BORDER, text_color=TEXT_PRIMARY,
            ).pack(side="left", padx=(0, 20))

        # Explanation (for Lernmodus)
        ctk.CTkLabel(form, text="Erklärung (optional, für Lernmodus)",
                      text_color=TEXT_SECONDARY,
                      font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(4, 2))
        self.add_explanation = ctk.CTkTextbox(
            form, height=60, fg_color=INPUT_BG, border_color=BORDER,
            border_width=1, corner_radius=10, text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=14),
        )
        self.add_explanation.pack(fill="x", pady=(2, 14))

        # Feedback label
        self.add_feedback = ctk.CTkLabel(
            form, text="", font=ctk.CTkFont(size=13),
            text_color=SUCCESS,
        )
        self.add_feedback.pack(pady=(0, 6))

        # Submit
        AccentButton(
            form, text="✓  Frage speichern", width=220,
            command=self._save_new_question,
        ).pack()

    def _save_new_question(self):
        question_text = self.add_question.get("1.0", "end").strip()
        options = [e.get().strip() for e in self.add_options]
        category = self.add_category.get().strip() or "Allgemein"
        correct_letter = self.correct_var.get()
        correct_idx = "ABCD".index(correct_letter)

        # Validation
        if not question_text:
            self.add_feedback.configure(text="⚠ Bitte eine Frage eingeben.", text_color=ERROR)
            return
        if any(not o for o in options):
            self.add_feedback.configure(text="⚠ Alle vier Antworten ausfüllen.", text_color=ERROR)
            return

        difficulty = self.difficulty_var.get()
        explanation = self.add_explanation.get("1.0", "end").strip()
        new_q = {
            "question": question_text,
            "options": options,
            "correct": correct_idx,
            "category": category,
            "difficulty": difficulty,
        }
        if explanation:
            new_q["explanation"] = explanation
        self.questions.append(new_q)
        save_questions(self.questions)

        self.add_feedback.configure(
            text=f"✓ Frage gespeichert! ({len(self.questions)} Fragen insgesamt)",
            text_color=SUCCESS,
        )
        # Clear fields for the next entry
        self.add_question.delete("1.0", "end")
        for e in self.add_options:
            e.delete(0, "end")
        self.add_category.delete(0, "end")
        self.add_explanation.delete("1.0", "end")
        self.correct_var.set("A")
        self.difficulty_var.set("Mittel")

    # =====================================================================
    # PAGE: Manage Questions
    # =====================================================================
    def _show_manage_questions(self):
        self._clear()

        # Header
        top = ctk.CTkFrame(self.container, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(20, 6))
        GhostButton(
            top, text="←  Zurück", width=110, height=36,
            command=self._show_home,
        ).pack(side="left")
        ctk.CTkLabel(
            top, text="Fragen verwalten",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left", padx=16)

        ctk.CTkLabel(
            top,
            text=f"{len(self.questions)} Fragen",
            font=ctk.CTkFont(size=14),
            text_color=TEXT_MUTED,
        ).pack(side="right")

        if not self.questions:
            ctk.CTkLabel(
                self.container,
                text="Noch keine Fragen vorhanden.\nFüge über die Startseite neue Fragen hinzu!",
                font=ctk.CTkFont(size=15),
                text_color=TEXT_SECONDARY,
                justify="center",
            ).pack(expand=True)
            return

        scroll = ctk.CTkScrollableFrame(
            self.container, fg_color="transparent",
            scrollbar_button_color=BORDER,
        )
        scroll.pack(fill="both", expand=True, padx=30, pady=(6, 20))

        for idx, q in enumerate(self.questions):
            row = Card(scroll)
            row.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=12)

            # Category + Question
            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)

            cat = q.get("category", "Allgemein")
            diff = q.get("difficulty", "Mittel")
            badge_row = ctk.CTkFrame(info, fg_color="transparent")
            badge_row.pack(anchor="w")
            ctk.CTkLabel(
                badge_row, text=f"  {cat}  ",
                font=ctk.CTkFont(size=11),
                text_color=ACCENT,
                fg_color=CARD_HOVER,
                corner_radius=6,
            ).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(
                badge_row, text=f"  {diff}  ",
                font=ctk.CTkFont(size=11),
                text_color=DIFFICULTY_COLORS.get(diff, TEXT_MUTED),
                fg_color=CARD_HOVER,
                corner_radius=6,
            ).pack(side="left")
            ctk.CTkLabel(
                info,
                text=q["question"][:90] + ("…" if len(q["question"]) > 90 else ""),
                font=ctk.CTkFont(size=14),
                text_color=TEXT_PRIMARY,
                anchor="w",
                wraplength=550,
                justify="left",
            ).pack(anchor="w")

            # Delete button
            ctk.CTkButton(
                inner, text="🗑", width=36, height=36,
                fg_color="transparent", hover_color=ERROR,
                corner_radius=8, font=ctk.CTkFont(size=16),
                text_color=TEXT_MUTED,
                command=lambda i=idx: self._delete_question(i),
            ).pack(side="right", padx=(8, 0))

    def _delete_question(self, idx: int):
        if 0 <= idx < len(self.questions):
            self.questions.pop(idx)
            save_questions(self.questions)
            self._show_manage_questions()

    # =====================================================================
    # Utility: Simple message dialog
    # =====================================================================
    def _show_message(self, title: str, message: str):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("380x180")
        dialog.configure(fg_color=BG_DARK)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text=title,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(pady=(24, 6))
        ctk.CTkLabel(
            dialog, text=message,
            font=ctk.CTkFont(size=14),
            text_color=TEXT_SECONDARY,
            wraplength=300,
        ).pack(pady=(0, 16))
        AccentButton(
            dialog, text="OK", width=100,
            command=dialog.destroy,
        ).pack()


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()
