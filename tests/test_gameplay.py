
import pygame
import pytest

from typestriker import storage
from typestriker.autoplay import Autoplayer
from typestriker.config import BOSS_BONUS, FPS, LEVELS, MAX_HP, POINTS_PER_LETTER, RAIL_Y, WIDTH
from typestriker.entities import Target
from typestriker.play import PlayScene, Session
from typestriker.scenes import HighScores, LevelSummary, MainMenu, NameEntry, ResultsScene

DT = 1 / FPS


def run(app, seconds, bot=None):
    for _ in range(int(seconds * FPS)):
        scene = app.scene
        if bot and isinstance(scene, PlayScene):
            bot.update(DT, scene)
        app.step(DT)


def start(app, number=1, seed=1):
    session = Session(start_level=number, seed=seed)
    scene = PlayScene(app, session)
    app.switch(scene)
    scene.set_state("wave")
    return scene


def add_target(scene, text="cat", kind="fighter", x=300, y=200):
    target = Target(kind, text, x, scene.level, scene.book, scene.rng, scene.player.x)
    target.y = y
    scene.targets.append(target)
    scene.spawned = scene.level.targets  # no surprise arrivals during the test
    return target


def key(char):
    return pygame.event.Event(pygame.KEYDOWN, key=0, unicode=char, mod=0)


def settle(scene, frames=30):
    for _ in range(frames):
        scene._update_shots(DT)
        scene.effects.update(DT)


def test_correct_letter_scores_100_and_one_hit_kills_in_early_levels(app):
    scene = start(app, 1)
    target = add_target(scene, "q")
    scene.handle_event(key("q"))
    assert scene.session.score == POINTS_PER_LETTER == 100
    settle(scene)
    assert not target.alive
    assert scene.stats.destroyed == 1


def test_uppercase_input_counts(app):
    scene = start(app, 1)
    add_target(scene, "q")
    scene.handle_event(key("Q"))
    assert scene.stats.correct == 1


def test_wrong_key_lowers_accuracy_and_scores_nothing(app):
    scene = start(app, 1)
    add_target(scene, "q")
    scene.handle_event(key("x"))
    assert scene.session.score == 0
    assert scene.stats.wrong == 1
    assert scene.stats.accuracy == 0.0


def test_stray_key_with_nothing_on_screen_costs_nothing(app):
    scene = start(app, 1)
    scene.spawned = scene.level.targets
    scene.handle_event(key("x"))
    assert scene.stats.wrong == 0


@pytest.mark.parametrize("word", ["go", "cat", "moon", "comet", "planet", "rainbow", "treasure"])
def test_enemy_takes_one_hit_per_letter(app, word):
    scene = start(app, 4)
    target = add_target(scene, word)
    for i, letter in enumerate(word):
        assert target.alive
        scene.handle_event(key(letter))
        settle(scene)
        assert target.hits == i + 1
    assert not target.alive
    assert scene.session.score == 100 * len(word)


def test_word_locks_until_finished_and_backspace_releases(app):
    scene = start(app, 5)
    first = add_target(scene, "cat", y=300)
    second = add_target(scene, "dog", x=700, y=200)
    scene.handle_event(key("c"))
    assert scene.locked is first
    scene.handle_event(key("d"))  # the other word cannot be started while locked
    assert second.typed == 0 and scene.stats.wrong == 1
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE, unicode="\b", mod=0))
    assert scene.locked is None
    scene.handle_event(key("d"))
    assert scene.locked is second and first.typed == 1


def test_lowest_enemy_is_chosen_when_letters_match(app):
    scene = start(app, 1)
    add_target(scene, "a", x=200, y=150)
    low = add_target(scene, "a", x=700, y=400)
    scene.handle_event(key("a"))
    assert low.typed == 1


def test_letter_cannot_be_typed_until_its_plate_is_visible(app):
    scene = start(app, 1)
    hidden = add_target(scene, "q", y=-40)
    assert not hidden.on_screen
    scene.handle_event(key("q"))
    assert hidden.typed == 0


