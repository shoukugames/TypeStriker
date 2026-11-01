import re

import pygame
import pytest

import typestriker
from typestriker import hud, i18n, play, scenes, storage, ui
from typestriker.config import AUTHOR, EMAIL, LEVELS, WEBSITE, WIDTH
from typestriker.i18n import ENGLISH, JAPANESE, STRINGS, t
from typestriker.play import PlayScene, Session

FPS_DT = 1 / 60
JAPANESE_CHAR = re.compile(r"[぀-ヿ㐀-鿿]")
SAME_IN_BOTH = {"col.wpm"}


@pytest.fixture(autouse=True)
def english_afterwards():
    yield
    i18n.set_language(ENGLISH)


def f3():
    return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F3, unicode="", mod=0)


def test_every_string_exists_in_both_languages():
    for key, (english, japanese) in STRINGS.items():
        assert english and japanese, key
        if key not in SAME_IN_BOTH:
            assert JAPANESE_CHAR.search(japanese), key


def test_placeholders_match_between_languages():
    for key, (english, japanese) in STRINGS.items():
        assert set(re.findall(r"{(\w+)}", english)) == set(re.findall(r"{(\w+)}", japanese)), key


def test_bundled_font_has_every_japanese_character(app):
    text = "".join(pair[1] for pair in STRINGS.values()) + "".join(i18n.LEVEL_NAMES_JA.values()) + "日本語"
    for char in set(text):
        if ord(char) >= 0x2E80:
            assert ui.font_for(char, 40).metrics(char)[0] is not None, char


def test_all_levels_have_japanese_names():
    assert set(i18n.LEVEL_NAMES_JA) == {lv.number for lv in LEVELS}


def test_credits_keep_the_required_details_in_both_languages():
    for language in (ENGLISH, JAPANESE):
        i18n.set_language(language)
        assert AUTHOR in t("about.author", author=AUTHOR)
        assert "Claude Code" in t("about.author", author=AUTHOR)
    assert WEBSITE == "https://shoukugames.org/" and EMAIL == "info@shoukugames.org"


def all_screens(app):
    session = Session(seed=2)
    session.score = 12300
    scene = PlayScene(app, session)
    stats = session.levels[0]
    stats.correct, stats.wrong, stats.active_time, stats.completed = 80, 5, 60.0, True
    return [scenes.MainMenu(app), scenes.HighScores(app), scenes.ProgressScene(app), scenes.HowToPlay(app),
            scenes.AboutScene(app), scenes.OptionsScene(app), scenes.ResultsScene(app, session),
            scenes.LevelSummary(app, session, stats, {"wpm": True, "accuracy": True}),
            scenes.NameEntry(app, session), scene]


@pytest.mark.parametrize("language", [ENGLISH, JAPANESE])
def test_no_text_runs_off_the_screen(app, monkeypatch, language):
    storage.add_score("ACE", 90000, 7, 30, 95)
    for number in range(1, 11):
        storage.record_level(number, 30, 95, True)
    i18n.set_language(language)
    overflow = []
    real = ui.text

    def checked(surf, string, *args, **kwargs):
        rect = real(surf, string, *args, **kwargs)
        if rect.left < 0 or rect.right > WIDTH:
            overflow.append(string)
        return rect

    monkeypatch.setattr(scenes, "text", checked)
    monkeypatch.setattr(ui, "text", checked)
    for scene in all_screens(app):
        if isinstance(scene, PlayScene):
            scene.set_paused(True)
        app.switch(scene)
        app.step(FPS_DT)
    assert not overflow, overflow
    for key in ("title", "top10.title", "results.victory", "name.title", "progress.title"):
        assert ui.fancy_title(t(key), 130 if key == "title" else 84).get_width() <= WIDTH + 70, key


def test_f3_and_the_pill_switch_language_and_it_is_saved(app):
    i18n.set_language(ENGLISH)
    app.switch(scenes.MainMenu(app))
    app.dispatch(f3())
    assert i18n.get_language() == JAPANESE
    assert storage.load_settings()["language"] == JAPANESE
    pill = app._pill_rect()
    app.dispatch(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pill.center))
    assert i18n.get_language() == ENGLISH
    assert storage.load_settings()["language"] == ENGLISH


def test_options_row_switches_language(app):
    i18n.set_language(ENGLISH)
    scene = scenes.OptionsScene(app)
    app.switch(scene)
    scene.index = 3
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, unicode="", mod=0))
    assert i18n.get_language() == JAPANESE


def test_gameplay_stays_in_english_and_cannot_toggle(app, monkeypatch):
    i18n.set_language(JAPANESE)
    scene = PlayScene(app, Session(seed=1))
    app.switch(scene)
    app.dispatch(f3())
    assert i18n.get_language() == JAPANESE
    drawn = []
    real = ui.text

    def spy(surf, string, *args, **kwargs):
        drawn.append(string)
        return real(surf, string, *args, **kwargs)

    monkeypatch.setattr(hud, "text", spy)
    monkeypatch.setattr(play, "text", spy)
    for _ in range(30):
        app.step(FPS_DT)
    assert drawn and all(string.isascii() for string in drawn), drawn
    scene.set_paused(True)
    app.dispatch(f3())
    assert i18n.get_language() == ENGLISH  # the pause menu can


def test_kana_mode_keyboard_still_types_letters(app):
    scene = PlayScene(app, Session(seed=1))
    app.switch(scene)
    scene.set_state("wave")
    scene.spawned = scene.level.targets
    from typestriker.entities import Target
    target = Target("fighter", "a", 300, scene.level, scene.book, scene.rng, scene.player.x)
    target.y = 200
    scene.targets.append(target)
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, unicode="ち", mod=0))
    assert target.typed == 1


@pytest.mark.parametrize("value, expected", [
    ("ja_JP.UTF-8", JAPANESE), ("ja", JAPANESE), ("en_US.UTF-8", ENGLISH), ("fr_FR.UTF-8", ENGLISH), ("C", ENGLISH),
])
def test_first_run_language_follows_the_system(monkeypatch, value, expected):
    for name in ("LANGUAGE", "LC_ALL", "LC_MESSAGES"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LANG", value)
    assert i18n.detect_language() == expected


def test_version_format_and_changelog():
    version = typestriker.__version__
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    with open("README.md", encoding="utf-8") as handle:
        assert f"**v{version}**" in handle.read(), "every version needs a changelog line"
