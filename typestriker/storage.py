"""Saves the top 10 scores, per-level progression and settings as JSON.

Files live in the per-user data folder, so scores survive updates and the game
works when installed in a read-only location. A damaged file is set aside and
replaced rather than stopping the game.
"""
import json
import os
import sys
import tempfile
import time

from .config import NAME_LENGTH, TOP_SCORES

HISTORY_LENGTH = 20


def data_dir():
    override = os.environ.get("TYPESTRIKER_DATA")
    if override:
        path = override
    elif sys.platform == "win32":
        path = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "TypeStriker")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        path = os.path.join(base, "typestriker")
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        path = os.path.join(tempfile.gettempdir(), "typestriker")
        os.makedirs(path, exist_ok=True)
    return path


def _load(name, default):
    path = os.path.join(data_dir(), name)
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, type(default)):
            return data
        raise ValueError("unexpected structure")
    except FileNotFoundError:
        return default
    except (OSError, ValueError):
        try:
            os.replace(path, path + ".corrupt")
        except OSError:
            pass
        return default


def _save(name, data):
    path = os.path.join(data_dir(), name)
    temp = path + ".tmp"
    try:
        with open(temp, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        os.replace(temp, path)
    except OSError as error:
        print(f"Could not save {name}: {error}", file=sys.stderr)


# ---- Top 10 ---------------------------------------------------------------

def load_scores():
    good = []
    for row in _load("scores.json", []):
        try:
            good.append({
                "name": str(row["name"])[:NAME_LENGTH],
                "score": int(row["score"]),
                "level": int(row.get("level", 1)),
                "wpm": float(row.get("wpm", 0)),
                "accuracy": float(row.get("accuracy", 0)),
                "date": str(row.get("date", "")),
            })
        except (KeyError, TypeError, ValueError):
            continue
    good.sort(key=lambda r: -r["score"])
    return good[:TOP_SCORES]


def qualifies(score):
    if score <= 0:
        return False
    scores = load_scores()
    return len(scores) < TOP_SCORES or score > scores[-1]["score"]


def add_score(name, score, level, wpm, accuracy):
    """Insert a score and return its rank (0 is first place)."""
    scores = load_scores()
    entry = {
        "name": name.strip()[:NAME_LENGTH] or "PILOT",
        "score": int(score),
        "level": int(level),
        "wpm": round(wpm, 1),
        "accuracy": round(accuracy, 1),
        "date": time.strftime("%Y-%m-%d"),
    }
    rank = next((i for i, row in enumerate(scores) if score > row["score"]), len(scores))
    scores.insert(rank, entry)
    _save("scores.json", scores[:TOP_SCORES])
    return rank


# ---- Progression ----------------------------------------------------------

def load_progress():
    data = _load("progress.json", {})
    return {k: v for k, v in data.items() if isinstance(v, dict)}


def record_level(number, wpm, accuracy, completed):
    """Store one attempt at a level. Returns which personal bests were beaten."""
    progress = load_progress()
    row = progress.get(str(number)) or {}
    earlier_plays = int(row.get("plays", 0))
    best_wpm = float(row.get("best_wpm", 0))
    best_accuracy = float(row.get("best_accuracy", 0))
    beaten = {
        "wpm": earlier_plays > 0 and wpm > best_wpm,
        "accuracy": earlier_plays > 0 and accuracy > best_accuracy,
    }
    history = list(row.get("history", []))
    history.append({"wpm": round(wpm, 1), "accuracy": round(accuracy, 1),
                    "date": time.strftime("%Y-%m-%d")})
    progress[str(number)] = {
        "plays": earlier_plays + 1,
        "clears": int(row.get("clears", 0)) + (1 if completed else 0),
        "best_wpm": round(max(best_wpm, wpm), 1),
        "best_accuracy": round(max(best_accuracy, accuracy), 1),
        "last_wpm": round(wpm, 1),
        "last_accuracy": round(accuracy, 1),
        "history": history[-HISTORY_LENGTH:],
    }
    _save("progress.json", progress)
    return beaten


# ---- Settings -------------------------------------------------------------

DEFAULT_SETTINGS = {"sound": 0.8, "music": 0.5, "fullscreen": False, "language": None}


def load_settings():
    settings = dict(DEFAULT_SETTINGS)
    settings.update(_load("settings.json", {}))
    return settings


def save_settings(settings):
    _save("settings.json", settings)
