import hashlib
import os
import secrets
from pathlib import Path


def generate_magic_token() -> str:
    return secrets.token_urlsafe(32)


def hash_magic_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_magic_link(token: str) -> str:
    ui_base_url = os.getenv("UI_BASE_URL", "http://localhost:3000").rstrip("/")
    return f"{ui_base_url}/magic-link/callback?token={token}"


def render_magic_link_email(magic_link: str) -> str:
    template_path = Path(__file__).resolve().parent.parent / "templates" / "magic_link_email.html"
    template = template_path.read_text(encoding="utf-8")
    return template.replace("{{MAGIC_LINK_URL}}", magic_link)
