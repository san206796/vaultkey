"""
ui/main_window.py

Main hub screen shown after vault is unlocked.
Three main options matching the proposal mockup:
  - Add password
  - View passwords
  - Delete password

Plus: sync to Drive, password generator, sign out.
"""

import tkinter as tk
from tkinter import messagebox
import threading

from core.vault import Vault
from core.drive_sync import upload_vault
from core.auth import logout
from ui.styles import (
    BG_DARK, BG_SECONDARY, ACCENT, ACCENT_BTN,
    TEXT_PRIMARY, TEXT_MUTED, BORDER, DANGER,
    FONT_TITLE, FONT_HEADING, FONT_BODY,
    FONT_SMALL, FONT_BUTTON,
    style_button,
)

# MainWindow class
class MainWindow:

    def __init__(self, root: tk.Tk, vault: Vault,
                 creds, user_info: dict):
        self.root      = root
        self.vault     = vault
        self.creds     = creds
        self.user_info = user_info

        self.root.title("VaultKey")
        self.root.configure(bg=BG_DARK)
        self.root.geometry("500x580")
        self.root.resizable(False, False)

        self._build_ui()

    #  Build UI 
    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG_DARK)
        outer.pack(expand=True, fill="both", padx=40, pady=30)

        #  Header 
        tk.Label(
            outer, text="VaultKey",
            font=FONT_TITLE,
            bg=BG_DARK, fg=TEXT_PRIMARY,
        ).pack()

        tk.Label(
            outer, text="Your passwords are safe",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(pady=(4, 8))

        # User email badge
        email_frame = tk.Frame(outer, bg=BG_SECONDARY,
                               highlightbackground=BORDER,
                               highlightthickness=1)
        email_frame.pack(pady=(0, 24))
        tk.Label(
            email_frame,
            text=self.user_info.get("email", ""),
            font=FONT_SMALL,
            bg=BG_SECONDARY, fg=TEXT_MUTED,
            padx=14, pady=4,
        ).pack()

        #  Main action buttons 
        # Add password
        add_btn = tk.Button(
            outer,
            text="＋   Add password",
            command=self._open_add,
            width=30,
        )
        style_button(add_btn)
        add_btn.pack(fill="x", pady=(0, 10))

        # View passwords
        view_btn = tk.Button(
            outer,
            text="🔍   View passwords",
            command=self._open_view,
            width=30,
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            font=FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            pady=10,
            borderwidth=1,
        )
        view_btn.pack(fill="x", pady=(0, 10))

        #  Stats row 
        separator = tk.Frame(outer, bg=BORDER, height=1)
        separator.pack(fill="x", pady=20)

        stats_frame = tk.Frame(outer, bg=BG_DARK)
        stats_frame.pack(fill="x")

        # Passwords stored
        self._stat_widget(
            stats_frame,
            str(self.vault.count()),
            "Passwords stored",
            col=0,
        )

        # Encryption strength
        self._stat_widget(
            stats_frame,
            "AES",
            "256-bit encryption",
            col=1,
        )

        # Status
        self._stat_widget(
            stats_frame,
            "✓",
            "Vault unlocked",
            col=2,
        )

        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)

        #  Footer buttons 
        separator2 = tk.Frame(outer, bg=BORDER, height=1)
        separator2.pack(fill="x", pady=20)

        footer = tk.Frame(outer, bg=BG_DARK)
        footer.pack(fill="x")

        # Sync to Drive
        sync_btn = tk.Button(
            footer,
            text="↑ Sync to Drive",
            command=self._sync_to_drive,
            bg=BG_DARK, fg=TEXT_MUTED,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            borderwidth=0,
        )
        sync_btn.pack(side="left")


        # Sign out
        signout_btn = tk.Button(
            footer,
            text="Sign out",
            command=self._sign_out,
            bg=BG_DARK, fg=DANGER,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            borderwidth=0,
        )
        signout_btn.pack(side="right")

        # Sync status label
        self.sync_var = tk.StringVar(value="")
        tk.Label(
            outer,
            textvariable=self.sync_var,
            font=FONT_SMALL,
            bg=BG_DARK, fg=ACCENT,
        ).pack(pady=(8, 0))

    #  Stat widget helper 
    def _stat_widget(self, parent, value: str, label: str, col: int):
        
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.grid(row=0, column=col, padx=8)

        tk.Label(
            frame, text=value,
            font=FONT_HEADING,
            bg=BG_DARK, fg=ACCENT,
        ).pack()

        tk.Label(
            frame, text=label,
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        ).pack()

    #  Navigation 
    #  Open add password screen
    def _open_add(self):
   
        from ui.add_password_window import AddPasswordWindow
        AddPasswordWindow(
            parent=self.root,
            vault=self.vault,
            on_close=self._refresh,
        )

    #  Open view/search passwords screen
    def _open_view(self):
      
        from ui.view_window import ViewWindow
        ViewWindow(
            parent=self.root,
            vault=self.vault,
        )

    #  Open delete password screen
    def _open_delete(self):

        from ui.delete_window import DeleteWindow
        DeleteWindow(
            parent=self.root,
            vault=self.vault,
            on_close=self._refresh,
        )

    #  Open password generator screen
    def _open_generator(self):
        
        from ui.generator_window import GeneratorWindow
        GeneratorWindow(parent=self.root)

    #  Sync to Drive 
    # When user clicks sync, disable button and show status. Run upload in background thread to avoid freezing UI. On success or failure, show message and re-enable button.
    def _sync_to_drive(self):
       
        self.sync_var.set("Syncing...")

        def do_sync():
            ok = upload_vault(self.creds)
            msg = "Synced to Drive ✓" if ok else "Sync failed ✗"
            self.root.after(0, lambda: self._on_sync_done(msg))

        threading.Thread(target=do_sync, daemon=True).start()

    # Sync completion handler — show message and clear after a few seconds.
    def _on_sync_done(self, msg: str):
        self.sync_var.set(msg)
     
        self.root.after(3000, lambda: self.sync_var.set(""))

    #  Refresh 
    # After adding or deleting a password, we need to refresh the main window to update the password count and reflect any changes. This method destroys all widgets and rebuilds the UI.
    def _refresh(self):
      
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.geometry("500x580")
        MainWindow(
            root=self.root,
            vault=self.vault,
            creds=self.creds,
            user_info=self.user_info,
        )

    #  Sign out 
    # When user clicks sign out, show confirmation dialog. If confirmed, log out and return to login screen.
    def _sign_out(self):
        confirm = messagebox.askyesno(
            "Sign out",
            "Sign out of VaultKey?\n\n"
            "Your vault stays encrypted on this device.",
        )
        if confirm:
            logout()
            for widget in self.root.winfo_children():
                widget.destroy()
            self.root.geometry("460x500")
            self.root.resizable(False, False)

            from ui.login_window import LoginWindow
            LoginWindow(root=self.root)