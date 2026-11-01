#!/usr/bin/env python3
"""Render every level and screen to PNG files for checking the artwork by eye.

Usage: python3 tools/screenshots.py OUTPUT_DIR
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
os.environ["TYPESTRIKER_DATA"] = os.path.join(out, "data")

import pygame  # noqa: E402

from typestriker import storage  # noqa: E402
from typestriker.app import App  # noqa: E402
from typestriker.autoplay import Autoplayer  # noqa: E402
from typestriker.config import FPS, LEVELS  # noqa: E402
from typestriker.play import PlayScene, Session  # noqa: E402
from typestriker import scenes  # noqa: E402

DT = 1 / FPS
app = App(fullscreen=False)


def shot(name):
    pygame.image.save(app.screen, os.path.join(out, name + ".png"))


def run(seconds, bot=None):
    for _ in range(int(seconds * FPS)):
        if bot and isinstance(app.scene, PlayScene):
            bot.update(DT, app.scene)
        app.step(DT)


for level in LEVELS:
    session = Session(start_level=level.number, seed=level.number)
    app.switch(PlayScene(app, session))
    run(1.2)
    shot(f"L{level.number:02d}_a_intro")
    run(10.0, Autoplayer(level.word_length * 0.42 + 0.2))
    shot(f"L{level.number:02d}_b_wave")
    scene = app.scene
    # Skip ahead to the boss
    scene.spawned = level.targets
    scene.targets = []
    scene.locked = None
    run(4.0)
    bot = Autoplayer(1.5)
    run(5.0, bot)
    shot(f"L{level.number:02d}_c_boss")

session = Session(seed=5)
for score, name in ((98000, "ACE"), (45200, "NOVA"), (12300, "SAM")):
    storage.add_score(name, score, 7, 31.5, 94.2)
for n in range(1, 8):
    for k in range(5):
        storage.record_level(n, 10 + n * 2 + k * 3, 80 + k * 3, k > 1)

for name, scene_type in (("menu", scenes.MainMenu), ("top10", scenes.HighScores),
                         ("progress", scenes.ProgressScene), ("howto", scenes.HowToPlay),
                         ("about", scenes.AboutScene), ("options", scenes.OptionsScene)):
    app.switch(scene_type(app))
    run(0.3)
    shot(f"S_{name}")

session = Session(seed=9)
bot = Autoplayer(6.0)
app.switch(PlayScene(app, session))
scene = app.scene
run(45.0, bot)
for s in range(120):
    if not isinstance(app.scene, PlayScene):
        break
    run(0.5, bot)
shot("S_level_summary")
session.levels[0].completed = True
session.victory = True
app.switch(scenes.ResultsScene(app, session))
run(2.0)
shot("S_results")
entry = scenes.NameEntry(app, session)
entry.name = "CAPTAIN"
app.switch(entry)
run(0.2)
shot("S_name_entry")
print("done")
