"""
ui/master_password_window.py
Handles master password for both new and returning users.
"""

import tkinter as tk
from tkinter import messagebox

from core.auth import MasterPasswordManager
from core.vault import Vault
from core.generator import check_strength
from ui.styles import (
    BG_DARK, BG_SECONDARY, BG_INPUT,
    ACCENT, ACCENT_BTN, TEXT_PRIMARY, TEXT_MUTED,
    BORDER, DANGER, STRENGTH_COLOURS,
    FONT_TITLE, FONT_HEADING, FONT_BODY,
    FONT_SMALL, FONT_BUTTON, FONT_MONO,
    style_button, style_entry, style_label,
)

# MasterPasswordWindow class
class MasterPasswordWindow:

    def __init__(self, root: tk.Tk, creds,
             user_info: dict, vault: Vault):
            
        self.root      = root
        self.creds     = creds
        self.user_info = user_info
        self.vault     = vault
        self.manager   = MasterPasswordManager()

        self.root.title("VaultKey")
        self.root.configure(bg=BG_DARK)
        self.root.geometry("460x540")
        self.root.minsize(400, 480)
        self.root.resizable(True, True)

        # First launch — no vault exists yet
        # go straight to create screen
        if not vault.vault_exists():
            self.is_new_user = True
            self._build_ui()
        else:
            # Returning user — show login or delete options
            self._build_choice_screen()

    #  Build choice screen for returning users
    def _build_choice_screen(self):
       
        for w in self.root.winfo_children():
            w.destroy()

        outer = tk.Frame(self.root, bg=BG_DARK)
        outer.pack(expand=True, fill="both", padx=50, pady=20)

        try:
            from PIL import Image, ImageTk
            img = Image.open("assets/icon.png").resize(
                (80, 80), Image.LANCZOS
            )
            self._icon_img = ImageTk.PhotoImage(img)
            tk.Label(
                outer,
                image=self._icon_img,
                bg=BG_DARK,
            ).pack(pady=(0, 8))
        except Exception as e:
            print(f"Icon load error: {e}")
            tk.Label(
                outer, text="🔑",
                font=("Segoe UI Emoji", 40),
                bg=BG_DARK, fg=TEXT_PRIMARY,
            ).pack()

        # App name
        tk.Label(
            outer, text="VaultKey",
            font=FONT_TITLE,
            bg=BG_DARK, fg=TEXT_PRIMARY,
        ).pack(pady=(8, 4))

        # Email
        tk.Label(
            outer,
            text=self.user_info.get("email", ""),
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(pady=(0, 28))

        # Welcome back
        tk.Label(
            outer,
            text=f"Welcome back, {self.user_info.get('name', '')}",
            font=FONT_HEADING,
            bg=BG_DARK, fg=TEXT_PRIMARY,
        ).pack()

        tk.Label(
            outer,
            text="What would you like to do?",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(pady=(4, 24))

        # Login button
        login_btn = tk.Button(
            outer,
            text="Login — open my vault",
            command=self._go_login,
            width=28,
        )
        style_button(login_btn)
        login_btn.pack(fill="x", pady=(0, 12))

        # Delete account button
        tk.Button(
            outer,
            text="Delete account",
            command=self._confirm_delete_account,
            bg=BG_DARK, fg=DANGER,
            font=FONT_BUTTON,
            relief="flat", cursor="hand2",
            pady=10,
            width=28,
            highlightbackground=DANGER,
            highlightthickness=1,
        ).pack(fill="x")

        # Note
        tk.Label(
            outer,
            text="Delete account removes your vault\n"
                "and signs you out permanently.",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            justify="center",
        ).pack(pady=(14, 0))

    #  Route to login screen
    def _go_login(self):
  
        self.is_new_user = False
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()

    #  Ask for master password first then confirm before wiping everything.
    def _confirm_delete_account(self):
        
        # Create prompt window
        prompt = tk.Toplevel(self.root)
        prompt.title("Delete account")
        prompt.configure(bg=BG_DARK)
        prompt.geometry("400x340")
        prompt.resizable(False, False)
        prompt.grab_set()

        outer = tk.Frame(prompt, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(
            outer,
            text="⚠  Delete account",
            font=FONT_HEADING,
            bg=BG_DARK, fg=DANGER,
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            outer,
            text="This will permanently delete your vault\n"
                "and sign you out. This cannot be undone.",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            justify="left",
        ).pack(anchor="w", pady=(0, 16))

        tk.Label(
            outer, text="Enter master password to confirm:",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        pw_var = tk.StringVar()
        pw_entry = tk.Entry(
            outer,
            textvariable=pw_var,
            show="●", width=32,
        )
        style_entry(pw_entry)
        pw_entry.pack(fill="x", pady=(4, 8))
        pw_entry.focus()

        error_var = tk.StringVar(value="")
        tk.Label(
            outer,
            textvariable=error_var,
            font=FONT_SMALL,
            bg=BG_DARK, fg=DANGER,
        ).pack(anchor="w", pady=(0, 16))

        btn_row = tk.Frame(outer, bg=BG_DARK)
        btn_row.pack(fill="x")

        # Verify password and if correct, show final confirmation before deleting everything.
        def verify_and_delete():
            entered = pw_var.get()
            if not entered:
                error_var.set("Please enter your master password")
                return

            test_vault = Vault()
            if not test_vault.open(entered):
                error_var.set("Wrong master password")
                pw_var.set("")
                pw_entry.focus()
                return

            # Correct — do final confirmation
            prompt.destroy()
            self._final_delete_confirm()

        tk.Button(
            btn_row,
            text="Cancel",
            command=prompt.destroy,
            bg=BG_SECONDARY, fg=TEXT_MUTED,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=12, pady=6,
        ).pack(side="left")

        tk.Button(
            btn_row,
            text="Confirm delete",
            command=verify_and_delete,
            bg=DANGER, fg="#FFFFFF",
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=12, pady=6,
        ).pack(side="right")

        prompt.bind("<Return>", lambda e: verify_and_delete())
        prompt.bind("<Escape>", lambda e: prompt.destroy())

    # Final confirmation before deleting everything
    def _final_delete_confirm(self):
        from tkinter import messagebox

        confirmed = messagebox.askyesno(
            "Final confirmation",
            "Are you absolutely sure?\n\n"
            "This will:\n"
            "  • Delete your entire vault\n"
            "  • Remove your Google sign-in\n"
            "  • Remove the Drive backup\n\n"
            "This CANNOT be undone.",
            icon="warning",
        )

        if not confirmed:
            return

        # Wipe everything
        import os
        import shutil

        # Delete local vault folder
        vault_dir = os.path.join(
            os.path.expanduser("~"), ".vaultkey"
        )
        if os.path.exists(vault_dir):
            shutil.rmtree(vault_dir)

        # Delete token
        token_file = os.path.join(
            os.path.expanduser("~"), ".vaultkey_token.json"
        )
        if os.path.exists(token_file):
            os.remove(token_file)

        # Try to delete Drive backup too
        try:
            from core.drive_sync import delete_remote_vault
            delete_remote_vault(self.creds)
        except Exception:
            pass

        messagebox.showinfo(
            "Account deleted",
            "Your vault and account have been deleted.\n"
            "The app will now close."
        )
        self.root.destroy()


    # Route to enter master password screen.
    def _go_login(self):
        self.is_new_user = False
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()

    #  Password screen 

    def _build_ui(self):
        
        outer = tk.Frame(self.root, bg=BG_DARK)
        outer.pack(expand=True, fill="both", padx=50, pady=30)

        # Icon
        try:
            from PIL import Image, ImageTk
            img = Image.open("assets/icon.png").resize(
                (80, 80), Image.LANCZOS
            )
            self._icon_img = ImageTk.PhotoImage(img)
            tk.Label(
                outer,
                image=self._icon_img,
                bg=BG_DARK,
            ).pack(pady=(0, 8))
        except Exception as e:
            print(f"Icon load error: {e}")
            tk.Label(
                outer, text="🔑",
                font=("Segoe UI Emoji", 40),
                bg=BG_DARK, fg=TEXT_PRIMARY,
            ).pack()

        # App name
        tk.Label(
            outer, text="VaultKey",
            font=FONT_TITLE,
            bg=BG_DARK, fg=TEXT_PRIMARY,
        ).pack(pady=(8, 4))

        # Email
        tk.Label(
            outer,
            text=self.user_info.get("email", ""),
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(pady=(0, 20))

        # Heading and sub label
        if self.is_new_user:
            heading = "Create your master password"
            sub     = "This password encrypts your vault.\n" \
                      "Never stored — remember it carefully."
        else:
            heading = "Enter your master password"
            sub     = f"Attempts remaining: " \
                      f"{self.manager.attempts_remaining()}"

        tk.Label(
            outer, text=heading,
            font=FONT_HEADING,
            bg=BG_DARK, fg=TEXT_PRIMARY,
        ).pack()

        self.sub_label_var = tk.StringVar(value=sub)
        tk.Label(
            outer,
            textvariable=self.sub_label_var,
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            justify="center",
        ).pack(pady=(4, 20))

        #  Password field 

        tk.Label(
            outer, text="Master password",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x")

        self.pw_var = tk.StringVar()
        self.pw_entry = tk.Entry(
            outer,
            textvariable=self.pw_var,
            show="●",
            width=36,
        )
        style_entry(self.pw_entry)
        self.pw_entry.pack(fill="x", pady=(4, 8))
        self.pw_entry.focus()

        # Show / hide toggle
        self._pw_visible = False
        self.toggle_btn = tk.Button(
            outer,
            text="Show password",
            command=self._toggle_password,
            bg=BG_DARK, fg=TEXT_MUTED,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            borderwidth=0,
        )
        self.toggle_btn.pack(anchor="e")

        #  Strength meter (new user only) 

        if self.is_new_user:
            self.strength_var = tk.StringVar(value="")
            self.strength_label = tk.Label(
                outer,
                textvariable=self.strength_var,
                font=FONT_SMALL,
                bg=BG_DARK, fg=TEXT_MUTED,
            )
            self.strength_label.pack(anchor="w", pady=(4, 0))
            self.pw_var.trace_add("write", self._update_strength)

            # Confirm field
            tk.Label(
                outer, text="Confirm master password",
                font=FONT_SMALL,
                bg=BG_DARK, fg=TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", pady=(16, 0))

            self.confirm_var = tk.StringVar()
            self.confirm_entry = tk.Entry(
                outer,
                textvariable=self.confirm_var,
                show="●",
                width=36,
            )
            style_entry(self.confirm_entry)
            self.confirm_entry.pack(fill="x", pady=(4, 16))

        #  Error label 

        self.error_var = tk.StringVar(value="")
        tk.Label(
            outer,
            textvariable=self.error_var,
            font=FONT_SMALL,
            bg=BG_DARK, fg=DANGER,
            wraplength=360,
        ).pack(pady=(8, 0))

        #  Submit button 

        btn_text = "Create vault" if self.is_new_user else "Unlock vault"
        self.submit_btn = tk.Button(
            outer,
            text=btn_text,
            command=self._on_submit,
            width=24,
        )
        style_button(self.submit_btn)
        self.submit_btn.pack(pady=(16, 0))

        # Back button — returns to choice screen
        tk.Button(
            outer,
            text="← Back",
            command=self._build_choice_screen,
            bg=BG_DARK, fg=TEXT_MUTED,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            borderwidth=0,
        ).pack(pady=(10, 0))

        # Bind Enter and Escape
        self.root.bind("<Return>", lambda e: self._on_submit())
        self.root.bind("<Escape>",
                       lambda e: self._build_choice_screen())

    #  Strength meter 
    def _update_strength(self, *args):
     
        password = self.pw_var.get()
        if not password:
            self.strength_var.set("")
            return
        score, label, colour = check_strength(password)
        self.strength_var.set(f"Strength: {label}")
        self.strength_label.configure(fg=colour)

    #  Show / hide password 
    def _toggle_password(self):
        self._pw_visible = not self._pw_visible
        char = "" if self._pw_visible else "●"
        self.pw_entry.configure(show=char)
        self.toggle_btn.configure(
            text="Hide password"
            if self._pw_visible else "Show password"
        )

    #  Submit 
    def _on_submit(self):
        if self.is_new_user:
            self._create_vault()
        else:
            self._unlock_vault()

    #  New user — create vault 
    def _create_vault(self):
        password = self.pw_var.get()
        confirm  = self.confirm_var.get()

        if not password:
            self.error_var.set("Please enter a master password")
            return

        score, label, _ = check_strength(password)
        if score < 2:
            self.error_var.set(
                f"Password too weak ({label}). "
                "Use at least 8 characters with mixed types."
            )
            return

        if password != confirm:
            self.error_var.set("Passwords do not match")
            self.confirm_entry.configure(
                highlightbackground=DANGER,
                highlightcolor=DANGER,
            )
            return

        try:
            self.vault.create(password)
            self.error_var.set("")
            self._open_main_window()
        except Exception as e:
            self.error_var.set(f"Error creating vault: {e}")

    #  Returning user — unlock vault 
    def _unlock_vault(self):
        password = self.pw_var.get()

        if not password:
            self.error_var.set("Please enter your master password")
            return

        if self.manager.is_locked():
            self.error_var.set(
                "Too many wrong attempts. "
                "Please restart the app."
            )
            self.submit_btn.configure(state="disabled")
            return

        try:
            success = self.manager.verify(self.vault, password)
        except RuntimeError:
            self.error_var.set(
                "Too many wrong attempts. "
                "Please restart the app."
            )
            self.submit_btn.configure(state="disabled")
            return

        if success:
            self.error_var.set("")
            self._open_main_window()
        else:
            remaining = self.manager.attempts_remaining()
            if remaining > 0:
                self.error_var.set(
                    f"Wrong password. "
                    f"{remaining} attempt(s) remaining."
                )
                self.sub_label_var.set(
                    f"Attempts remaining: {remaining}"
                )
            else:
                self.error_var.set(
                    "Too many wrong attempts. "
                    "Please restart the app."
                )
                self.submit_btn.configure(state="disabled")

            self.pw_var.set("")
            self.pw_entry.focus()

    #  Open main window 
    # Clear screen and open the main vault window
    def _open_main_window(self):
        from ui.main_window import MainWindow

        for w in self.root.winfo_children():
            w.destroy()

        self.root.geometry("500x580")
        self.root.resizable(True, True)
        MainWindow(
            root=self.root,
            vault=self.vault,
            creds=self.creds,
            user_info=self.user_info,
        )