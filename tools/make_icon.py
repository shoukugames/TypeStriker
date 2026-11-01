#!/usr/bin/env python3
"""Draw the spaceship icon from the game's own artwork: assets/icon.png and icon.ico.

Run this only when the ship design changes. Needs Pillow for the .ico file.
"""
import os
import random
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

import pygame  # noqa: E402
from PIL import Image  # noqa: E402

from typestriker import art  # noqa: E402

pygame.init()
pygame.display.set_mode((16, 16))
SIZE = 512
BIG = SIZE * 2

canvas = pygame.Surface((BIG, BIG), pygame.SRCALPHA)
c = BIG // 2

# Deep-space rounded square
back = pygame.Surface((1, 128))
for y in range(128):
    t = y / 127
    back.set_at((0, y), art.mix((26, 42, 120), (6, 8, 34), t))
back = pygame.transform.smoothscale(back, (BIG, BIG)).convert_alpha()
mask = pygame.Surface((BIG, BIG), pygame.SRCALPHA)
pygame.draw.rect(mask, (255, 255, 255, 255), (20, 20, BIG - 40, BIG - 40), border_radius=190)
back.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
canvas.blit(back, (0, 0))

rng = random.Random(4)
for _ in range(150):
    x, y = rng.randint(70, BIG - 70), rng.randint(70, BIG - 70)
    pygame.draw.circle(canvas, (255, 255, 255, rng.randint(90, 240)), (x, y), rng.choice((2, 2, 3, 4)))

halo = art.radial(430, (70, 150, 255), 2.2)
canvas.blit(halo, (c - 430, c - 470))

ship = art.player_ship(8.2)
sx, sy = c - ship.get_width() // 2, c - ship.get_height() // 2 - 50
# Engine flames
for dx in (-45, 45):
    for r, col in ((96, (255, 110, 30)), (62, (255, 200, 90)), (34, (255, 255, 235))):
        canvas.blit(art.radial(r, col, 1.0), (c + dx - r, sy + ship.get_height() - 8 - r + (96 - r) // 2))
canvas.blit(ship, (sx, sy))

canvas.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
final = pygame.transform.smoothscale(canvas, (SIZE, SIZE))
assets = os.path.join(ROOT, "assets")
png = os.path.join(assets, "icon.png")
pygame.image.save(final, png)
Image.open(png).convert("RGBA").save(os.path.join(assets, "icon.ico"),
                                     sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("wrote", png)
