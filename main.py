"""Web entry point for pygbag (https://pygame-web.github.io): Type Striker in the browser.

Build with:  python3 tools/build_web.py     (writes build/web/)
The desktop game still starts with run_game.py; nothing here changes it.
"""
import asyncio

import pygame  # noqa: F401  (must be imported here so pygbag loads pygame)

from typestriker.app import App


async def main():
    await App().run_web()


asyncio.run(main())