def test_ten_hits_lose_a_life_and_refill_the_bar(app):
    scene = start(app, 1)
    session = scene.session
    for expected in range(MAX_HP - 1, 0, -1):
        scene.hurt()
        assert session.hp == expected
    assert session.lives == 3
    scene.hurt()
    assert session.lives == 2 and session.hp == MAX_HP
    assert scene.player.invulnerable > 0
    before = session.hp
    scene.hurt()  # protected for a moment after a life is lost
    assert session.hp == before


def test_three_lives_then_game_over_flow(app):
    scene = start(app, 1)
    session = scene.session
    session.score = 5000
    for _ in range(3):
        scene.player.invulnerable = 0
        session.hp = 1
        scene.hurt()
    assert session.lives == 0 and scene.state == "dying"
    run(app, 3.2)
    assert isinstance(app.scene, ResultsScene)
    assert app.scene.qualified
    app.scene.time = 5
    app.scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r", mod=0))
    assert isinstance(app.scene, NameEntry)


def test_collision_costs_one_hit_and_destroys_the_enemy(app):
    scene = start(app, 1)
    target = add_target(scene, "q", x=scene.player.x, y=scene.player.y)
    scene.player.y = RAIL_Y
    target.y = RAIL_Y
    scene._update_targets(DT)
    assert not target.alive
    assert scene.session.hp == MAX_HP - 1
    assert scene.stats.missed == 1


def test_bullet_hit_costs_one_hit(app):
    scene = start(app, 1)
    scene.player.y = RAIL_Y
    scene._spawn_bullet(scene.player.x, RAIL_Y, 0, 0)
    scene._update_bullets(DT)
    assert scene.session.hp == MAX_HP - 1
    assert not scene.bullets


def _to_boss(app, number):
    scene = start(app, number)
    scene.spawned = scene.level.targets
    run(app, 2.6)
    assert scene.state == "boss"
    while not scene.boss.arrived:
        app.step(DT)
    return scene


@pytest.mark.parametrize("number", [lv.number for lv in LEVELS])
def test_each_boss_takes_exactly_ten_shots(app, number):
    scene = _to_boss(app, number)
    boss = scene.boss
    level = LEVELS[number - 1]
    scene.player.invulnerable = 1000
    typed = 0
    for shot in range(10):
        assert len(boss.text) == level.word_length
        assert boss.shots_fired == shot and not boss.dying
        for letter in boss.text:
            scene.handle_event(key(letter))
            typed += 1
        settle(scene, 60)
        assert boss.hits == shot + 1
    assert boss.dying and scene.state == "boss_death"
    assert typed == 10 * level.word_length
    assert scene.session.score == 100 * typed + BOSS_BONUS


def test_boss_words_do_not_repeat(app):
    scene = _to_boss(app, 8)
    boss = scene.boss
    scene.player.invulnerable = 1000
    words = []
    for _ in range(10):
        words.append(boss.text)
        for letter in list(boss.text):
            scene.handle_event(key(letter))
    assert len(set(words)) == 10


def test_stats_measure_speed_and_accuracy(app):
    scene = start(app, 1)
    stats = scene.stats
    stats.correct, stats.wrong, stats.active_time = 90, 10, 60.0
    assert stats.accuracy == 90.0
    assert stats.wpm == 18.0


def test_timer_stops_while_paused(app):
    scene = start(app, 1)
    run(app, 0.5)
    before = scene.session.time
    assert before > 0
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="\x1b", mod=0))
    assert scene.paused
    run(app, 0.5)
    assert scene.session.time == before


