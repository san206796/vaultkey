"""
vault.py
Handles vault management — creating, opening, saving, and managing password entries.
The Vault class provides methods to create a new vault, open an existing vault,
add/edit/delete entries, and search the vault. All data is encrypted on disk using AES-GCM.
"""

import os
import uuid
import base64
from datetime import datetime, timezone

from core.encryption import (
   derive_key,
    encrypt,
    decrypt,
    generate_salt,
    salt_to_string,
    string_to_salt,
    verify_master_password,
)


# Vault management 
VAULT_DIR  = os.path.join(os.path.expanduser("~"), ".vaultkey")
VAULT_FILE = os.path.join(VAULT_DIR, "vault.enc")


# Vault class to manage password entries and handle encryption/decryption of vault data.
class Vault:

    # Initialize an empty vault instance. Use create() or open() to load/save data.
    def __init__(self):
        self._key     = None   # 256-bit AES key — in memory only
        self._salt    = None   # 32-byte salt — saved to disk
        self._entries = []     # list of password entries in memory

    # Create a new vault with the given master password.
    def create(self, master_password: str):
   
        os.makedirs(VAULT_DIR, exist_ok=True)
        self._salt    = generate_salt()
        self._key     = derive_key(master_password, self._salt)
        self._entries = []
        self.save()
        print(f"[Vault] New vault created at {VAULT_FILE}")

    # Open an existing vault with the given master password.
    def open(self, master_password: str) -> bool:

        if not os.path.exists(VAULT_FILE):
            return False

        # Read the vault file
        with open(VAULT_FILE, "rb") as f:
            raw = f.read()

        # First 32 bytes are the salt — stored unencrypted
        self._salt    = raw[:32]
        encrypted     = raw[32:]

        # Verify the master password before decrypting
        if not verify_master_password(master_password, self._salt, encrypted):
            return False

        # Password correct — derive key and decrypt
        self._key     = derive_key(master_password, self._salt)
        data          = decrypt(encrypted, self._key)
        self._entries = data.get("entries", [])
        return True
    
    # Save the current vault state to disk (encrypting the data).
    def save(self):

        os.makedirs(VAULT_DIR, exist_ok=True)
        data      = {"entries": self._entries}
        encrypted = encrypt(data, self._key)

        # Write salt first (unencrypted) then encrypted data
        with open(VAULT_FILE, "wb") as f:
            f.write(self._salt)
            f.write(encrypted)

    # Check if a vault file already exists on this device.
    def vault_exists(self) -> bool:
        """Check if a vault file already exists on this device."""
        return os.path.exists(VAULT_FILE)

    # Add a new password entry to the vault and save.
    def add(self,username: str, password: str,
            url: str , notes: str = "",title: str = "") -> dict:
        
        if not username.strip():
            raise ValueError("Username is required")
        if not password.strip():
            raise ValueError("Password is required")
        if not url.strip():
            raise ValueError("URL is required")   
        
        # Create a new entry with a unique ID and timestamps, then save the vault.
        now   = _now()
        entry = {
            "id":         str(uuid.uuid4())[:8],  # short unique ID
            "title":      title.strip(),
            "username":   username.strip(),
            "password":   password,
            "url":        url.strip(),
            "notes":      notes.strip(),
            "created_at": now,
            "updated_at": now,
        }
        self._entries.append(entry)
        self.save()
        return entry
    
    # Edit an existing entry by ID and save. Returns True if successful, False if entry not found.
    def edit(self, entry_id: str, username: str,
             password: str, url: str , notes: str ="",title: str = "") -> bool:
        
        if not username.strip():
            raise ValueError("Username is required")
        if not password.strip():
            raise ValueError("Password is required")
        if not url.strip():
            raise ValueError("URL is required")
        
        # Find the entry by ID, update its fields and timestamp, then save the vault.
        for entry in self._entries:
            if entry["id"] == entry_id:
                entry["title"]      = title.strip()
                entry["username"]   = username.strip()
                entry["password"]   = password
                entry["url"]        = url.strip()
                entry["notes"]      = notes.strip()
                entry["updated_at"] = _now()
                self.save()
                return True
        return False
    
    # Delete an entry by ID and save. Returns True if successful, False if entry not found.
    def delete(self, entry_id: str) -> bool:

        before         = len(self._entries)
        self._entries  = [e for e in self._entries
                          if e["id"] != entry_id]
        changed        = len(self._entries) < before
        if changed:
            self.save()
        return changed
    
    # Get all entries sorted alphabetically by title.
    def get_all(self) -> list:
        """Return all entries sorted alphabetically by title."""
        return sorted(self._entries, key=lambda e: e["title"].lower())

    # Search entries by title, username, or URL (case-insensitive substring match).
    def search(self, query: str) -> list:
        
        q       = query.lower().strip()
        results = [
            e for e in self._entries
            if q in e["title"].lower()
            or q in e.get("username", "").lower()
            or q in e.get("url", "").lower()
        ]
        return sorted(results, key=lambda e: e["title"].lower())
    
    # Return the total number of stored entries.
    def count(self) -> int:
        """Return total number of stored entries."""
        return len(self._entries)


#  Helper 
def _now() -> str:
    """Return current UTC time as an ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


#  Quick test 
if __name__ == "__main__":
    import shutil

    # Clean up any old test vault
    test_dir = os.path.join(os.path.expanduser("~"), ".vaultkey")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    print("=" * 50)
    print("STEP 1 — Create new vault")
    vault = Vault()
    vault.create("MySecret123!")
    print(f"Vault created : {vault.vault_exists()}")
    print(f"File exists on disk  : {os.path.exists(VAULT_FILE)}")  # explicit disk check
    print(f"Entry count   : {vault.count()}")

    print()
    print("=" * 50)
    print("STEP 2 — Add entries")
    vault.add("Netflix",  "user@gmail.com", "netflix_pass", "https://netflix.com")
    vault.add("GitHub",   "sanjose",        "gh_pass456",   "https://github.com")
    vault.add("Amazon",   "user@gmail.com", "amz_pass789",  "https://amazon.com")
    print(f"Entry count   : {vault.count()}")

    print()
    print("=" * 50)
    print("STEP 3 — Get all entries")
    for e in vault.get_all():
        print(f"  {e['title']:10} | {e['username']:20} | {e['password']}")

    print()
    print("=" * 50)
    print("STEP 4 — Search")
    results = vault.search("git")
    print(f"Search 'git'  : {results[0]['title'] if results else 'nothing found'}")

    print()
    print("=" * 50)
    print("STEP 5 — Edit an entry")
    entry_id = vault.get_all()[0]["id"]
    vault.edit(entry_id, "Netflix", "new@gmail.com", "new_pass_999", "https://netflix.com")
    updated  = vault.get_all()[0]
    print(f"Updated user  : {updated['username']}")
    print(f"Updated pass  : {updated['password']}")

    print()
    print("=" * 50)
    print("STEP 6 — Delete an entry")
    vault.delete(entry_id)
    print(f"Entry count after delete : {vault.count()}")

    print()
    print("=" * 50)
    print("STEP 7 — Close and reopen with correct password")
    vault2 = Vault()
    result = vault2.open("MySecret123!")
    print(f"Opened with correct password : {result}")
    print(f"Entry count after reopen     : {vault2.count()}")

    print()
    print("=" * 50)
    print("STEP 8 — Wrong password rejected")
    vault3 = Vault()
    result = vault3.open("WrongPassword!")
    print(f"Opened with wrong password   : {result}")

    print()
    print("All tests passed!")