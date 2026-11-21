"""
main.py
Entry point for VaultKey.
Run this to launch the app: python main.py
"""

import tkinter as tk
from ui.login_window import LoginWindow


def main():
    root = tk.Tk()
    root.title("VaultKey")
    root.resizable(True, True)
    root.minsize(400, 480)
    root.geometry("460x520")

    try:
        root.iconbitmap("assets/icon.ico")
    except Exception:
        pass

    
    LoginWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()