@pytest.mark.parametrize("kind", ["scout", "fighter", "bomber", "saucer", "interceptor", "drone", "missile"])
def test_missed_flyers_reach_the_ship(app, kind):
    scene = start(app, 7)
    scene.spawned = scene.level.targets
    target = add_target(scene, "comet", kind=kind, x=100, y=100)
    scene.session.hp = MAX_HP
    for _ in range(FPS * 40):
        scene.bullets = []
        scene._update_targets(DT)
        scene.player.update(DT)
        if not target.alive:
            break
    assert not target.alive, f"{kind} never finished its run"


def test_destroy_sounds_are_all_different():
    from typestriker.audio import _build_effects
    effects = _build_effects()
    kinds = ["scout", "fighter", "bomber", "saucer", "interceptor", "drone", "tank", "asteroid", "missile"]
    data = [tuple(effects[f"destroy_{k}"][:400]) for k in kinds]
    assert len(set(data)) == len(kinds)


def test_full_game_can_be_won_and_score_saved(app):
    session = Session(seed=7)
    app.switch(PlayScene(app, session))
    bot = Autoplayer(9.0)
    frame = 0
    for _ in range(FPS * 60 * 40):
        scene = app.scene
        if isinstance(scene, PlayScene):
            bot.update(DT, scene)
        elif isinstance(scene, LevelSummary):
            scene.time = 5
            app.dispatch(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r", mod=0))
            continue
        elif isinstance(scene, ResultsScene):
            break
        frame += 1
        # Simulating is quick. Drawing every 20th frame still exercises all the art.
        if frame % 20:
            scene.update(DT)
        else:
            app.step(DT)
    assert isinstance(app.scene, ResultsScene), type(app.scene)
    assert session.victory
    assert len(session.levels) == 10 and all(s.completed for s in session.levels)
    assert session.score == 100 * session.total_correct + 10 * BOSS_BONUS
    # Each level must record its own speed and accuracy
    progress = storage.load_progress()
    assert set(progress) == {str(n) for n in range(1, 11)}
    assert all(row["best_accuracy"] == 100.0 and row["best_wpm"] > 0 for row in progress.values())

    # Name entry takes at most ten characters and lands in the Top 10
    app.scene.time = 5
    app.scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r", mod=0))
    entry = app.scene
    assert isinstance(entry, NameEntry)
    for letter in "ABCDEFGHIJKLMN":
        entry.handle_event(key(letter))
    assert entry.name == "ABCDEFGHIJ"
    entry.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r", mod=0))
    assert isinstance(app.scene, HighScores)
    assert storage.load_scores()[0]["name"] == "ABCDEFGHIJ"
    app.scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r", mod=0))
    assert isinstance(app.scene, MainMenu)


def test_doing_nothing_ends_in_game_over(app):
    session = Session(seed=3)
    app.switch(PlayScene(app, session))
    for _ in range(FPS * 60 * 12):
        if isinstance(app.scene, ResultsScene):
            break
        app.scene.update(DT)
    assert isinstance(app.scene, ResultsScene)
    assert session.lives == 0 and not session.victory and session.score == 0


def test_about_has_required_details():
    from typestriker import config
    assert config.WEBSITE == "https://shoukugames.org/"
    assert config.EMAIL == "info@shoukugames.org"
    assert config.AUTHOR == "Shawn Rapaz"


def test_planet_levels_have_tanks_and_space_levels_do_not():
    planets = [lv for lv in LEVELS if lv.setting == "planet"]
    assert len(planets) >= 3
    for level in LEVELS:
        assert ("tank" in level.weights) == (level.setting == "planet"), level.name


def test_levels_get_harder():
    pace = [lv.word_length / lv.spawn_interval for lv in LEVELS]
    assert pace == sorted(pace) and len(set(pace)) == 10
    assert len({lv.theme for lv in LEVELS}) == 10
    assert len({lv.boss for lv in LEVELS}) == 10


def test_ship_stays_on_screen_on_its_rail():
    from typestriker.entities import Player
    player = Player(pygame.Surface((10, 10)))
    for t in range(0, 4000):
        assert 30 < player.rail_x(t / 10) < WIDTH - 30


