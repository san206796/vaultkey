"""
ui/login_window.py

First screen the user sees when VaultKey opens.
Handles Google sign-in then decides what comes next:
  - New user     → master password creation screen
  - Returning    → master password entry screen
"""

import tkinter as tk
from tkinter import messagebox
import threading

from core.auth import google_login, get_user_info, _load_saved_token
from core.vault import Vault
from core.drive_sync import download_vault
from ui.styles import (
    BG_DARK, BG_SECONDARY, ACCENT, ACCENT_BTN,
    TEXT_PRIMARY, TEXT_MUTED, BORDER,
    FONT_TITLE, FONT_BODY, FONT_SMALL, FONT_BUTTON,
    style_button, style_label,
)

# LoginWindow class
class LoginWindow:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.configure(bg=BG_DARK)
        self.root.geometry("460x500")
        self.root.title("VaultKey")

        self._build_ui()
        self._try_auto_login()

    #  Build UI 
    def _build_ui(self):
        # Outer frame — centres everything
        outer = tk.Frame(self.root, bg=BG_DARK)
        outer.pack(expand=True, fill="both", padx=60, pady=40)

        # Lock icon
        try:
            from PIL import Image, ImageTk
            img = Image.open("assets/icon.png").resize(
                (100, 100), Image.LANCZOS
            )
            self._icon_img = ImageTk.PhotoImage(img)
            tk.Label(
                outer,
                image=self._icon_img,
                bg=BG_DARK,
            ).pack(pady=(0, 16))
        except Exception as e:
            print(f"Error loading icon: {e}")
            # Fallback to emoji if image not found
            tk.Label(
                outer, text="🔐",
                font=("Segoe UI Emoji", 56),
                bg=BG_DARK, fg=TEXT_PRIMARY,
            ).pack(pady=(0, 16))

        # App name
        title = tk.Label(outer, text="VaultKey",
                         font=FONT_TITLE, bg=BG_DARK, fg=TEXT_PRIMARY)
        title.pack()

        # Tagline
        tagline = tk.Label(outer,
                           text="Your Personal Password Manager",
                           font=FONT_SMALL, bg=BG_DARK, fg=TEXT_MUTED)
        tagline.pack(pady=(6, 40))

        # Sign in button
        self.login_btn = tk.Button(
            outer,
            text="Sign in with Google",
            command=self._start_login,
            width=24,
        )
        style_button(self.login_btn)
        self.login_btn.pack(pady=(0, 16))

        # Status label
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(
            outer,
            textvariable=self.status_var,
            font=FONT_SMALL,
            bg=BG_DARK,
            fg=TEXT_MUTED,
            wraplength=340,
        )
        self.status_label.pack()

        # Footer
        footer = tk.Label(
            outer,
            text="AES-256 encrypted  ·  Google Drive backup",
            font=FONT_SMALL,
            bg=BG_DARK,
            fg=TEXT_MUTED,
        )
        footer.pack(side="bottom", pady=(0, 0))

    #  Auto login 
    # On app start, check for saved Google credentials and try to use them for silent login. If valid, skip sign-in button and go straight to next screen. 
    # If not valid or no token, do nothing and show sign-in button as normal.
    def _try_auto_login(self):
        
        creds = _load_saved_token()
        if creds and creds.valid:
            try:
                user_info = get_user_info(creds)
                self.status_var.set(f"Welcome back, {user_info['name']}")
                # Small delay so user sees the welcome message
                self.root.after(800, lambda: self._open_next_screen(creds, user_info))
            except Exception:
                pass  # Token stale — show login button normally

    #  Login flow 
    # When user clicks sign-in, disable button and show status. 
    def _start_login(self):
     
        self.login_btn.configure(state="disabled")
        self.status_var.set("Opening browser for Google sign-in...")

        # Run OAuth in background thread so UI does not freeze
        thread = threading.Thread(target=self._do_login, daemon=True)
        thread.start()

    # Background login method
    def _do_login(self):
    
        try:
            creds     = google_login()
            user_info = get_user_info(creds)
            # Schedule UI update back on main thread
            self.root.after(0, lambda: self._on_login_success(creds, user_info))
        except Exception as e:
            self.root.after(0, lambda: self._on_login_failed(str(e)))

    # Login success and failure handlers 
    #  On success, show welcome message then open next screen.
    def _on_login_success(self, creds, user_info):
        
        self.status_var.set(f"Signed in as {user_info['email']}")
        self.root.after(600, lambda: self._open_next_screen(creds, user_info))

    # On failure, re-enable login button and show error message.
    def _on_login_failed(self, error_msg):
       
        self.login_btn.configure(state="normal")
        self.status_var.set("")
        messagebox.showerror(
            "Sign-in failed",
            f"Could not sign in with Google.\n\n{error_msg}"
        )

    #  Open next screen 
    # After Google sign-in decide what to show next. Check if vault exists locally or on Drive.
    def _open_next_screen(self, creds, user_info):
      
        from ui.master_password_window import MasterPasswordWindow

        vault = Vault()

        # If no local vault try to download from Drive
        if not vault.vault_exists():
            self.status_var.set("Checking Google Drive for backup...")
            self.root.update()
            try:
                download_vault(creds)
            except Exception:
                pass  # No backup exists — this is a new user

        # Clear this window and open master password screen
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.geometry("460x520")
        MasterPasswordWindow(
            root=self.root,
            creds=creds,
            user_info=user_info,
            vault=vault,
        )