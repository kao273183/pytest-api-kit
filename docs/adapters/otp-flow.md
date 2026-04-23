# Adapter: Multi-step login (OTP / CAPTCHA / encrypted payload)

Real-world case extracted from a production app where login requires:

1. Hitting a `/login/step1` that returns a nonce
2. AES-encrypting the password with the nonce as key
3. POSTing encrypted payload + phone to `/login/step2` to trigger SMS OTP
4. POSTing OTP to `/login/step3` to get access + ID tokens
5. Refreshing tokens when expired via `/login/refresh`

The kit doesn't solve this for you — every company's flow is different — but
the pattern below is proven on a production UAT suite running 170+ tests daily.

## Pattern: class-based TokenManager + file cache

```python
# utils/auth.py
import base64
import hashlib
import json
import time
from pathlib import Path
from typing import Dict

import requests
from Crypto.Cipher import AES  # pycryptodome


class TokenManager:
    """Multi-step login with file-cached session."""

    SESSION_FILE = Path("data") / "session.json"

    def __init__(self, phone: str, password: str, fixed_otp: str = ""):
        self.phone = phone
        self.password = password
        self.fixed_otp = fixed_otp
        self._tokens: Dict = {}
        self._load_cached()

    # ------ public ------

    def ensure_valid_token(self) -> Dict:
        """Return cached tokens if valid, else re-login."""
        if self._tokens and not self.is_expired:
            return self._tokens
        if self._tokens and self._tokens.get("refresh_token"):
            try:
                return self._refresh()
            except Exception:
                pass
        return self._login()

    @property
    def is_expired(self) -> bool:
        exp = self._tokens.get("expires_at", 0)
        return time.time() >= exp - 30

    # ------ internal ------

    def _login(self) -> Dict:
        # Step 1: get nonce
        r1 = requests.post("https://auth.example.com/login/step1", json={
            "phone": self.phone,
        }, timeout=10).json()
        nonce = r1["nonce"]

        # Step 2: AES-encrypt password, trigger OTP
        encrypted = self._aes_encrypt(self.password, nonce)
        requests.post("https://auth.example.com/login/step2", json={
            "phone": self.phone,
            "encrypted_pwd": encrypted,
        }, timeout=10)

        # Step 3: submit OTP
        otp = self.fixed_otp or self._prompt_for_otp()
        r3 = requests.post("https://auth.example.com/login/step3", json={
            "phone": self.phone,
            "otp": otp,
        }, timeout=10).json()

        self._tokens = {
            "access_token": r3["access_token"],
            "id_token": r3["id_token"],
            "refresh_token": r3.get("refresh_token", ""),
            "uid": r3["uid"],
            "expires_at": time.time() + r3.get("expires_in", 3600),
        }
        self._save()
        return self._tokens

    def _refresh(self) -> Dict:
        r = requests.post("https://auth.example.com/login/refresh", json={
            "refresh_token": self._tokens["refresh_token"],
        }, timeout=10).json()
        self._tokens["access_token"] = r["access_token"]
        self._tokens["expires_at"] = time.time() + r.get("expires_in", 3600)
        self._save()
        return self._tokens

    def _aes_encrypt(self, plaintext: str, key: str) -> str:
        key_bytes = hashlib.sha256(key.encode()).digest()
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        # PKCS7 padding
        padded = plaintext + chr(16 - len(plaintext) % 16) * (16 - len(plaintext) % 16)
        ct = cipher.encrypt(padded.encode())
        return base64.b64encode(ct).decode()

    def _prompt_for_otp(self) -> str:
        return input("Enter OTP: ").strip()

    def _save(self):
        self.SESSION_FILE.parent.mkdir(exist_ok=True)
        self.SESSION_FILE.write_text(json.dumps(self._tokens))

    def _load_cached(self):
        if self.SESSION_FILE.exists():
            try:
                self._tokens = json.loads(self.SESSION_FILE.read_text())
            except Exception:
                self._tokens = {}
```

## Wire into APIClient

Our APIClient ships with `set_token()` for simple Bearer. For multi-header
auth, either:

1. Use `set_header()` directly:
   ```python
   tokens = token_manager.ensure_valid_token()
   client.set_header("X-Access-Token", tokens["access_token"])
   client.set_header("X-Id-Token", tokens["id_token"])
   client.set_header("Authorization", f"Bearer {tokens['access_token']}")
   ```

2. Or subclass for convenience:
   ```python
   class MyAPIClient(APIClient):
       def set_dual_token(self, access: str, id_token: str):
           self.session.headers["X-Access-Token"] = access
           self.session.headers["X-Id-Token"] = id_token
           self.session.headers["Authorization"] = f"Bearer {access}"
   ```

## Fixed OTP for UAT

Production OTP flow doesn't work for automation (SMS requires a phone).
The usual fix: have the backend treat a hard-coded OTP (e.g. `000000`) as
valid in UAT environment only. Pass it via `AUTH_FIXED_OTP` env var.

## Don't save tokens to git

Add `data/session.json` to `.gitignore`. If your flow produces any encryption
key or secret artefact, the snapshot should explicitly exclude it.
