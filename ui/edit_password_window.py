"""
ui/edit_password_window.py

Screen for editing an existing password entry.
Pre-fills all fields with current values.
"""

import tkinter as tk
from tkinter import messagebox

from core.vault import Vault
from core.generator import check_strength
from ui.styles import (
    BG_DARK, BG_SECONDARY, BG_INPUT,
    ACCENT, ACCENT_BTN, TEXT_PRIMARY, TEXT_MUTED,
    BORDER, DANGER,
    FONT_HEADING, FONT_BODY, FONT_SMALL,
    FONT_BUTTON, FONT_MONO,
    style_button, style_entry,
)

# EditPasswordWindow class
class EditPasswordWindow:

    def __init__(self, parent, vault: Vault,
                 entry: dict, on_close=None):
        self.vault    = vault
        self.entry    = entry
        self.on_close = on_close

        self.win = tk.Toplevel(parent)
        self.win.title("Edit Password")
        self.win.configure(bg=BG_DARK)
        self.win.geometry("480x600")
        self.win.resizable(True, True)
        self.win.grab_set()

        self.win.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._build_ui()

    def _build_ui(self):
        outer = tk.Frame(self.win, bg=BG_DARK)
        outer.pack(expand=True, fill="both", padx=40, pady=24)

        # Heading
        tk.Label(
            outer, text="Edit password",
            font=FONT_HEADING,
            bg=BG_DARK, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 20))

        #  Name field 
        self._field_label(outer, "NAME")
        self.name_var = tk.StringVar(
            value=self.entry.get("title", "")
        )
        name_entry = tk.Entry(
            outer, textvariable=self.name_var, width=40
        )
        style_entry(name_entry)
        name_entry.pack(fill="x", pady=(4, 14))

        #  URL field 
        self._field_label(outer, "URL *")
        self.url_var = tk.StringVar(
            value=self.entry.get("url", "")
        )
        url_entry = tk.Entry(
            outer, textvariable=self.url_var, width=40
        )
        style_entry(url_entry)
        url_entry.pack(fill="x", pady=(4, 14))

        #  Username field 
        self._field_label(outer, "USER ID *")
        self.username_var = tk.StringVar(
            value=self.entry.get("username", "")
        )
        username_entry = tk.Entry(
            outer, textvariable=self.username_var, width=40
        )
        style_entry(username_entry)
        username_entry.pack(fill="x", pady=(4, 14))

        #  Password field 
        self._field_label(outer, "PASSWORD *")

        pw_row = tk.Frame(outer, bg=BG_DARK)
        pw_row.pack(fill="x", pady=(4, 0))

        self.pw_var = tk.StringVar(
            value=self.entry.get("password", "")
        )
        self._pw_visible = True
        self.pw_entry = tk.Entry(
            pw_row,
            textvariable=self.pw_var,
            show="",
            width=28,
        )
        style_entry(self.pw_entry)
        self.pw_entry.pack(side="left", fill="x", expand=True)

        self.show_btn = tk.Button(
            pw_row,
            text="Hide",
            command=self._toggle_pw,
            bg=BG_SECONDARY, fg=TEXT_MUTED,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=8,
        )
        self.show_btn.pack(side="left", padx=(6, 0))

        #  Strength meter 
        self.strength_var = tk.StringVar(value="")
        self.strength_label = tk.Label(
            outer,
            textvariable=self.strength_var,
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        )
        self.strength_label.pack(anchor="w", pady=(4, 0))
        self.pw_var.trace_add("write", self._update_strength)
        self._update_strength()

        #  Generate button 
        tk.Button(
            outer,
            text="Generate new password",
            command=self._open_generator,
            bg=BG_SECONDARY, fg=ACCENT,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=10, pady=6,
        ).pack(anchor="w", pady=(8, 14))

        #  Error label 
        self.error_var = tk.StringVar(value="")
        tk.Label(
            outer,
            textvariable=self.error_var,
            font=FONT_SMALL,
            bg=BG_DARK, fg=DANGER,
            wraplength=380,
        ).pack(anchor="w", pady=(0, 8))

        #  Required note 
        tk.Label(
            outer,
            text="* required fields",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 12))

        #  Buttons 
        btn_frame = tk.Frame(outer, bg=BG_DARK)
        btn_frame.pack(fill="x")

        tk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel,
            bg=BG_SECONDARY, fg=TEXT_MUTED,
            font=FONT_BUTTON,
            relief="flat", cursor="hand2",
            padx=16, pady=8,
        ).pack(side="left")

        save_btn = tk.Button(
            btn_frame,
            text="Save changes",
            command=self._on_save,
            width=18,
        )
        style_button(save_btn)
        save_btn.pack(side="right")

        self.win.bind("<Return>", lambda e: self._on_save())
        self.win.bind("<Escape>", lambda e: self._on_cancel())

    #  Helper methods for UI interactions
    def _field_label(self, parent, text: str):
        tk.Label(
            parent, text=text,
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x")

    # Toggle password visibility
    def _toggle_pw(self):
        self._pw_visible = not self._pw_visible
        self.pw_entry.configure(
            show="" if self._pw_visible else "●"
        )
        self.show_btn.configure(
            text="Hide" if self._pw_visible else "Show"
        )

    # Update password strength meter as user types
    def _update_strength(self, *args):
        pw = self.pw_var.get()
        if not pw:
            self.strength_var.set("")
            return
        score, label, colour = check_strength(pw)
        self.strength_var.set(f"Strength: {label}")
        self.strength_label.configure(fg=colour)

    # Open the password generator window and set up callback to receive generated password.
    def _open_generator(self):
        from ui.generator_window import GeneratorWindow
        GeneratorWindow(
            parent=self.win,
            on_use=self._use_generated_password,
        )

    # Callback to receive generated password from generator window and update the password field.
    def _use_generated_password(self, password: str):
        self.pw_var.set(password)
        self.pw_entry.configure(show="")
        self._pw_visible = True
        self.show_btn.configure(text="Hide")

    # Validate input and save changes to the vault. Shows confirmation dialog before saving. Displays error messages if validation fails or if there's an error during save.
    def _on_save(self):
  
        name     = self.name_var.get().strip()
        url      = self.url_var.get().strip()
        username = self.username_var.get().strip()
        password = self.pw_var.get().strip()

        # Validate required fields
        if not url:
            self.error_var.set("URL is required")
            return
        if not username:
            self.error_var.set("User ID is required")
            return
        if not password:
            self.error_var.set("Password is required")
            return

        # Confirm before saving
        confirm = messagebox.askyesno(
            "Confirm Edit",
            f"Save changes to this entry?\n\n"
            f"Name     : {name or url}\n"
            f"URL      : {url}\n"
            f"Username : {username}",
            parent=self.win,
        )

        if not confirm:
            return

        try:
            self.vault.edit(
                entry_id=self.entry["id"],
                username=username,
                password=password,
                url=url,
                notes="",
                title=name or url,
            )
            messagebox.showinfo(
                "Saved",
                "Password updated successfully.",
                parent=self.win,
            )
            self._on_cancel()
        except ValueError as e:
            self.error_var.set(str(e))
        except Exception as e:
            self.error_var.set(f"Error saving: {e}")

    # Close the window and call on_close callback if provided.
    def _on_cancel(self):
        self.win.destroy()
        if self.on_close:
            self.on_close()