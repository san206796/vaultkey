"""
ui/view_window.py

Screen for viewing, searching, and deleting stored passwords.
- Search bar filters entries in real time
- Click entry to see full details
- Copy username / password buttons
- Delete button shows inline confirmation before deleting
- Edit button requires master password then opens edit form
"""

import tkinter as tk
import pyperclip

from core.vault import Vault
from ui.styles import (
    BG_DARK, BG_SECONDARY, BG_INPUT,
    ACCENT, ACCENT_BTN, TEXT_PRIMARY, TEXT_MUTED,
    BORDER, DANGER,
    FONT_HEADING, FONT_BODY, FONT_SMALL,
    FONT_BUTTON, FONT_MONO,
    style_button, style_entry,
)

# ViewWindow class
class ViewWindow:
 
    def __init__(self, parent: tk.Tk, vault: Vault,
                 on_close=None):
        self.vault          = vault
        self.on_close       = on_close
        self._selected      = None
        self._confirm_frame = None
        self._entries       = []

        self.win = tk.Toplevel(parent)
        self.win.title("View Passwords")
        self.win.configure(bg=BG_DARK)
        self.win.geometry("680x580")
        self.win.resizable(True, True)
        self.win.grab_set()

        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._load_entries()

    #  Build UI 

    def _build_ui(self):

        #  Top bar 
        topbar = tk.Frame(
            self.win, bg=BG_SECONDARY,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        topbar.pack(fill="x")

        inner_top = tk.Frame(topbar, bg=BG_SECONDARY)
        inner_top.pack(fill="x", padx=20, pady=12)

        tk.Label(
            inner_top, text="Search passwords",
            font=FONT_HEADING,
            bg=BG_SECONDARY, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        # Search row
        search_row = tk.Frame(inner_top, bg=BG_SECONDARY)
        search_row.pack(fill="x")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        self.search_entry = tk.Entry(
            search_row,
            textvariable=self.search_var,
            width=40,
        )
        style_entry(self.search_entry)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.insert(0, "Search by name, URL or username...")
        self.search_entry.bind("<FocusIn>",
                               self._clear_search_placeholder)
        self.search_entry.bind("<FocusOut>",
                               self._set_search_placeholder)
        self.search_entry.focus()

        tk.Button(
            search_row,
            text="Clear",
            command=self._clear_search,
            bg=BG_SECONDARY, fg=TEXT_MUTED,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=10,
        ).pack(side="left", padx=(8, 0))

        # Count label
        self.count_var = tk.StringVar(value="")
        tk.Label(
            inner_top,
            textvariable=self.count_var,
            font=FONT_SMALL,
            bg=BG_SECONDARY, fg=TEXT_MUTED,
        ).pack(anchor="w", pady=(6, 0))

        #  Main area 
        main_area = tk.Frame(self.win, bg=BG_DARK)
        main_area.pack(fill="both", expand=True)

        #  Left panel — list 
        list_frame = tk.Frame(main_area, bg=BG_DARK, width=220)
        list_frame.pack(side="left", fill="y", padx=(16, 0), pady=16)
        list_frame.pack_propagate(False)

        tk.Label(
            list_frame, text="ENTRIES",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 6))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            font=FONT_BODY,
            selectbackground=ACCENT_BTN,
            selectforeground=TEXT_PRIMARY,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
            width=26,
        )
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        scrollbar.configure(command=self.listbox.yview)

        # Vertical divider
        tk.Frame(main_area, bg=BORDER, width=1).pack(
            side="left", fill="y", pady=16
        )

        #  Right panel — detail 
        self.detail_frame = tk.Frame(main_area, bg=BG_DARK)
        self.detail_frame.pack(
            side="left", fill="both",
            expand=True, padx=16, pady=16,
        )

        self._show_empty_detail()

    #  Entry list 
    #  Load entries from vault and display in the listbox. Called on startup
    def _load_entries(self, query: str = ""):
       
        self.listbox.delete(0, "end")
        self._entries = (
            self.vault.search(query)
            if query else
            self.vault.get_all()
        )

        for entry in self._entries:
            display = entry["title"] or entry["url"]
            self.listbox.insert("end", f"  {display}")

        count = len(self._entries)
        total = self.vault.count()
        if query:
            self.count_var.set(
                f"{count} result{'s' if count != 1 else ''} "
                f"of {total} passwords"
            )
        else:
            self.count_var.set(
                f"{total} password{'s' if total != 1 else ''} stored"
            )

    # Search bar callbacks
    def _on_search(self, *args):
    
        query = self.search_var.get().strip()
        if query == "Search by name, URL or username...":
            query = ""
        self._load_entries(query)
        self._show_empty_detail()

    # Clear search and show all entries
    def _clear_search(self):
        self.search_var.set("")
        self.search_entry.delete(0, "end")
        self._load_entries()
        self._show_empty_detail()

    # Search placeholder behavior
    def _clear_search_placeholder(self, event):
        if self.search_entry.get() == \
                "Search by name, URL or username...":
            self.search_entry.delete(0, "end")
            self.search_entry.configure(fg=TEXT_PRIMARY)

    # Restore placeholder if search is empty
    def _set_search_placeholder(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(
                0, "Search by name, URL or username..."
            )
            self.search_entry.configure(fg=TEXT_MUTED)

    #  Detail panel 
    #  Called when user clicks an entry in the list. Shows full details and
    def _on_select(self, event):
       
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if index < len(self._entries):
            self._selected      = self._entries[index]
            self._confirm_frame = None
            self._show_detail(self._selected)

    # Copy value to clipboard and show temporary confirmation
    def _show_empty_detail(self):

        for w in self.detail_frame.winfo_children():
            w.destroy()

        tk.Label(
            self.detail_frame,
            text="Select an entry\nto view details",
            font=FONT_BODY,
            bg=BG_DARK, fg=TEXT_MUTED,
            justify="center",
        ).pack(expand=True)

    # Copy to clipboard
    def _show_detail(self, entry: dict):

        for w in self.detail_frame.winfo_children():
            w.destroy()

        # Scrollable frame for detail content
        canvas = tk.Canvas(
            self.detail_frame,
            bg=BG_DARK,
            highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(
            self.detail_frame,
            orient="vertical",
            command=canvas.yview,
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg=BG_DARK)
        canvas_window = canvas.create_window(
            (0, 0), window=content, anchor="nw"
        )

    # Make canvas resize with window
        def on_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_resize)

        # Make canvas scroll with mouse wheel
        def on_content_resize(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        content.bind("<Configure>", on_content_resize)

        #  Title 
        tk.Label(
            content,
            text=entry["title"] or entry["url"],
            font=FONT_HEADING,
            bg=BG_DARK, fg=TEXT_PRIMARY,
            anchor="w",
            wraplength=360,
        ).pack(anchor="w", pady=(0, 16))

        #  Fields 
        self._detail_field(content, "URL",
                           entry.get("url",      ""))
        self._detail_field(content, "USERNAME",
                           entry.get("username", ""))
        self._detail_field(content, "PASSWORD",
                           entry.get("password", ""),
                           secret=True)

        if entry.get("notes"):
            self._detail_field(content, "NOTES",
                               entry["notes"])

        #  Timestamps 
        tk.Frame(
            content, bg=BORDER, height=1
        ).pack(fill="x", pady=10)

        tk.Label(
            content,
            text=f"Added:   {entry.get('created_at', '')}",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            content,
            text=f"Updated: {entry.get('updated_at', '')}",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        #  Delete and Edit buttons side by side 
        tk.Frame(
            content, bg=BORDER, height=1
        ).pack(fill="x", pady=12)

        self._confirm_frame = None

        btn_row = tk.Frame(content, bg=BG_DARK)
        btn_row.pack(fill="x")

        # Delete — left side red
        tk.Button(
            btn_row,
            text="🗑  Delete this entry",
            command=lambda: self._show_confirm(content, entry),
            bg=DANGER, fg="#FFFFFF",
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=12, pady=6,
        ).pack(side="left")

        # Edit — right side teal
        tk.Button(
            btn_row,
            text="✎  Edit",
            command=lambda: self._prompt_master_for_edit(entry),
            bg=ACCENT_BTN, fg="#FFFFFF",
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=12, pady=6,
        ).pack(side="right")

    #  Detail field helper
    def _detail_field(self, parent, label: str,
                      value: str, secret: bool = False):
        tk.Label(
            parent,
            text=label,
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        row = tk.Frame(parent, bg=BG_DARK)
        row.pack(fill="x", pady=(2, 12))

        display = "●" * len(value) if secret else value

        val_label = tk.Label(
            row,
            text=display,
            font=FONT_MONO if secret else FONT_BODY,
            bg=BG_DARK, fg=TEXT_PRIMARY,
            anchor="w",
            wraplength=260,
        )
        val_label.pack(side="left", fill="x", expand=True)

        if secret:
            tk.Button(
                row, text="Show",
                command=lambda lbl=val_label, v=value:
                    self._prompt_master_password(lbl, v),
                bg=BG_SECONDARY, fg=TEXT_MUTED,
                font=FONT_SMALL,
                relief="flat", cursor="hand2",
                padx=6,
            ).pack(side="left", padx=(4, 4))

        tk.Button(
            row,
            text="Copy",
            command=lambda v=value: self._copy(v),
            bg=BG_SECONDARY, fg=ACCENT,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=8,
        ).pack(side="left")

    #  Show password with master password verification 
    # When user clicks "Show" on a password field, ask for master password
    def _prompt_master_password(self, label: tk.Label,
                                password: str):

        prompt = tk.Toplevel(self.win)
        prompt.title("Verify identity")
        prompt.configure(bg=BG_DARK)
        prompt.geometry("360x260")
        prompt.resizable(False, False)
        prompt.grab_set()

        outer = tk.Frame(prompt, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(
            outer, text="🔒  Confirm your identity",
            font=FONT_HEADING,
            bg=BG_DARK, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            outer,
            text="Enter your master password to view this password.",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            wraplength=300,
        ).pack(anchor="w", pady=(0, 16))

        tk.Label(
            outer, text="Master password",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x")

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
        ).pack(anchor="w", pady=(0, 12))

        btn_row = tk.Frame(outer, bg=BG_DARK)
        btn_row.pack(fill="x")

        # Verify master password and show the password if correct
        def verify():
            entered = pw_var.get()
            if not entered:
                error_var.set("Please enter your master password")
                return
            test_vault = Vault()
            if test_vault.open(entered):
                prompt.destroy()
                label.configure(text=password)
                self.win.after(
                    30000,
                    lambda: label.configure(
                        text="●" * len(password)
                    )
                )
                self.count_var.set(
                    "Password visible for 30 seconds"
                )
                self.win.after(
                    30000,
                    lambda: self.count_var.set("")
                )
            else:
                error_var.set("Wrong master password")
                pw_var.set("")
                pw_entry.focus()

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
            text="Confirm",
            command=verify,
            bg=ACCENT_BTN, fg="#FFFFFF",
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=12, pady=6,
        ).pack(side="right")

        prompt.bind("<Return>", lambda e: verify())
        prompt.bind("<Escape>", lambda e: prompt.destroy())

    #  Edit with master password verification 
    # When user clicks "Edit", ask for master password then open edit form if
    def _prompt_master_for_edit(self, entry: dict):
      
        prompt = tk.Toplevel(self.win)
        prompt.title("Verify identity")
        prompt.configure(bg=BG_DARK)
        prompt.geometry("360x240")
        prompt.resizable(False, False)
        prompt.grab_set()

        outer = tk.Frame(prompt, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(
            outer,
            text="🔒  Verify identity to edit",
            font=FONT_HEADING,
            bg=BG_DARK, fg=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            outer,
            text="Enter your master password to edit this entry.",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            wraplength=300,
        ).pack(anchor="w", pady=(0, 14))

        tk.Label(
            outer, text="Master password",
            font=FONT_SMALL,
            bg=BG_DARK, fg=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x")

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
        ).pack(anchor="w", pady=(0, 12))

        btn_row = tk.Frame(outer, bg=BG_DARK)
        btn_row.pack(fill="x")

        # Verify master password and show the password if correct
        def verify():
            entered = pw_var.get()
            if not entered:
                error_var.set("Please enter your master password")
                return
            test_vault = Vault()
            if test_vault.open(entered):
                prompt.destroy()
                self._open_edit(entry)
            else:
                error_var.set("Wrong master password")
                pw_var.set("")
                pw_entry.focus()

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
            text="Verify",
            command=verify,
            bg=ACCENT_BTN, fg="#FFFFFF",
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=12, pady=6,
        ).pack(side="right")

        prompt.bind("<Return>", lambda e: verify())
        prompt.bind("<Escape>", lambda e: prompt.destroy())

    # Open edit window after identity verified
    def _open_edit(self, entry: dict):
    
        from ui.edit_password_window import EditPasswordWindow
        EditPasswordWindow(
            parent=self.win,
            vault=self.vault,
            entry=entry,
            on_close=self._on_edit_done,
        )

    # Callback after edit to refresh the list and detail view
    def _on_edit_done(self):
        query = self.search_var.get().strip()
        if query == "Search by name, URL or username...":
            query = ""
        self._load_entries(query)
        self._show_empty_detail()

    #  Delete confirmation 
    # When user clicks "Delete", show inline confirmation with master password
    def _show_confirm(self, parent, entry: dict):
       
        if self._confirm_frame:
            self._confirm_frame.destroy()
            self._confirm_frame = None

        self._confirm_frame = tk.Frame(
            parent,
            bg=BG_SECONDARY,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self._confirm_frame.pack(fill="x", pady=(8, 0))

        inner = tk.Frame(self._confirm_frame, bg=BG_SECONDARY)
        inner.pack(fill="x", padx=14, pady=12)

        tk.Label(
            inner,
            text="🔒  Verify identity to delete",
            font=FONT_SMALL,
            bg=BG_SECONDARY, fg=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            inner,
            text="Enter your master password to proceed.",
            font=FONT_SMALL,
            bg=BG_SECONDARY, fg=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(
            inner, text="Master password",
            font=FONT_SMALL,
            bg=BG_SECONDARY, fg=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        pw_var = tk.StringVar()
        pw_entry = tk.Entry(
            inner,
            textvariable=pw_var,
            show="●", width=30,
        )
        style_entry(pw_entry)
        pw_entry.pack(fill="x", pady=(4, 8))
        pw_entry.focus()

        error_var = tk.StringVar(value="")
        tk.Label(
            inner,
            textvariable=error_var,
            font=FONT_SMALL,
            bg=BG_SECONDARY, fg=DANGER,
        ).pack(anchor="w", pady=(0, 8))

        btn_row = tk.Frame(inner, bg=BG_SECONDARY)
        btn_row.pack(fill="x")

    # Verify master password and show the delete confirmation if correct
        def verify_then_confirm():
            entered = pw_var.get()
            if not entered:
                error_var.set("Please enter your master password")
                return
            test_vault = Vault()
            if test_vault.open(entered):
                self._show_delete_confirmation(entry)
            else:
                error_var.set("Wrong master password")
                pw_var.set("")
                pw_entry.focus()

        tk.Button(
            btn_row,
            text="Cancel",
            command=self._cancel_confirm,
            bg=BG_DARK, fg=TEXT_MUTED,
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=10, pady=6,
        ).pack(side="left")

        tk.Button(
            btn_row,
            text="Verify",
            command=verify_then_confirm,
            bg=ACCENT_BTN, fg="#FFFFFF",
            font=FONT_SMALL,
            relief="flat", cursor="hand2",
            padx=10, pady=6,
        ).pack(side="right")

        pw_entry.bind("<Return>", lambda e: verify_then_confirm())

    # After master password verified, show final delete confirmation with entry details and yes/no buttons
    def _show_delete_confirmation(self, entry: dict):

        if self._confirm_frame:
            self._confirm_frame.destroy()
            self._confirm_frame = None

        self._confirm_frame = tk.Frame(
            self.detail_frame,
            bg="#1A0A0A",
            highlightbackground=DANGER,
            highlightthickness=1,
        )
        self._confirm_frame.pack(fill="x", pady=(8, 0))

        inner = tk.Frame(self._confirm_frame, bg="#1A0A0A")
        inner.pack(fill="x", padx=14, pady=14)

        tk.Label(
            inner,
            text="⚠  Caution — permanent deletion",
            font=FONT_HEADING,
            bg="#1A0A0A", fg=DANGER,
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(
            inner, text="You are about to permanently delete:",
            font=FONT_SMALL,
            bg="#1A0A0A", fg=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        detail_card = tk.Frame(
            inner, bg=BG_SECONDARY,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        detail_card.pack(fill="x", pady=(0, 10))

        card_inner = tk.Frame(detail_card, bg=BG_SECONDARY)
        card_inner.pack(fill="x", padx=12, pady=8)

        for key, val in [
            ("Name",     entry.get("title") or entry.get("url", "")),
            ("URL",      entry.get("url",      "")),
            ("Username", entry.get("username", "")),
        ]:
            row = tk.Frame(card_inner, bg=BG_SECONDARY)
            row.pack(fill="x", pady=2)
            tk.Label(
                row, text=f"{key}:",
                font=FONT_SMALL,
                bg=BG_SECONDARY, fg=TEXT_MUTED,
                width=10, anchor="w",
            ).pack(side="left")
            tk.Label(
                row, text=val,
                font=FONT_SMALL,
                bg=BG_SECONDARY, fg=TEXT_PRIMARY,
                anchor="w",
            ).pack(side="left")

        tk.Label(
            inner,
            text="This action cannot be undone.\n"
                 "The password will be permanently removed from your vault.",
            font=FONT_SMALL,
            bg="#1A0A0A", fg=DANGER,
            justify="left",
            anchor="w",
            wraplength=340,
        ).pack(anchor="w", pady=(0, 14))

        btn_row = tk.Frame(inner, bg="#1A0A0A")
        btn_row.pack(fill="x")

        tk.Button(
            btn_row,
            text="No — don't delete",
            command=self._cancel_confirm,
            bg=BG_SECONDARY, fg=TEXT_PRIMARY,
            font=FONT_BUTTON,
            relief="flat", cursor="hand2",
            padx=14, pady=8,
        ).pack(side="left")

        tk.Button(
            btn_row,
            text="Yes — delete",
            command=lambda: self._confirm_delete(entry),
            bg=DANGER, fg="#FFFFFF",
            font=FONT_BUTTON,
            relief="flat", cursor="hand2",
            padx=14, pady=8,
        ).pack(side="right")

    # Remove the confirm box — nothing deleted.
    def _cancel_confirm(self):
        if self._confirm_frame:
            self._confirm_frame.destroy()
            self._confirm_frame = None

    # User confirmed — delete the entry from vault.
    def _confirm_delete(self, entry: dict):
        title   = entry.get("title") or entry.get("url", "this entry")
        success = self.vault.delete(entry["id"])

        if success:
            self._load_entries(self.search_var.get().strip())
            self._show_empty_detail()
            self._selected      = None
            self._confirm_frame = None
            self.count_var.set(f"'{title}' deleted successfully ✓")
            if self.on_close:
                self.on_close()
            self.win.after(2500, lambda: self._on_search())
        else:
            self.count_var.set("Error — could not delete entry")

    #  Copy to clipboard 

    def _copy(self, value: str):
        """Copy value to clipboard and show brief confirmation."""
        pyperclip.copy(value)
        self.count_var.set("Copied to clipboard ✓")
        self.win.after(2000, lambda: self._on_search())

    #  Close 

    def _on_close(self):
        self.win.destroy()
        if self.on_close:
            self.on_close()