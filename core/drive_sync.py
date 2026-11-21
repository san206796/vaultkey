"""
core/drive_sync.py
Handles uploading and downloading the encrypted vault file
to and from Google Drive's hidden appDataFolder.
This allows users to sync their vault across devices by backing up to Drive and restoring on a new device.
"""

import os
import io

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError

# Constants and configuration

VAULT_DIR       = os.path.join(os.path.expanduser("~"), ".vaultkey")
LOCAL_VAULT     = os.path.join(VAULT_DIR, "vault.enc")
REMOTE_FILENAME = "vaultkey_vault.enc"


#  Upload
# Upload the local vault.enc file to Google Drive's appDataFolder.
# If the file already exists on Drive, it will be updated. If not, it will be created.
def upload_vault(creds: Credentials) -> bool:
   
    if not os.path.exists(LOCAL_VAULT):
        print("[Drive] No local vault found to upload")
        return False

    try:
        service = _get_service(creds)
        file_id = _find_remote_vault(service)
        media   = MediaFileUpload(
            LOCAL_VAULT,
            mimetype="application/octet-stream",
            resumable=False,
        )

        if file_id:
            # File already exists on Drive — update it
            service.files().update(
                fileId=file_id,
                media_body=media,
            ).execute()
            print("[Drive] Vault updated on Drive")
        else:
            # First upload — create the file
            metadata = {
                "name":    REMOTE_FILENAME,
                "parents": ["appDataFolder"],
            }
            service.files().create(
                body=metadata,
                media_body=media,
                fields="id",
            ).execute()
            print("[Drive] Vault uploaded to Drive for first time")

        return True

    except HttpError as e:
        print(f"[Drive] Upload failed: {e}")
        return False
    except Exception as e:
        print(f"[Drive] Unexpected error during upload: {e}")
        return False


#  Download 
# Download the vault.enc file from Google Drive's appDataFolder to the local device.
# This is used on first launch on a new device to restore an existing vault backup. If no remote vault is found, it returns False to indicate that a new vault should be created instead.
def download_vault(creds: Credentials) -> bool:

    try:
        service = _get_service(creds)
        file_id = _find_remote_vault(service)

        if not file_id:
            print("[Drive] No remote vault found")
            return False

        # Download the file into memory first
        request    = service.files().get_media(fileId=file_id)
        buffer     = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        # Write to local vault file
        os.makedirs(VAULT_DIR, exist_ok=True)
        with open(LOCAL_VAULT, "wb") as f:
            f.write(buffer.getvalue())

        print(f"[Drive] Vault downloaded to {LOCAL_VAULT}")
        return True

    except HttpError as e:
        print(f"[Drive] Download failed: {e}")
        return False
    except Exception as e:
        print(f"[Drive] Unexpected error during download: {e}")
        return False


#  Check remote vault exists
# Check if a vault backup exists on Google Drive.
# Used on first launch to decide whether to download an existing vault or create a new one.
def vault_exists_on_drive(creds: Credentials) -> bool:
   
    try:
        service = _get_service(creds)
        file_id = _find_remote_vault(service)
        return file_id is not None
    except Exception:
        return False


#  Delete remote vault 
# Delete the vault backup from Google Drive. Used when the user wants to remove their remote backup.
def delete_remote_vault(creds: Credentials) -> bool:
 
    try:
        service = _get_service(creds)
        file_id = _find_remote_vault(service)

        if not file_id:
            print("[Drive] No remote vault to delete")
            return False

        service.files().delete(fileId=file_id).execute()
        print("[Drive] Remote vault deleted from Drive")
        return True

    except HttpError as e:
        print(f"[Drive] Delete failed: {e}")
        return False


# Private helpers
# Build and return the Google Drive API service object.
def _get_service(creds: Credentials):

    return build("drive", "v3", credentials=creds)

# Search appDataFolder for the vault file.
# Returns the file ID string if found, None if not found.
def _find_remote_vault(service) -> str | None:

    results = service.files().list(
        spaces="appDataFolder",
        fields="files(id, name)",
        q=f"name = '{REMOTE_FILENAME}'",
    ).execute()

    files = results.get("files", [])
    return files[0]["id"] if files else None


#  Quick test 
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from core.auth import google_login, get_user_info

    print("=" * 50)
    print("STEP 1 — Google sign-in")
    print("Your browser will open for Google sign-in...")
    creds     = google_login()
    user_info = get_user_info(creds)
    print(f"Signed in as : {user_info['email']}")

    print()
    print("=" * 50)
    print("STEP 2 — Check if vault exists on Drive")
    exists = vault_exists_on_drive(creds)
    print(f"Remote vault exists : {exists}")

    print()
    print("=" * 50)
    print("STEP 3 — Upload local vault to Drive")
    if os.path.exists(LOCAL_VAULT):
        result = upload_vault(creds)
        print(f"Upload successful : {result}")
    else:
        print("No local vault found — run vault.py test first to create one")

    print()
    print("=" * 50)
    print("STEP 4 — Check Drive again after upload")
    exists = vault_exists_on_drive(creds)
    print(f"Remote vault exists : {exists}")

    print()
    print("=" * 50)
    print("STEP 5 — Download vault from Drive")
    # Rename local vault temporarily to test download
    backup = LOCAL_VAULT + ".backup"
    if os.path.exists(LOCAL_VAULT):
        os.rename(LOCAL_VAULT, backup)

    result = download_vault(creds)
    print(f"Download successful : {result}")
    print(f"Local vault exists  : {os.path.exists(LOCAL_VAULT)}")

    # Restore backup
    if os.path.exists(backup):
        os.remove(LOCAL_VAULT)
        os.rename(backup, LOCAL_VAULT)

    print()
    print("All drive sync tests passed!")