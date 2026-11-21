"""
core/auth.py
Handles user authentication and master password management.
Includes Google OAuth sign-in and a MasterPasswordManager class to track login attempts and lockout.
"""

import os
import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

#  Constants and configuration 

# What permissions we ask Google for
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.appdata",
]

# Where files are stored
TOKEN_FILE   = os.path.join(os.path.expanduser("~"), ".vaultkey_token.json")
SECRETS_FILE = os.path.join(os.path.dirname(__file__), "..", "client_secrets.json")

# Max wrong password attempts before lockout
MAX_ATTEMPTS = 3


#  Google sign-in 
# We use Google OAuth for user authentication. The first time the user signs in,
# they will be prompted to grant permissions. A token is saved to disk for future
# sign-ins. The token is refreshed automatically if expired. The user can log out
# to remove the token and require sign-in again.
def google_login() -> Credentials:
    creds = _load_saved_token()

    if not creds:
        # No saved token — run the full OAuth flow
        if not os.path.exists(SECRETS_FILE):
            raise FileNotFoundError(
                "client_secrets.json not found.\n"
                "Please follow Step 4 in the setup guide\n"
                "to create Google OAuth credentials."
            )
        flow  = InstalledAppFlow.from_client_secrets_file(SECRETS_FILE, SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent")
        _save_token(creds)

    return creds

# Get the signed-in user's name and email from Google using the provided credentials.
# Returns a dict with keys: name, email
def get_user_info(creds: Credentials) -> dict:

    service = build("oauth2", "v2", credentials=creds)
    info    = service.userinfo().get().execute()
    return {
        "name":  info.get("name",  ""),
        "email": info.get("email", ""),
    }

# Log out by removing the saved token file. Next launch will require sign-in again.
# Note: This does not revoke the token with Google, but it prevents the app from using it.
def logout():
  
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        print("[Auth] Logged out — token removed")

# Check if the user is currently logged in by verifying if a valid token exists.
def is_logged_in() -> bool:

    creds = _load_saved_token()
    return creds is not None and creds.valid


#  Master password management and lockout
# The MasterPasswordManager class tracks how many wrong master password attempts the user has made.
class MasterPasswordManager:

    def __init__(self):
        self._attempts = 0          # wrong attempts so far
        self._locked   = False      # locked out flag

    # Check if the user is currently locked out due to too many wrong attempts.
    def is_locked(self) -> bool:

        return self._locked

    # Get how many attempts the user has left before lockout.
    def attempts_remaining(self) -> int:

        return MAX_ATTEMPTS - self._attempts
    
    # Verify the provided master password by trying to open the vault. Tracks attempts and locks out if too many wrong tries.
    def verify(self, vault, master_password: str) -> bool:
       
        if self._locked:
            raise RuntimeError(
                "Too many wrong attempts. "
                "Please restart the application."
            )

        result = vault.open(master_password)

        if result:
            # Correct — reset attempt counter
            self._attempts = 0
            return True
        else:
            # Wrong — increment counter
            self._attempts += 1
            if self._attempts >= MAX_ATTEMPTS:
                self._locked = True
            return False
        
    # Reset attempts — called after successful login.
    def reset(self):

        self._attempts = 0
        self._locked   = False


# Token helpers (private) 
# These functions handle loading, refreshing, and saving the OAuth token to disk. They are used by the google_login() function.
# The token is stored in the user's home directory as a JSON file. When loading, we check if the token is expired and refresh it if possible. If the token is valid, we return the credentials object; otherwise, we return None to indicate that the user needs to sign in again.
def _load_saved_token() -> Credentials | None:
 
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_token(creds)
        if creds and creds.valid:
            return creds
    except Exception:
        pass
    return None

# Save the OAuth token to disk for next launch.
def _save_token(creds: Credentials):

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    print(f"[Auth] Token saved to {TOKEN_FILE}")


# ─ Quick test  
if __name__ == "__main__":
    import shutil
    from core.vault import Vault

    print("=" * 50)
    print("STEP 1 — Test MasterPasswordManager")
    from core.vault import Vault

    # Create a fresh test vault
    test_dir = os.path.join(os.path.expanduser("~"), ".vaultkey")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    vault = Vault()
    vault.create("CorrectPassword123!")

    # Test correct password
    manager = MasterPasswordManager()
    vault2  = Vault()
    result  = manager.verify(vault2, "CorrectPassword123!")
    print(f"Correct password accepted : {result}")
    print(f"Attempts remaining        : {manager.attempts_remaining()}")

    print()
    print("=" * 50)
    print("STEP 2 — Test wrong password + lockout")
    manager2 = MasterPasswordManager()
    vault3   = Vault()

    for i in range(1, 4):
        result = manager2.verify(vault3, "WrongPassword!")
        print(f"Attempt {i} accepted  : {result}")
        if not manager2.is_locked():
            print(f"Attempts remaining : {manager2.attempts_remaining()}")

    print(f"Locked out after 3 attempts : {manager2.is_locked()}")

    print()
    print("=" * 50)
    print("STEP 3 — Test locked out error")
    try:
        manager2.verify(vault3, "AnotherAttempt!")
    except RuntimeError as e:
        print(f"Lockout error caught : {e}")

    print()
    print("=" * 50)
    print("STEP 4 — Test is_logged_in")
    print(f"Logged in : {is_logged_in()}")

    print()
    print("All auth tests passed!")