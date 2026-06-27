"""
Rich Menu Setup for LINE Bot
Creates a persistent button menu at the bottom of the chat
"""
import httpx
from app.config import settings

LINE_API_URL = "https://api.line.me/v2/bot"


async def create_rich_menu():
    """Create and set up the rich menu with buttons."""
    
    # Define the rich menu structure
    rich_menu_data = {
        "size": {
            "width": 2500,
            "height": 1686
        },
        "selected": True,
        "name": "Expense Tracker Menu",
        "chatBarText": "เมนู",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
                "action": {"type": "message", "text": "recent"}
            },
            {
                "bounds": {"x": 833, "y": 0, "width": 834, "height": 843},
                "action": {"type": "message", "text": "summary"}
            },
            {
                "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
                "action": {"type": "message", "text": "categories"}
            },
            {
                "bounds": {"x": 0, "y": 843, "width": 1250, "height": 843},
                "action": {"type": "message", "text": "log cash"}
            },
            {
                "bounds": {"x": 1250, "y": 843, "width": 1250, "height": 843},
                "action": {"type": "message", "text": "export"}
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # Create rich menu
        response = await client.post(
            f"{LINE_API_URL}/richmenu",
            headers=headers,
            json=rich_menu_data
        )
        
        if response.status_code == 200:
            rich_menu_id = response.json()["richMenuId"]
            print(f"✅ Rich Menu created: {rich_menu_id}")
            
            # Set as default rich menu
            default_response = await client.post(
                f"{LINE_API_URL}/user/all/richmenu/{rich_menu_id}",
                headers=headers
            )
            
            if default_response.status_code == 200:
                print("✅ Rich Menu set as default")
                return rich_menu_id
            else:
                print(f"❌ Failed to set default: {default_response.text}")
                return None
        else:
            print(f"❌ Failed to create Rich Menu: {response.text}")
            return None


async def upload_rich_menu_image(rich_menu_id: str, image_path: str):
    """Upload image for the rich menu."""
    headers = {
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "image/png"
    }
    
    with open(image_path, "rb") as image_file:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LINE_API_URL}/richmenu/{rich_menu_id}/content",
                headers=headers,
                content=image_file.read()
            )
            
            if response.status_code == 200:
                print("✅ Rich Menu image uploaded")
                return True
            else:
                print(f"❌ Failed to upload image: {response.text}")
                return False


async def delete_all_rich_menus():
    """Delete all existing rich menus."""
    headers = {
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    async with httpx.AsyncClient() as client:
        # Get all rich menus
        response = await client.get(
            f"{LINE_API_URL}/richmenu/list",
            headers=headers
        )
        
        if response.status_code == 200:
            menus = response.json().get("richmenus", [])
            for menu in menus:
                menu_id = menu["richMenuId"]
                # Delete each menu
                await client.delete(
                    f"{LINE_API_URL}/richmenu/{menu_id}",
                    headers=headers
                )
                print(f"✅ Deleted rich menu: {menu_id}")
        else:
            print(f"❌ Failed to get rich menus: {response.text}")
