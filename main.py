"""
IT-Grundlagen Quiz – A modern desktop quiz application.
Built with customtkinter for a premium dark-mode UI.
Questions are persisted in questions.json next to the script.
"""

import json
import random
import os
import sys
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError:
    print("customtkinter nicht gefunden. Installiere es mit:  pip install customtkinter")
    sys.exit(1)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = BASE_DIR / "questions.json"

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
        self.quiz_pool: list[dict] = []
        self.current_index: int = 0
        self.score: int = 0
        self.selected_answer: int | None = None
        self.answered: bool = False
        self.option_buttons: list[ctk.CTkButton] = []

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
        self._show_question()

    # =====================================================================
    # PAGE: Quiz
    # =====================================================================

    def _show_question(self):
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
            command=self._show_home,
        ).pack(side="left")

        ctk.CTkLabel(
            top,
            text=f"Frage {self.current_index + 1} / {total}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", expand=True)

        ctk.CTkLabel(
            top,
            text=f"⭐ {self.score}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ACCENT,
        ).pack(side="right", padx=(0, 8))

        # Progress bar
        progress = ctk.CTkProgressBar(
            self.container, width=400, height=6,
            progress_color=ACCENT, fg_color=BORDER,
            corner_radius=3,
        )
        progress.set((self.current_index) / total)
        progress.pack(pady=(14, 0))

        # Category badge
        cat = q.get("category", "Allgemein")
        ctk.CTkLabel(
            self.container,
            text=f"  {cat}  ",
            font=ctk.CTkFont(size=12),
            text_color=ACCENT,
            fg_color=CARD_BG,
            corner_radius=8,
        ).pack(pady=(22, 6))

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
        self.action_btn = AccentButton(
            self.container, text="Bestätigen", width=200,
            command=self._confirm_answer,
        )
        # Not packed yet – shown after selection

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
        if self.answered or self.selected_answer is None:
            return
        self.answered = True

        q = self.quiz_pool[self.current_index]
        correct = q["correct"]

        for i, btn in enumerate(self.option_buttons):
            if i == correct:
                btn.configure(fg_color=SUCCESS, border_color=SUCCESS, text_color="#ffffff")
            elif i == self.selected_answer and i != correct:
                btn.configure(fg_color=ERROR, border_color=ERROR, text_color="#ffffff")
            btn.configure(state="disabled")

        if self.selected_answer == correct:
            self.score += 1

        # Switch action button to "Next"
        is_last = self.current_index == len(self.quiz_pool) - 1
        self.action_btn.configure(
            text="Ergebnis anzeigen" if is_last else "Nächste Frage  →",
            command=self._next_question,
        )

    def _next_question(self):
        self.current_index += 1
        if self.current_index >= len(self.quiz_pool):
            self._show_result()
        else:
            self._show_question()

    # =====================================================================
    # PAGE: Result
    # =====================================================================
    def _show_result(self):
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
        new_q = {
            "question": question_text,
            "options": options,
            "correct": correct_idx,
            "category": category,
            "difficulty": difficulty,
        }
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
