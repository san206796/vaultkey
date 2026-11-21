"""
ui/generator_window.py

Standalone password generator window.
Can be opened from:
  - Main window footer button (standalone use)
  - Add password window (inserts generated password into field)

Options match the proposal mockup:
  LENGTH, LOWER CASE, UPPER CASE, NUMBER, SPECIAL CHARACTER
"""

import tkinter as tk

from core.generator import generate_password, check_strength
from ui.styles import (
    BG_DARK, BG_SECONDARY, BG_INPUT,
    ACCENT, ACCENT_BTN, TEXT_PRIMARY, TEXT_MUTED,
    BORDER, DANGER, STRENGTH_COLOURS,
    FONT_HEADING, FONT_BODY, FONT_SMALL,
    FONT_BUTTON, FONT_MONO,
    style_button, style_entry,
)
import pyperclip

# GeneratorWindow class
class GeneratorWindow:

    def __init__(self, parent: tk.Tk, on_use=None):
        self.on_use = on_use  # callback from add password window

        self.win = tk.Toplevel(parent)
        self.win.title("Password Generator")
        self.win.configure(bg=BG_DARK)
        self.win.geometry("420x520")
        self.win.resizable(False, False)
        self.win.grab_set()

        self._build_ui()
        self._generate()  # generate one immediately on open

    #  Build UI 

    def _build_ui(self):
        outer = tk.Frame(self.win, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=32, pady=24)

        # Heading
        tk.Label(
            outer, text="Password Generator",
            font=FONT_HEADING,
            bg=BG_DARK, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 20))

        #  Generated password display 
        tk.Label(
            outer, text="GENERATED PASSWORD",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(anchor="w")

        pw_frame = tk.Frame(
            outer, bg=BG_SECONDARY,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        pw_frame.pack(fill="x", pady=(4, 6))

        self.pw_var = tk.StringVar()
        pw_label = tk.Label(
            pw_frame,
            textvariable=self.pw_var,
            font=FONT_MONO,
            bg=BG_SECONDARY, fg=ACCENT,
            padx=14, pady=12,
            wraplength=320,
            justify="center",
        )
        pw_label.pack(fill="x")

        #  Strength bar 
        self.strength_var = tk.StringVar(value="")
        self.strength_label = tk.Label(
            outer,
            textvariable=self.strength_var,
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        )
        self.strength_label.pack(anchor="w", pady=(0, 16))

        #  Options 
        tk.Label(
            outer, text="OPTIONS",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 8))

        options_frame = tk.Frame(
            outer, bg=BG_SECONDARY,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        options_frame.pack(fill="x", pady=(0, 16))

        inner = tk.Frame(options_frame, bg=BG_SECONDARY)
        inner.pack(fill="x", padx=16, pady=12)

        # LENGTH row
        length_row = tk.Frame(inner, bg=BG_SECONDARY)
        length_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            length_row, text="LENGTH",
            font=FONT_SMALL,
            bg=BG_SECONDARY, fg=TEXT_MUTED,
            width=18, anchor="w",
        ).pack(side="left")

        self.length_var = tk.IntVar(value=16)

        # Minus button
        tk.Button(
            length_row, text="−",
            command=self._decrease_length,
            bg=BG_DARK, fg=TEXT_PRIMARY,
            font=FONT_BODY,
            relief="flat", cursor="hand2",
            padx=8,
        ).pack(side="left")

        # Length display
        self.length_label = tk.Label(
            length_row,
            textvariable=self.length_var,
            font=FONT_BODY,
            bg=BG_SECONDARY, fg=TEXT_PRIMARY,
            width=4,
        )
        self.length_label.pack(side="left")

        # Plus button
        tk.Button(
            length_row, text="＋",
            command=self._increase_length,
            bg=BG_DARK, fg=TEXT_PRIMARY,
            font=FONT_BODY,
            relief="flat", cursor="hand2",
            padx=8,
        ).pack(side="left")

        # Checkbox options — matches proposal mockup exactly
        self.use_lower   = self._checkbox(inner, "LOWER CASE   (a-z)", True)
        self.use_upper   = self._checkbox(inner, "UPPER CASE   (A-Z)", True)
        self.use_digits  = self._checkbox(inner, "NUMBER       (0-9)", True)
        self.use_symbols = self._checkbox(inner, "SPECIAL CHAR (!@#…)", True)

        #  Buttons 
        btn_frame = tk.Frame(outer, bg=BG_DARK)
        btn_frame.pack(fill="x", pady=(0, 10))

        # Regenerate
        regen_btn = tk.Button(
            btn_frame,
            text="↻  Regenerate",
            command=self._generate,
            bg=BG_SECONDARY, fg=TEXT_PRIMARY,
            font=FONT_BUTTON,
            relief="flat", cursor="hand2",
            padx=14, pady=8,
        )
        regen_btn.pack(side="left")

        # Copy
        copy_btn = tk.Button(
            btn_frame,
            text="Copy",
            command=self._copy,
            bg=BG_SECONDARY, fg=ACCENT,
            font=FONT_BUTTON,
            relief="flat", cursor="hand2",
            padx=14, pady=8,
        )
        copy_btn.pack(side="left", padx=(8, 0))

        # Use password (only shown when opened from add window)
        if self.on_use:
            use_btn = tk.Button(
                btn_frame,
                text="Use password",
                command=self._use_password,
                width=16,
            )
            style_button(use_btn)
            use_btn.pack(side="right")

        # Close
        close_btn = tk.Button(
            outer,
            text="Close",
            command=self.win.destroy,
            bg=BG_SECONDARY, fg=TEXT_MUTED,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=14, pady=6,
        )
        close_btn.pack(anchor="e")

        # Status label
        self.status_var = tk.StringVar(value="")
        tk.Label(
            outer,
            textvariable=self.status_var,
            font=FONT_SMALL,
            bg=BG_DARK, fg=ACCENT,
        ).pack(anchor="w", pady=(8, 0))

        # Bind Enter to regenerate
        self.win.bind("<Return>", lambda e: self._generate())
        self.win.bind("<Escape>", lambda e: self.win.destroy())

    #  Checkbox helper 
    # Creates a styled checkbox with the given label and default value. Returns the BooleanVar associated with the checkbox for later retrieval.
    def _checkbox(self, parent, label: str,
                  default: bool) -> tk.BooleanVar:
        
        var = tk.BooleanVar(value=default)
        row = tk.Frame(parent, bg=BG_SECONDARY)
        row.pack(fill="x", pady=3)

        tk.Checkbutton(
            row,
            text=label,
            variable=var,
            command=self._generate,
            bg=BG_SECONDARY, fg=TEXT_PRIMARY,
            selectcolor=ACCENT_BTN,
            activebackground=BG_SECONDARY,
            activeforeground=TEXT_PRIMARY,
            font=FONT_SMALL,
            relief="flat",
            cursor="hand2",
        ).pack(side="left")

        return var

    #  Length controls 
    # Increases or decreases the length variable within bounds and regenerates the password.
    def _increase_length(self):
        if self.length_var.get() < 64:
            self.length_var.set(self.length_var.get() + 1)
            self._generate()

    # Decrease length with bounds check
    def _decrease_length(self):
        if self.length_var.get() > 8:
            self.length_var.set(self.length_var.get() - 1)
            self._generate()

    #  Generate 
    # Generates a new password based on current options, updates the display and strength meter. If no character types are selected, shows an error message instead.
    def _generate(self, *args):

        # Must have at least one option ticked
        if not any([
            self.use_lower.get(),
            self.use_upper.get(),
            self.use_digits.get(),
            self.use_symbols.get(),
        ]):
            self.strength_var.set(
                "Select at least one character type"
            )
            self.strength_label.configure(fg=DANGER)
            return

        pw = generate_password(
            length=self.length_var.get(),
            use_lower=self.use_lower.get(),
            use_upper=self.use_upper.get(),
            use_digits=self.use_digits.get(),
            use_symbols=self.use_symbols.get(),
        )
        self.pw_var.set(pw)

        # Update strength
        score, label, colour = check_strength(pw)
        self.strength_var.set(f"Strength: {label}")
        self.strength_label.configure(fg=colour)
        self.status_var.set("")

    #  Copy 
    def _copy(self):
       
        pw = self.pw_var.get()
        if pw:
            pyperclip.copy(pw)
            self.status_var.set("Copied to clipboard ✓")
            self.win.after(
                2000,
                lambda: self.status_var.set("")
            )

    #  Use password 
    def _use_password(self):
        
        pw = self.pw_var.get()
        if pw and self.on_use:
            self.on_use(pw)
            self.win.destroy()