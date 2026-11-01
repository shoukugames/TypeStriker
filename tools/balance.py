#!/usr/bin/env python3
"""Simulate typists of different speeds and report how far each one gets.

Usage: python3 tools/balance.py [letters-per-second ...]
"""
import os
import random
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["TYPESTRIKER_DATA"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typestriker.app import App  # noqa: E402
from typestriker.autoplay import Autoplayer  # noqa: E402
from typestriker.play import PlayScene, Session  # noqa: E402
from typestriker.scenes import LevelSummary  # noqa: E402

DT = 1 / 60


def play(app, cps, seed, limit_minutes=60):
    session = Session(seed=seed)
    app.switch(PlayScene(app, session))
    rng = random.Random(seed)
    bot = Autoplayer(cps, 0.08 if cps else 0, rng) if cps else None
    for _ in range(int(limit_minutes * 3600)):
        scene = app.scene
        if isinstance(scene, PlayScene):
            if bot:
                bot.update(DT, scene)
            scene.update(DT)
        elif isinstance(scene, LevelSummary):
            session.level_index += 1
            if session.level_index >= 10:
                session.victory = True
                break
            app.switch(PlayScene(app, session))
        else:
            break
    return session


def main():
    speeds = [float(a) for a in sys.argv[1:]] or [0, 0.7, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0]
    app = App(fullscreen=False)
    for cps in speeds:
        rows = [play(app, cps, seed) for seed in (1, 2, 3)]
        reached = [("WIN" if s.victory else s.levels[-1].number) for s in rows]
        hits = {}
        for session in rows:
            for stats in session.levels:
                hits.setdefault(stats.number, []).append(stats.hits_taken)
        mins = [round(s.time / 60, 1) for s in rows]
        print(f"{cps:4.1f} cps ({cps * 12:3.0f} wpm)  reached {reached}  minutes {mins}  "
              f"score {rows[0].score:>7}  hits/level "
              + " ".join(f"{sum(v) / len(v):.0f}" for _, v in sorted(hits.items())), flush=True)


main()
