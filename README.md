# VaultKey
 
A secure desktop password manager built in Python. VaultKey stores your credentials in an encrypted local vault protected by a master password, with optional backup to Google Drive.
 
Built as my final-year Honours project (COMP390) for my BSc in Computer Science at the University of Liverpool.
 
## Features
 
- **Strong encryption:** vault data is encrypted with AES-256-GCM, which also detects tampering.
- **Master password protection:** the encryption key is derived from your master password using PBKDF2, so the password itself is never stored.
- **Password manager basics:** add, view and edit saved entries from a simple desktop interface.
- **Password generator:** create strong random passwords with a built-in generator window.
- **Google Drive sync:** back up and sync your encrypted vault using OAuth 2.0.
- **Standalone build:** can be packaged into a single executable with PyInstaller.

## Tech stack
 
| Area | Technology |
| --- | --- |
| Language | Python 3 |
| GUI | Tkinter |
| Encryption | AES-256-GCM |
| Key derivation | PBKDF2 |
| Cloud sync | Google Drive API, OAuth 2.0 |
| Packaging | PyInstaller |
 
## Project structure
 
```
VaultKey/
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── assets/                  # Images and static files
├── core/
│   ├── auth.py              # Master password and login logic
│   ├── encryption.py        # AES-256-GCM encryption and decryption
│   ├── vault.py             # Reading, writing and managing entries
│   ├── generator.py         # Password generator
│   └── drive_sync.py        # Google Drive sync via OAuth 2.0
└── ui/
    ├── login_window.py
    ├── master_password_window.py
    ├── main_window.py
    ├── add_password_window.py
    ├── edit_password_window.py
    ├── view_window.py
    ├── generator_window.py
    └── styles.py
```
 
## Getting started
 
### 1. Clone the repository
 
```bash
git clone https://github.com/san206796/vaultkey.git
cd vaultkey
```
 
### 2. Create a virtual environment (recommended)
 
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
```
 
### 3. Install dependencies
 
```bash
pip install -r requirements.txt
```
 
### 4. Run the app
 
```bash
python main.py
```
 
On first launch you will be asked to create a master password. **Remember it: it cannot be recovered**, because it is the only thing that unlocks your vault.
 
## Google Drive sync (optional)
 
Drive sync needs your own Google OAuth credentials. This repository does not include any, for security reasons.
 
1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Google Drive API** for that project.
3. Create an **OAuth client ID** (application type: Desktop app).
4. Download the credentials file, rename it `client_secrets.json`, and place it in the project root next to `main.py`.
5. On first sync, a browser window opens so you can sign in and grant access.
The app works fully offline without this step.
 
## Building an executable
 
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```
 
The executable appears in the `dist/` folder. If your build needs the `assets` folder, include it with PyInstaller's `--add-data` option.
 
## Security notes
 
- Only encrypted data is stored locally and uploaded to Drive.
- Never commit `client_secrets.json`, `token.json` or your vault file. They are listed in `.gitignore`.
- VaultKey is an academic and portfolio project. It has not been independently audited, so don't rely on it as your only password manager.
## What I learned
 
- Applying modern cryptography correctly: authenticated encryption, key derivation and secure handling of secrets.
- Structuring a Python application into separate core logic and UI layers.
- Integrating a third-party API with OAuth 2.0.
- Planning and delivering a full project: proposal, technology evaluation, implementation, documentation and presentation.
## Author
 
**Sanjose Saji**
BSc Computer Science, University of Liverpool
 
GitHub: [san206796](https://github.com/san206796)
 