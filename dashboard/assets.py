"""
dashboard/assets.py - Encoded UI Assets for FinGuard AI
Loads and caches base64-encoded visual assets for high-fidelity rendering.
"""

from pathlib import Path
import base64

ASSETS_DIR = Path(__file__).resolve().parent / "assets"

def get_asset_b64(filename: str) -> str:
    """Returns base64 data URI for an asset image, or empty string if missing."""
    p = ASSETS_DIR / filename
    if p.exists():
        try:
            with open(p, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
                mime = "image/png" if filename.endswith(".png") else "image/jpeg"
                return f"data:{mime};base64,{data}"
        except Exception:
            return ""
    return ""

LOGO_B64 = get_asset_b64("finguard_logo.png")
HERO_SHIELD_B64 = get_asset_b64("hero_shield.png")
SIDEBAR_GLOBE_B64 = get_asset_b64("sidebar_globe.png")
SHIELD_WATERMARK_B64 = get_asset_b64("shield_watermark.png")
