#!/usr/bin/env python
"""
Setup Rich Menu for LINE Bot
Run this after the bot is running to create the bottom button menu
"""
import asyncio
from app.rich_menu import create_rich_menu, delete_all_rich_menus


async def main():
    print("🎨 Setting up Rich Menu...")
    print()
    
    # Delete existing menus first
    print("🗑️  Deleting old rich menus...")
    await delete_all_rich_menus()
    print()
    
    # Create new rich menu
    print("✨ Creating new rich menu...")
    rich_menu_id = await create_rich_menu()
    
    if rich_menu_id:
        print()
        print("=" * 60)
        print("🎉 Rich Menu Created Successfully!")
        print("=" * 60)
        print()
        print(f"Rich Menu ID: {rich_menu_id}")
        print()
        print("📱 Now open your LINE app and you should see:")
        print("   - Bottom menu with 5 buttons")
        print("   - Recent | Summary | Categories")
        print("   - Log Cash | Export")
        print()
        print("✅ Setup complete!")
    else:
        print()
        print("❌ Failed to create Rich Menu")
        print("   Check your LINE_CHANNEL_ACCESS_TOKEN in .env")


if __name__ == "__main__":
    asyncio.run(main())
