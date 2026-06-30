"""
Rich Menu — creates a 6-button persistent menu at the bottom of the LINE chat.
Triggered by calling GET /setup-rich-menu on the running server.
"""
import urllib.request
import urllib.error
import json

from app.config import settings

LINE_API = "https://api.line.me/v2/bot"


def _headers(content_type: str = "application/json") -> dict:
    return {
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": content_type,
    }


def _request(method: str, url: str, body: bytes = b"", content_type: str = "application/json"):
    req = urllib.request.Request(
        url,
        data=body if body else None,
        headers=_headers(content_type),
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def delete_all_rich_menus():
    """Delete every existing rich menu."""
    status, data = _request("GET", f"{LINE_API}/richmenu/list")
    if status != 200:
        print(f"[RichMenu] Could not list menus: {data}")
        return
    for menu in data.get("richmenus", []):
        mid = menu["richMenuId"]
        _request("DELETE", f"{LINE_API}/richmenu/{mid}")
        print(f"[RichMenu] Deleted {mid}")


def create_rich_menu() -> str | None:
    """
    Create a 6-button rich menu (3x2 grid):
      Top:    Recent | Summary | Categories
      Bottom: Log Cash | Send Slip (photo tip) | Export
    """
    menu_data = {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "Expense Tracker Menu",
        "chatBarText": "เมนู / Menu",
        "areas": [
            # ── Top row ──────────────────────────────────────────
            {
                "bounds": {"x": 0,    "y": 0, "width": 833, "height": 843},
                "action": {"type": "message", "text": "recent"},
            },
            {
                "bounds": {"x": 833,  "y": 0, "width": 834, "height": 843},
                "action": {"type": "message", "text": "summary"},
            },
            {
                "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
                "action": {"type": "message", "text": "categories"},
            },
            # ── Bottom row ────────────────────────────────────────
            {
                "bounds": {"x": 0,    "y": 843, "width": 833, "height": 843},
                "action": {"type": "message", "text": "cash "},   # user must add amount
            },
            {
                "bounds": {"x": 833,  "y": 843, "width": 834, "height": 843},
                "action": {"type": "message", "text": "help"},
            },
            {
                "bounds": {"x": 1667, "y": 843, "width": 833, "height": 843},
                "action": {"type": "message", "text": "export"},
            },
        ],
    }

    status, data = _request("POST", f"{LINE_API}/richmenu", json.dumps(menu_data).encode())
    if status != 200:
        print(f"[RichMenu] Create failed: {data}")
        return None

    rich_menu_id = data["richMenuId"]
    print(f"[RichMenu] Created: {rich_menu_id}")
    return rich_menu_id


def upload_rich_menu_image(rich_menu_id: str, image_path: str) -> bool:
    """Upload the PNG/JPG background image to the rich menu."""
    with open(image_path, "rb") as f:
        body = f.read()

    # Detect content type from extension
    ct = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
    status, data = _request(
        "POST",
        f"{LINE_API}/richmenu/{rich_menu_id}/content",
        body,
        content_type=ct,
    )
    if status == 200:
        print("[RichMenu] Image uploaded ✅")
        return True
    print(f"[RichMenu] Image upload failed: {data}")
    return False


def set_default_rich_menu(rich_menu_id: str) -> bool:
    """Set this rich menu as the default for all users."""
    status, data = _request(
        "POST",
        f"{LINE_API}/user/all/richmenu/{rich_menu_id}",
    )
    if status == 200:
        print("[RichMenu] Set as default ✅")
        return True
    print(f"[RichMenu] Set default failed: {data}")
    return False


def setup_rich_menu(image_path: str | None = None) -> dict:
    """
    Full pipeline: delete old → create new → upload image (optional) → set default.
    Returns a result dict.
    """
    delete_all_rich_menus()

    rich_menu_id = create_rich_menu()
    if not rich_menu_id:
        return {"ok": False, "error": "Failed to create rich menu"}

    if image_path:
        upload_rich_menu_image(rich_menu_id, image_path)

    ok = set_default_rich_menu(rich_menu_id)
    return {"ok": ok, "richMenuId": rich_menu_id}
