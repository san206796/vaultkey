"""
ui/add_password_window.py

Screen for adding a new password entry to the vault.
Matches the proposal mockup:
  - Name, URL, Username, Password fields
  - Generate password button
  - Confirm before saving
"""

import tkinter as tk
from tkinter import messagebox

from core.vault import Vault
from core.generator import generate_password, check_strength
from ui.styles import (
    BG_DARK, BG_SECONDARY, BG_INPUT,
    ACCENT, ACCENT_BTN, TEXT_PRIMARY, TEXT_MUTED,
    BORDER, DANGER, STRENGTH_COLOURS,
    FONT_TITLE, FONT_HEADING, FONT_BODY,
    FONT_SMALL, FONT_BUTTON, FONT_MONO,
    style_button, style_entry, style_label,
)

# AddPasswordWindow class
class AddPasswordWindow:

    def __init__(self, parent: tk.Tk, vault: Vault, on_close=None):
        self.vault    = vault
        self.on_close = on_close  # callback to refresh main window

        # Create popup window
        self.win = tk.Toplevel(parent)
        self.win.title("Add Password")
        self.win.configure(bg=BG_DARK)
        self.win.geometry("480x620")
        self.win.resizable(False, False)
        self.win.grab_set()  # make it modal

        # Call on_close when window is closed
        self.win.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._build_ui()

    #  Build UI
    # Build the UI elements for the add password window. This includes the input fields, labels, buttons, and strength meter. The layout is designed to match the proposal mockup.
    def _build_ui(self):
        outer = tk.Frame(self.win, bg=BG_DARK)
        outer.pack(expand=True, fill="both", padx=40, pady=24)

        # Heading
        tk.Label(
            outer, text="Add new password",
            font=FONT_HEADING,
            bg=BG_DARK, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 20))

        # ─ Name field 
        self._field_label(outer, "NAME")
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(outer, textvariable=self.name_var, width=40)
        style_entry(name_entry)
        name_entry.pack(fill="x", pady=(4, 14))
        name_entry.insert(0, "e.g. Netflix")
        name_entry.bind("<FocusIn>",  lambda e: self._clear_placeholder(name_entry, "e.g. Netflix"))
        name_entry.bind("<FocusOut>", lambda e: self._set_placeholder(name_entry, "e.g. Netflix", self.name_var))
        name_entry.focus()

        #  URL field 
        self._field_label(outer, "URL *")
        self.url_var = tk.StringVar()
        url_entry = tk.Entry(outer, textvariable=self.url_var, width=40)
        style_entry(url_entry)
        url_entry.pack(fill="x", pady=(4, 14))
        url_entry.insert(0, "https://")
        url_entry.bind("<FocusIn>",  lambda e: self._clear_placeholder(url_entry, "https://"))
        url_entry.bind("<FocusOut>", lambda e: self._set_placeholder(url_entry, "https://", self.url_var))

        #  Username field 
        self._field_label(outer, "USER ID *")
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(outer, textvariable=self.username_var, width=40)
        style_entry(username_entry)
        username_entry.pack(fill="x", pady=(4, 14))

        #  Password field 
        self._field_label(outer, "PASSWORD *")

        pw_row = tk.Frame(outer, bg=BG_DARK)
        pw_row.pack(fill="x", pady=(4, 0))

        self.pw_var = tk.StringVar()
        self.pw_entry = tk.Entry(
            pw_row,
            textvariable=self.pw_var,
            show="●",
            width=28,
        )
        style_entry(self.pw_entry)
        self.pw_entry.pack(side="left", fill="x", expand=True)

        # Show/hide toggle
        self._pw_visible = False
        self.show_btn = tk.Button(
            pw_row,
            text="Show",
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

        #  Generate password button 
        gen_frame = tk.Frame(outer, bg=BG_DARK)
        gen_frame.pack(fill="x", pady=(8, 14))

        gen_btn = tk.Button(
            gen_frame,
            text="Generate password",
            command=self._open_generator,
            bg=BG_SECONDARY, fg=ACCENT,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=10, pady=6,
        )
        gen_btn.pack(side="left")

        #  Error label 
        self.error_var = tk.StringVar(value="")
        tk.Label(
            outer,
            textvariable=self.error_var,
            font=FONT_SMALL,
            bg=BG_DARK, fg=DANGER,
            wraplength=380,
        ).pack(pady=(0, 8))

        #  Required note 
        tk.Label(
            outer,
            text="* required fields",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 12))

        #  Buttons row 
        btn_frame = tk.Frame(outer, bg=BG_DARK)
        btn_frame.pack(fill="x")

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel,
            bg=BG_SECONDARY, fg=TEXT_MUTED,
            font=FONT_BUTTON,
            relief="flat", cursor="hand2",
            padx=16, pady=8,
        )
        cancel_btn.pack(side="left")

        add_btn = tk.Button(
            btn_frame,
            text="Add password",
            command=self._on_add,
            width=18,
        )
        style_button(add_btn)
        add_btn.pack(side="right")

        # Bind Enter key
        self.win.bind("<Return>", lambda e: self._on_add())
        self.win.bind("<Escape>", lambda e: self._on_cancel())

    #  Field label helper 
    # Helper to create a styled label for each field. Keeps the UI consistent and reduces code duplication.
    def _field_label(self, parent, text: str):
        tk.Label(
            parent, text=text,
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x")

    #  Placeholder helpers 
    # These functions manage the placeholder text in the Name and URL fields. When the field is focused, if it contains the placeholder text, it gets cleared
    # When the field loses focus, if it's empty, the placeholder text is set again. The placeholder text is styled with a muted colour to differentiate it from user input.
    def _clear_placeholder(self, entry: tk.Entry, placeholder: str):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.configure(fg=TEXT_PRIMARY)

    def _set_placeholder(self, entry: tk.Entry,
                         placeholder: str, var: tk.StringVar):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.configure(fg=TEXT_MUTED)
            var.set("")

    #  Show / hide password 
    # Toggle the visibility of the password field when the show/hide button is clicked.
    def _toggle_pw(self):
        self._pw_visible = not self._pw_visible
        self.pw_entry.configure(show="" if self._pw_visible else "●")
        self.show_btn.configure(
            text="Hide" if self._pw_visible else "Show"
        )

    #  Strength meter 
    # Update the strength label based on the current password. Called whenever the password field changes.
    def _update_strength(self, *args):
        pw = self.pw_var.get()
        if not pw:
            self.strength_var.set("")
            return
        score, label, colour = check_strength(pw)
        self.strength_var.set(f"Strength: {label}")
        self.strength_label.configure(fg=colour)

    #  Open generator 
    # Open the generator window. When user picks a password it gets pasted into the password field automatically.
    def _open_generator(self):
    
        from ui.generator_window import GeneratorWindow
        GeneratorWindow(
            parent=self.win,
            on_use=self._use_generated_password,
        )

    # Callback for when user clicks "Use password" in generator window.
    def _use_generated_password(self, password: str):
    
        self.pw_var.set(password)
        self.pw_entry.configure(show="")
        self._pw_visible = True
        self.show_btn.configure(text="Hide")

    #  Add password 
    # Validate fields and add to vault when user clicks "Add password".
    def _on_add(self):
        """Validate fields and add to vault."""
        name     = self.name_var.get().strip()
        url      = self.url_var.get().strip()
        username = self.username_var.get().strip()
        password = self.pw_var.get().strip()

        # Clean placeholders
        if url == "https://":
            url = ""
        if name == "e.g. Netflix":
            name = ""

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

        # Confirm before saving — matches proposal mockup
        confirm = messagebox.askyesno(
            "Confirm Add",
            f"Add this password?\n\n"
            f"Name     : {name or url}\n"
            f"URL      : {url}\n"
            f"Username : {username}",
            parent=self.win,
        )

        if not confirm:
            return

        # Save to vault
        try:
            self.vault.add(
                title=name or url,
                username=username,
                password=password,
                url=url,
            )
            messagebox.showinfo(
                "Saved",
                "Password added successfully.",
                parent=self.win,
            )
            self._on_cancel()  # close window and refresh

        except ValueError as e:
            self.error_var.set(str(e))
        except Exception as e:
            self.error_var.set(f"Error saving: {e}")

    # Cancel and close
    # Close the window and refresh the main window.
    def _on_cancel(self):
      
        self.win.destroy()
        if self.on_close:
            self.on_close()